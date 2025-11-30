"""Tests for product ratings functionality."""
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
def test_product_with_rating(client):
    """Create a test product with rating."""
    with app.app_context():
        product = Product(
            name='Rated Product',
            description='A product with rating',
            price=39.99,
            category='men',
            color='Blue',
            size='M',
            available_colors='["Blue", "Red"]',
            available_sizes='["M", "L"]',
            fabric='100% Cotton',
            stock_quantity=10,
            is_active=True,
            rating=4.75,
            review_count=150
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id
        db.session.expunge(product)
        return {'id': product_id}

def test_product_has_rating(client, test_product_with_rating):
    """Test that product includes rating in response."""
    response = client.get(f'/api/products/{test_product_with_rating["id"]}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'product' in data
    assert 'rating' in data['product']
    assert data['product']['rating'] == 4.75
    assert 'review_count' in data['product']
    assert data['product']['review_count'] == 150

def test_product_list_includes_ratings(client, test_product_with_rating):
    """Test that product list includes ratings."""
    response = client.get('/api/products')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'products' in data
    if len(data['products']) > 0:
        product = data['products'][0]
        assert 'rating' in product
        assert 'review_count' in product

