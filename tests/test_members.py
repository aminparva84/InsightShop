import pytest
import json
from app import app
from models.database import db
from models.user import User
from models.product import Product
from models.order import Order
from models.payment import Payment
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
        user = User(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password_hash=bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        )
        user.is_verified = True
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        db.session.expunge(user)
        return {'id': user_id, 'email': 'test@example.com'}

@pytest.fixture
def auth_token(client, test_user):
    """Get authentication token."""
    response = client.post('/api/auth/login',
        json={
            'email': 'test@example.com',
            'password': 'password123'
        },
        content_type='application/json'
    )
    return json.loads(response.data)['token']

@pytest.fixture
def test_order(client, test_user):
    """Create a test order."""
    with app.app_context():
        order = Order(
            user_id=test_user.id,
            shipping_name='Test User',
            shipping_address='123 Test St',
            shipping_city='Test City',
            shipping_state='CA',
            shipping_zip='12345',
            shipping_country='USA',
            subtotal=100.00,
            tax=8.00,
            shipping_cost=5.00,
            total=113.00,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        return order

@pytest.fixture
def test_payment(client, test_order):
    """Create a test payment."""
    with app.app_context():
        payment = Payment(
            order_id=test_order.id,
            payment_method='stripe',
            amount=113.00,
            status='completed'
        )
        db.session.add(payment)
        db.session.commit()
        return payment

def test_get_member_dashboard(client, auth_token, test_order, test_payment):
    """Test getting member dashboard."""
    response = client.get('/api/members/dashboard',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user' in data
    assert 'statistics' in data
    assert 'recent_orders' in data
    assert 'recent_payments' in data

def test_get_member_orders(client, auth_token, test_order):
    """Test getting member orders."""
    response = client.get('/api/members/orders',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'orders' in data
    assert 'total_orders' in data

def test_get_member_payments(client, auth_token, test_payment):
    """Test getting member payments."""
    response = client.get('/api/members/payments',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'payments' in data
    assert 'total_payments' in data
    assert 'total_spent' in data

def test_get_member_dashboard_unauthorized(client):
    """Test getting dashboard without authentication."""
    response = client.get('/api/members/dashboard')
    assert response.status_code == 401

