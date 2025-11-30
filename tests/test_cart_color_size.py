"""Tests for cart functionality with color and size selection."""
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
        user_id = user.id
        db.session.expunge(user)
        return {'id': user_id, 'email': 'test@example.com'}

@pytest.fixture
def test_product(client):
    """Create a test product with multiple colors and sizes."""
    with app.app_context():
        product = Product(
            name='Test T-Shirt',
            description='A test t-shirt',
            price=29.99,
            category='men',
            color='Blue',
            size='M',
            available_colors='["Blue", "Red", "Black", "White"]',
            available_sizes='["S", "M", "L", "XL"]',
            fabric='100% Cotton',
            stock_quantity=10,
            is_active=True,
            rating=4.5,
            review_count=25
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id
        db.session.expunge(product)
        return {'id': product_id}

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

def test_add_to_cart_with_color(client, auth_token, test_product):
    """Test adding item to cart with color selection."""
    response = client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1,
            'selected_color': 'Red'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    assert response.status_code == 200
    
    # Verify cart item has color
    cart_response = client.get('/api/cart',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    data = json.loads(cart_response.data)
    assert len(data['items']) == 1
    assert data['items'][0]['selected_color'] == 'Red'

def test_add_to_cart_with_size(client, auth_token, test_product):
    """Test adding item to cart with size selection."""
    response = client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1,
            'selected_size': 'L'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    assert response.status_code == 200
    
    # Verify cart item has size
    cart_response = client.get('/api/cart',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    data = json.loads(cart_response.data)
    assert len(data['items']) == 1
    assert data['items'][0]['selected_size'] == 'L'

def test_add_to_cart_with_color_and_size(client, auth_token, test_product):
    """Test adding item to cart with both color and size."""
    response = client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1,
            'selected_color': 'Black',
            'selected_size': 'XL'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    assert response.status_code == 200
    
    # Verify cart item has both color and size
    cart_response = client.get('/api/cart',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    data = json.loads(cart_response.data)
    assert len(data['items']) == 1
    assert data['items'][0]['selected_color'] == 'Black'
    assert data['items'][0]['selected_size'] == 'XL'

def test_add_same_product_different_variants(client, auth_token, test_product):
    """Test adding same product with different color/size creates separate cart items."""
    # Add Blue M
    client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1,
            'selected_color': 'Blue',
            'selected_size': 'M'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    
    # Add Red L
    client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1,
            'selected_color': 'Red',
            'selected_size': 'L'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    
    # Should have 2 separate items
    cart_response = client.get('/api/cart',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    data = json.loads(cart_response.data)
    assert len(data['items']) == 2

def test_add_same_variant_increments_quantity(client, auth_token, test_product):
    """Test adding same product with same color/size increments quantity."""
    # Add first time
    client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1,
            'selected_color': 'Blue',
            'selected_size': 'M'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    
    # Add same variant again
    client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 2,
            'selected_color': 'Blue',
            'selected_size': 'M'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    
    # Should have 1 item with quantity 3
    cart_response = client.get('/api/cart',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    data = json.loads(cart_response.data)
    assert len(data['items']) == 1
    assert data['items'][0]['quantity'] == 3

