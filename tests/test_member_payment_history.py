"""
Tests for member payment history functionality.
"""
import pytest
import json
from app import app
from models.database import db
from models.user import User
from models.order import Order
from models.payment import Payment
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
def test_user(client):
    """Create a test user."""
    with app.app_context():
        password_hash = bcrypt.hashpw('testpass123'.encode('utf-8'), bcrypt.gensalt())
        user = User(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password_hash=password_hash
        )
        user.is_verified = True
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def auth_token(client, test_user):
    """Get auth token for test user."""
    with app.app_context():
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        return json.loads(response.data)['token']


@pytest.fixture
def test_orders_and_payments(client, test_user):
    """Create test orders and payments."""
    with app.app_context():
        orders = []
        payments = []
        payment_logs = []
        
        for i in range(3):
            order = Order(
                user_id=test_user.id,
                total=10.00 + i * 5,
                currency='USD',
                status='processing' if i < 2 else 'pending'
            )
            db.session.add(order)
            db.session.flush()
            orders.append(order)
            
            # Create payment (only for completed orders)
            if i < 2:
                payment = Payment(
                    order_id=order.id,
                    payment_method='stripe' if i == 0 else 'jpmorgan',
                    amount=order.total,
                    currency='USD',
                    status='completed',
                    transaction_id=f'PAY-{i}'
                )
                db.session.add(payment)
                payments.append(payment)
            
            # Create payment logs (all attempts)
            log = PaymentLog(
                order_id=order.id,
                user_id=test_user.id,
                payment_method='stripe' if i == 0 else 'jpmorgan',
                amount=order.total,
                currency='USD',
                status='completed' if i < 2 else 'failed',
                transaction_id=f'LOG-{i}',
                error_message='Card declined' if i >= 2 else None
            )
            db.session.add(log)
            payment_logs.append(log)
        
        db.session.commit()
        return orders, payments, payment_logs


def test_get_member_payments_requires_auth(client):
    """Test that member payments endpoint requires authentication."""
    response = client.get('/api/members/payments')
    assert response.status_code == 401


def test_get_member_payments_returns_payments_and_logs(client, test_user, auth_token, test_orders_and_payments):
    """Test that member payments endpoint returns both payments and logs."""
    response = client.get(
        '/api/members/payments',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert 'payments' in data
    assert 'payment_logs' in data
    assert 'total_payments' in data
    assert 'total_attempts' in data
    assert 'total_spent' in data
    
    # Should have 2 successful payments
    assert len(data['payments']) == 2
    # Should have 3 payment logs (all attempts)
    assert len(data['payment_logs']) == 3
    assert data['total_payments'] == 2
    assert data['total_attempts'] == 3


def test_get_member_payments_only_shows_user_payments(client, test_user, auth_token, test_orders_and_payments):
    """Test that users can only see their own payments."""
    with app.app_context():
        # Create another user with payments
        password_hash = bcrypt.hashpw('otherpass123'.encode('utf-8'), bcrypt.gensalt())
        other_user = User(
            email='other@example.com',
            first_name='Other',
            last_name='User',
            password_hash=password_hash
        )
        other_user.is_verified = True
        db.session.add(other_user)
        db.session.commit()
        
        order = Order(
            user_id=other_user.id,
            total=100.00,
            currency='USD',
            status='processing'
        )
        db.session.add(order)
        db.session.commit()
        
        payment = Payment(
            order_id=order.id,
            payment_method='stripe',
            amount=100.00,
            currency='USD',
            status='completed'
        )
        db.session.add(payment)
        db.session.commit()
        
        # Get payments for test_user
        response = client.get(
            '/api/members/payments',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should not include other user's payments
        assert all(p['order_id'] in [o.id for o in test_orders_and_payments[0]] for p in data['payments'])


def test_get_member_payments_calculates_total_spent(client, test_user, auth_token, test_orders_and_payments):
    """Test that total spent is calculated correctly."""
    response = client.get(
        '/api/members/payments',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Total spent should be sum of completed payments
    expected_total = sum(10.00 + i * 5 for i in range(2))
    assert data['total_spent'] == expected_total


def test_get_member_payments_includes_payment_details(client, test_user, auth_token, test_orders_and_payments):
    """Test that payment details are included in response."""
    response = client.get(
        '/api/members/payments',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Check payment structure
    if len(data['payments']) > 0:
        payment = data['payments'][0]
        assert 'id' in payment
        assert 'order_id' in payment
        assert 'payment_method' in payment
        assert 'amount' in payment
        assert 'currency' in payment
        assert 'status' in payment
        assert 'transaction_id' in payment
        assert 'created_at' in payment
    
    # Check payment log structure
    if len(data['payment_logs']) > 0:
        log = data['payment_logs'][0]
        assert 'id' in log
        assert 'order_id' in log
        assert 'payment_method' in log
        assert 'amount' in log
        assert 'status' in log
        assert 'created_at' in log


def test_get_member_payments_empty_for_new_user(client, test_user, auth_token):
    """Test that new users with no payments get empty results."""
    response = client.get(
        '/api/members/payments',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['payments'] == []
    assert data['payment_logs'] == []
    assert data['total_payments'] == 0
    assert data['total_attempts'] == 0
    assert data['total_spent'] == 0

