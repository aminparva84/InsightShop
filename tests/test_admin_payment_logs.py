"""
Tests for admin payment logs endpoints.
"""
import pytest
import json
from app import app
from models.database import db
from models.user import User
from models.order import Order
from models.payment_log import PaymentLog
import bcrypt


@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET'] = 'test-secret-key-for-testing-only-min-32-chars'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def admin_user(client):
    """Create an admin user."""
    with app.app_context():
        password_hash = bcrypt.hashpw('adminpass123'.encode('utf-8'), bcrypt.gensalt())
        admin = User(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            password_hash=password_hash
        )
        admin.is_verified = True
        admin.is_admin = True
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def regular_user(client):
    """Create a regular user."""
    with app.app_context():
        password_hash = bcrypt.hashpw('userpass123'.encode('utf-8'), bcrypt.gensalt())
        user = User(
            email='user@example.com',
            first_name='Regular',
            last_name='User',
            password_hash=password_hash
        )
        user.is_verified = True
        user.is_admin = False
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_token(client, admin_user):
    """Get auth token for admin user."""
    with app.app_context():
        response = client.post('/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'adminpass123'
        })
        return json.loads(response.data)['token']


@pytest.fixture
def test_payment_logs(client, regular_user):
    """Create test payment logs."""
    with app.app_context():
        order = Order(
            user_id=regular_user.id,
            total=12.34,
            currency='USD',
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        
        logs = []
        for i in range(5):
            log = PaymentLog(
                order_id=order.id,
                user_id=regular_user.id,
                payment_method='stripe' if i % 2 == 0 else 'jpmorgan',
                amount=10.00 + i,
                currency='USD',
                status='completed' if i < 3 else 'failed',
                transaction_id=f'TXN-{i}',
                error_message='Card declined' if i >= 3 else None
            )
            db.session.add(log)
            logs.append(log)
        
        db.session.commit()
        return logs


def test_get_payment_logs_requires_admin(client, regular_user):
    """Test that only admins can access payment logs."""
    with app.app_context():
        # Login as regular user
        response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'userpass123'
        })
        token = json.loads(response.data)['token']
        
        # Try to access payment logs
        response = client.get(
            '/api/admin/payment-logs',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 403


def test_get_payment_logs_admin_access(client, admin_token, test_payment_logs):
    """Test that admin can access payment logs."""
    response = client.get(
        '/api/admin/payment-logs',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'payment_logs' in data
    assert len(data['payment_logs']) == 5
    assert 'pagination' in data
    assert 'summary' in data


def test_get_payment_logs_pagination(client, admin_token, test_payment_logs):
    """Test payment logs pagination."""
    response = client.get(
        '/api/admin/payment-logs?page=1&per_page=2',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['payment_logs']) == 2
    assert data['pagination']['page'] == 1
    assert data['pagination']['per_page'] == 2
    assert data['pagination']['total'] == 5


def test_get_payment_logs_filter_by_status(client, admin_token, test_payment_logs):
    """Test filtering payment logs by status."""
    response = client.get(
        '/api/admin/payment-logs?status=completed',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(log['status'] == 'completed' for log in data['payment_logs'])


def test_get_payment_logs_filter_by_payment_method(client, admin_token, test_payment_logs):
    """Test filtering payment logs by payment method."""
    response = client.get(
        '/api/admin/payment-logs?payment_method=stripe',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(log['payment_method'] == 'stripe' for log in data['payment_logs'])


def test_get_payment_logs_filter_by_user_id(client, admin_token, test_payment_logs, regular_user):
    """Test filtering payment logs by user ID."""
    response = client.get(
        f'/api/admin/payment-logs?user_id={regular_user.id}',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(log['user_id'] == regular_user.id for log in data['payment_logs'])


def test_get_payment_logs_summary(client, admin_token, test_payment_logs):
    """Test payment logs summary statistics."""
    response = client.get(
        '/api/admin/payment-logs',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'summary' in data
    assert data['summary']['total_logs'] == 5
    assert data['summary']['completed'] == 3
    assert data['summary']['failed'] == 2


def test_get_payment_log_detail(client, admin_token, test_payment_logs):
    """Test getting detailed payment log information."""
    log_id = test_payment_logs[0].id
    
    response = client.get(
        f'/api/admin/payment-logs/{log_id}',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'payment_log' in data
    assert data['payment_log']['id'] == log_id
    assert 'order' in data['payment_log']
    assert 'user' in data['payment_log']


def test_get_payment_log_detail_not_found(client, admin_token):
    """Test getting non-existent payment log."""
    response = client.get(
        '/api/admin/payment-logs/99999',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 404

