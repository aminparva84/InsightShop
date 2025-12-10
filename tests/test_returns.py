import pytest
import json
from app import app
from models.database import db
from models.user import User
from models.product import Product
from models.order import Order, OrderItem
from models.return_model import Return
from datetime import datetime, timedelta
from decimal import Decimal
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
        user_id = user.id  # Store ID before returning
        # Return a simple object with just the ID
        class UserRef:
            def __init__(self, uid):
                self.id = uid
        return UserRef(user_id)

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
        product_id = product.id  # Store ID before returning
        # Return a simple object with just the ID
        class ProductRef:
            def __init__(self, pid):
                self.id = pid
        return ProductRef(product_id)

@pytest.fixture
def test_order(client, test_user, test_product):
    """Create a test order (recent, within 30 days)."""
    with app.app_context():
        user_id = test_user.id
        product_id = test_product.id
        
        order = Order(
            user_id=user_id,
            shipping_name='Test User',
            shipping_address='123 Test St',
            shipping_city='Test City',
            shipping_state='CA',
            shipping_zip='12345',
            shipping_country='USA',
            subtotal=Decimal('29.99'),
            tax=Decimal('2.40'),
            shipping_cost=Decimal('5.00'),
            total=Decimal('37.39'),
            status='delivered',
            created_at=datetime.utcnow() - timedelta(days=10)  # 10 days ago
        )
        db.session.add(order)
        db.session.flush()
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=product_id,
            quantity=1,
            price=Decimal('29.99')
        )
        db.session.add(order_item)
        db.session.commit()
        order_id = order.id
        item_id = order_item.id
        # Return simple refs with IDs
        class OrderRef:
            def __init__(self, oid):
                self.id = oid
        class ItemRef:
            def __init__(self, iid):
                self.id = iid
        return OrderRef(order_id), ItemRef(item_id)

@pytest.fixture
def old_order(client, test_user, test_product):
    """Create an old order (more than 30 days)."""
    with app.app_context():
        user_id = test_user.id
        product_id = test_product.id
        
        order = Order(
            user_id=user_id,
            shipping_name='Test User',
            shipping_address='123 Test St',
            shipping_city='Test City',
            shipping_state='CA',
            shipping_zip='12345',
            shipping_country='USA',
            subtotal=Decimal('29.99'),
            tax=Decimal('2.40'),
            shipping_cost=Decimal('5.00'),
            total=Decimal('37.39'),
            status='delivered',
            created_at=datetime.utcnow() - timedelta(days=35)  # 35 days ago
        )
        db.session.add(order)
        db.session.flush()
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=product_id,
            quantity=1,
            price=Decimal('29.99')
        )
        db.session.add(order_item)
        db.session.commit()
        order_id = order.id
        item_id = order_item.id
        # Return simple refs with IDs
        class OrderRef:
            def __init__(self, oid):
                self.id = oid
        class ItemRef:
            def __init__(self, iid):
                self.id = iid
        return OrderRef(order_id), ItemRef(item_id)

def test_initiate_return_success(client, test_order):
    """Test initiating a return successfully (within 30 days)."""
    order, order_item = test_order
    
    response = client.post('/api/returns/initiate',
        json={
            'order_id': order.id,
            'item_id': order_item.id,
            'reason': 'Wrong Size'
        },
        content_type='application/json'
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'return' in data
    assert 'return_label_url' in data
    assert 'message' in data
    assert 'Return approved' in data['message']
    assert data['return']['status'] == 'approved'
    assert data['return']['reason'] == 'Wrong Size'

def test_initiate_return_old_order(client, old_order):
    """Test initiating a return for an order older than 30 days."""
    order, order_item = old_order
    
    response = client.post('/api/returns/initiate',
        json={
            'order_id': order.id,
            'item_id': order_item.id,
            'reason': 'Wrong Size'
        },
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] == False
    assert '30-day return window' in data['message']
    assert data['days_since_order'] > 30

def test_initiate_return_missing_order_id(client):
    """Test initiating return without order_id."""
    response = client.post('/api/returns/initiate',
        json={
            'item_id': 1,
            'reason': 'Wrong Size'
        },
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_initiate_return_missing_item_id(client):
    """Test initiating return without item_id."""
    response = client.post('/api/returns/initiate',
        json={
            'order_id': 1,
            'reason': 'Wrong Size'
        },
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_initiate_return_missing_reason(client):
    """Test initiating return without reason."""
    response = client.post('/api/returns/initiate',
        json={
            'order_id': 1,
            'item_id': 1
        },
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_initiate_return_invalid_reason(client, test_order):
    """Test initiating return with invalid reason."""
    order, order_item = test_order
    
    response = client.post('/api/returns/initiate',
        json={
            'order_id': order.id,
            'item_id': order_item.id,
            'reason': 'Invalid Reason'
        },
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_initiate_return_all_valid_reasons(client, test_order):
    """Test initiating return with all valid reasons."""
    order, order_item = test_order
    valid_reasons = ['Wrong Size', 'Damaged', 'Changed Mind']
    
    for reason in valid_reasons:
        # Delete previous return if exists
        with app.app_context():
            Return.query.filter_by(order_id=order.id, order_item_id=order_item.id).delete()
            db.session.commit()
        
        response = client.post('/api/returns/initiate',
            json={
                'order_id': order.id,
                'item_id': order_item.id,
                'reason': reason
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['return']['reason'] == reason

def test_initiate_return_order_not_found(client):
    """Test initiating return for non-existent order."""
    response = client.post('/api/returns/initiate',
        json={
            'order_id': 99999,
            'item_id': 1,
            'reason': 'Wrong Size'
        },
        content_type='application/json'
    )
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data

def test_initiate_return_item_not_found(client, test_order):
    """Test initiating return for non-existent order item."""
    order, order_item = test_order
    
    response = client.post('/api/returns/initiate',
        json={
            'order_id': order.id,
            'item_id': 99999,
            'reason': 'Wrong Size'
        },
        content_type='application/json'
    )
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data

def test_initiate_return_duplicate(client, test_order):
    """Test initiating return for an item that already has a return."""
    order, order_item = test_order
    
    # First return
    response1 = client.post('/api/returns/initiate',
        json={
            'order_id': order.id,
            'item_id': order_item.id,
            'reason': 'Wrong Size'
        },
        content_type='application/json'
    )
    assert response1.status_code == 201
    
    # Second return (duplicate)
    response2 = client.post('/api/returns/initiate',
        json={
            'order_id': order.id,
            'item_id': order_item.id,
            'reason': 'Damaged'
        },
        content_type='application/json'
    )
    assert response2.status_code == 200
    data = json.loads(response2.data)
    assert data['success'] == True
    assert 'already been initiated' in data['message']

def test_get_return_by_id(client, test_order):
    """Test getting return details by ID."""
    order, order_item = test_order
    
    # Create return first
    create_response = client.post('/api/returns/initiate',
        json={
            'order_id': order.id,
            'item_id': order_item.id,
            'reason': 'Wrong Size'
        },
        content_type='application/json'
    )
    return_id = json.loads(create_response.data)['return']['id']
    
    # Get return
    response = client.get(f'/api/returns/{return_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'return' in data
    assert data['return']['id'] == return_id

def test_get_return_not_found(client):
    """Test getting non-existent return."""
    response = client.get('/api/returns/99999')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data

