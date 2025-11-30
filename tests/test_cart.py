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
            available_colors='["Blue", "Red", "Black"]',
            available_sizes='["S", "M", "L", "XL"]',
            fabric='100% Cotton',
            stock_quantity=10,
            is_active=True,
            rating=4.5,
            review_count=25
        )
        db.session.add(product)
        db.session.commit()
        # Get the ID within session to avoid DetachedInstanceError
        product_id = product.id
        db.session.expunge(product)
        # Return a dict with ID instead of the object
        return {'id': product_id, 'name': 'Test Product', 'price': 29.99, 'stock_quantity': 10}

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

def test_get_cart_empty(client, auth_token):
    """Test getting empty cart."""
    response = client.get('/api/cart',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'items' in data
    assert len(data['items']) == 0

def test_add_to_cart(client, auth_token, test_product):
    """Test adding item to cart."""
    response = client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 2
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data

def test_add_to_cart_unauthorized(client, test_product):
    """Test adding to cart without authentication (guest cart)."""
    response = client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1
        },
        content_type='application/json'
    )
    # Guest cart should work (no auth required)
    assert response.status_code == 200

def test_add_to_cart_invalid_product(client, auth_token):
    """Test adding non-existent product to cart."""
    response = client.post('/api/cart',
        json={
            'product_id': 99999,
            'quantity': 1
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    assert response.status_code == 404

def test_get_cart_with_items(client, auth_token, test_product):
    """Test getting cart with items."""
    # Add item first
    client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 2
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    
    # Get cart
    response = client.get('/api/cart',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['items']) == 1
    assert data['items'][0]['quantity'] == 2

def test_update_cart_item(client, auth_token, test_product):
    """Test updating cart item quantity."""
    # Add item first
    add_response = client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    
    # Get cart to find item ID
    cart_response = client.get('/api/cart',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    item_id = json.loads(cart_response.data)['items'][0]['id']
    
    # Update quantity
    response = client.put(f'/api/cart/{item_id}',
        json={'quantity': 3},
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    assert response.status_code == 200

def test_remove_from_cart(client, auth_token, test_product):
    """Test removing item from cart."""
    # Add item first
    client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    
    # Get cart to find item ID
    cart_response = client.get('/api/cart',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    item_id = json.loads(cart_response.data)['items'][0]['id']
    
    # Remove item
    response = client.delete(f'/api/cart/{item_id}',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    # Verify cart is empty
    cart_response = client.get('/api/cart',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert len(json.loads(cart_response.data)['items']) == 0

def test_clear_cart(client, auth_token, test_product):
    """Test clearing entire cart."""
    # Add items
    client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    
    # Clear cart
    response = client.delete('/api/cart/clear',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    # Verify cart is empty
    cart_response = client.get('/api/cart',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert len(json.loads(cart_response.data)['items']) == 0

def test_add_to_cart_with_color_size(client, auth_token, test_product):
    """Test adding item to cart with color and size selection."""
    response = client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1,
            'selected_color': 'Red',
            'selected_size': 'L'
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data

def test_guest_add_to_cart(client, test_product):
    """Test guest adding item to cart."""
    response = client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    
    # Get guest cart
    response = client.get('/api/cart')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['is_guest'] == True
    assert len(data['items']) == 1

def test_guest_add_to_cart_with_color_size(client, test_product):
    """Test guest adding item to cart with color and size."""
    response = client.post('/api/cart',
        json={
            'product_id': test_product['id'],
            'quantity': 1,
            'selected_color': 'Blue',
            'selected_size': 'M'
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    
    # Get guest cart
    response = client.get('/api/cart')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['items']) == 1
    assert data['items'][0]['selected_color'] == 'Blue'
    assert data['items'][0]['selected_size'] == 'M'

