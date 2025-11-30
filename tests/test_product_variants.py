"""Tests for product color and size variants."""
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
def test_product_with_variants(client):
    """Create a test product with multiple color and size variants."""
    with app.app_context():
        product = Product(
            name='Variant Product',
            description='A product with variants',
            price=49.99,
            category='women',
            color='Red',
            size='S',
            available_colors='["Red", "Blue", "Black", "White", "Pink"]',
            available_sizes='["XS", "S", "M", "L", "XL"]',
            fabric='Polyester Blend',
            stock_quantity=20,
            is_active=True,
            rating=4.2,
            review_count=87
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id
        db.session.expunge(product)
        return {'id': product_id}

def test_product_includes_available_colors(client, test_product_with_variants):
    """Test that product includes available_colors array."""
    response = client.get(f'/api/products/{test_product_with_variants["id"]}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'product' in data
    assert 'available_colors' in data['product']
    assert isinstance(data['product']['available_colors'], list)
    assert len(data['product']['available_colors']) > 0

def test_product_includes_available_sizes(client, test_product_with_variants):
    """Test that product includes available_sizes array."""
    response = client.get(f'/api/products/{test_product_with_variants["id"]}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'product' in data
    assert 'available_sizes' in data['product']
    assert isinstance(data['product']['available_sizes'], list)
    assert len(data['product']['available_sizes']) > 0

def test_get_colors_endpoint(client, test_product_with_variants):
    """Test getting all available colors."""
    response = client.get('/api/products/colors')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'colors' in data
    assert isinstance(data['colors'], list)

def test_get_sizes_endpoint(client, test_product_with_variants):
    """Test getting all available sizes."""
    response = client.get('/api/products/sizes')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'sizes' in data
    assert isinstance(data['sizes'], list)

def test_get_fabrics_endpoint(client, test_product_with_variants):
    """Test getting all available fabrics."""
    response = client.get('/api/products/fabrics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'fabrics' in data
    assert isinstance(data['fabrics'], list)

def test_get_price_range_endpoint(client, test_product_with_variants):
    """Test getting price range."""
    response = client.get('/api/products/price-range')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'min_price' in data
    assert 'max_price' in data
    assert data['min_price'] <= data['max_price']

def test_filter_by_size(client, test_product_with_variants):
    """Test filtering products by size."""
    response = client.get('/api/products?size=M')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'products' in data

def test_filter_by_fabric(client, test_product_with_variants):
    """Test filtering products by fabric."""
    response = client.get('/api/products?fabric=Polyester Blend')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'products' in data

def test_filter_by_price_range(client, test_product_with_variants):
    """Test filtering products by price range."""
    response = client.get('/api/products?min_price=40&max_price=60')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'products' in data
    # Verify all products are within price range
    for product in data['products']:
        assert 40 <= product['price'] <= 60

