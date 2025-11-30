import pytest
import json
from app import app
from models.database import db
from models.product import Product

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
def test_products(client):
    """Create test products for AI agent."""
    with app.app_context():
        products = [
            Product(
                name='Blue T-Shirt Men',
                description='A blue t-shirt for men',
                price=25.99,
                category='men',
                color='Blue',
                size='M',
                stock_quantity=10,
                is_active=True
            ),
            Product(
                name='Red Dress Women',
                description='A red dress for women',
                price=49.99,
                category='women',
                color='Red',
                size='S',
                stock_quantity=5,
                is_active=True
            ),
            Product(
                name='Yellow Shirt Kids',
                description='A yellow shirt for kids',
                price=19.99,
                category='kids',
                color='Yellow',
                size='M',
                stock_quantity=15,
                is_active=True
            )
        ]
        for product in products:
            db.session.add(product)
        db.session.commit()
        return products

def test_ai_chat(client, test_products):
    """Test AI chat endpoint."""
    response = client.post('/api/ai/chat',
        json={
            'message': 'Show me blue clothes for men',
            'history': []
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'response' in data
    # Response should contain some text
    assert len(data['response']) > 0

def test_ai_chat_missing_message(client):
    """Test AI chat without message."""
    response = client.post('/api/ai/chat',
        json={'history': []},
        content_type='application/json'
    )
    assert response.status_code == 400

def test_ai_search(client, test_products):
    """Test AI search endpoint."""
    response = client.post('/api/ai/search',
        json={'query': 'blue t-shirt'},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'products' in data
    assert 'count' in data

def test_ai_search_missing_query(client):
    """Test AI search without query."""
    response = client.post('/api/ai/search',
        json={},
        content_type='application/json'
    )
    assert response.status_code == 400

def test_ai_filter(client, test_products):
    """Test AI filter endpoint."""
    response = client.post('/api/ai/filter',
        json={
            'criteria': {
                'category': 'men',
                'color': 'Blue'
            }
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'products' in data
    assert 'count' in data
    # Should return at least one product
    assert data['count'] > 0

def test_ai_compare(client, test_products):
    """Test AI compare endpoint."""
    product_ids = [test_products[0].id, test_products[1].id]
    response = client.post('/api/ai/compare',
        json={'product_ids': product_ids},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'products' in data
    assert 'comparison' in data
    assert len(data['products']) == 2

def test_ai_compare_insufficient_products(client):
    """Test AI compare with less than 2 products."""
    response = client.post('/api/ai/compare',
        json={'product_ids': [1]},
        content_type='application/json'
    )
    assert response.status_code == 400

def test_ai_compare_invalid_products(client):
    """Test AI compare with invalid product IDs."""
    response = client.post('/api/ai/compare',
        json={'product_ids': [99999, 99998]},
        content_type='application/json'
    )
    assert response.status_code == 404

