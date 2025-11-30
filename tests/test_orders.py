import pytest
import json
from app import app
from models.database import db
from models.user import User
from models.product import Product
from models.cart import CartItem
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
        return user

@pytest.fixture
def test_product(client):
    """Create a test product."""
    with app.app_context():
        product = Product(
            name='Test Product',
            description='A test product',
            price=29.99,
            category='men',
            color='Blue',
            size='M',
            stock_quantity=10,
            is_active=True
        )
        db.session.add(product)
        db.session.commit()
        return product

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
def cart_with_items(client, auth_token, test_product):
    """Create cart with items."""
    client.post('/api/cart',
        json={
            'product_id': test_product.id,
            'quantity': 2
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )

def test_create_order_success(client, auth_token, cart_with_items):
    """Test creating an order successfully."""
    response = client.post('/api/orders',
        json={
            'shipping_name': 'Test User',
            'shipping_address': '123 Test St',
            'shipping_city': 'Test City',
            'shipping_state': 'CA',
            'shipping_zip': '12345',
            'shipping_country': 'USA',
            'shipping_phone': '123-456-7890'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'order' in data
    assert 'order_number' in data['order']

def test_create_order_empty_cart(client, auth_token):
    """Test creating order with empty cart."""
    response = client.post('/api/orders',
        json={
            'shipping_name': 'Test User',
            'shipping_address': '123 Test St',
            'shipping_city': 'Test City',
            'shipping_state': 'CA',
            'shipping_zip': '12345'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    assert response.status_code == 400

def test_create_order_missing_shipping_info(client, auth_token, cart_with_items):
    """Test creating order with missing shipping information."""
    response = client.post('/api/orders',
        json={
            'shipping_name': 'Test User'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    assert response.status_code == 400

def test_get_orders(client, auth_token, cart_with_items):
    """Test getting user orders."""
    # Create an order first
    client.post('/api/orders',
        json={
            'shipping_name': 'Test User',
            'shipping_address': '123 Test St',
            'shipping_city': 'Test City',
            'shipping_state': 'CA',
            'shipping_zip': '12345',
            'shipping_country': 'USA'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    
    # Get orders
    response = client.get('/api/orders',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'orders' in data
    assert len(data['orders']) > 0

def test_get_order_by_id(client, auth_token, cart_with_items):
    """Test getting a specific order."""
    # Create an order first
    order_response = client.post('/api/orders',
        json={
            'shipping_name': 'Test User',
            'shipping_address': '123 Test St',
            'shipping_city': 'Test City',
            'shipping_state': 'CA',
            'shipping_zip': '12345',
            'shipping_country': 'USA'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    order_id = json.loads(order_response.data)['order']['id']
    
    # Get order
    response = client.get(f'/api/orders/{order_id}',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'order' in data
    assert data['order']['id'] == order_id

