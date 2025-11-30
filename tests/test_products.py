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
    """Create test products."""
    with app.app_context():
        products = [
            Product(
                name='Test T-Shirt Men',
                description='A test t-shirt',
                price=25.99,
                category='men',
                color='Blue',
                size='M',
                stock_quantity=10,
                is_active=True
            ),
            Product(
                name='Test Dress Women',
                description='A test dress',
                price=49.99,
                category='women',
                color='Red',
                size='S',
                stock_quantity=5,
                is_active=True
            ),
            Product(
                name='Test Shirt Kids',
                description='A test shirt for kids',
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

def test_get_products(client, test_products):
    """Test getting all products."""
    response = client.get('/api/products')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'products' in data
    assert len(data['products']) == 3

def test_get_products_with_category_filter(client, test_products):
    """Test getting products filtered by category."""
    response = client.get('/api/products?category=men')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['products']) == 1
    assert data['products'][0]['category'] == 'men'

def test_get_products_with_color_filter(client, test_products):
    """Test getting products filtered by color."""
    response = client.get('/api/products?color=Red')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['products']) == 1
    assert data['products'][0]['color'] == 'Red'

def test_get_products_with_search(client, test_products):
    """Test getting products with search query."""
    response = client.get('/api/products?search=dress')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['products']) == 1
    assert 'dress' in data['products'][0]['name'].lower()

def test_get_product_by_id(client, test_products):
    """Test getting a single product by ID."""
    product_id = test_products[0]
    response = client.get(f'/api/products/{product_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'product' in data
    assert data['product']['id'] == product_id
    # Check new fields
    assert 'rating' in data['product']
    assert 'review_count' in data['product']
    assert 'available_colors' in data['product']
    assert 'available_sizes' in data['product']

def test_get_product_not_found(client):
    """Test getting a non-existent product."""
    response = client.get('/api/products/99999')
    assert response.status_code == 404

def test_get_categories(client, test_products):
    """Test getting all categories."""
    response = client.get('/api/products/categories')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'categories' in data
    assert 'men' in data['categories']
    assert 'women' in data['categories']
    assert 'kids' in data['categories']

def test_get_colors(client, test_products):
    """Test getting all colors."""
    response = client.get('/api/products/colors')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'colors' in data
    assert 'Blue' in data['colors']
    assert 'Red' in data['colors']
    assert 'Yellow' in data['colors']

