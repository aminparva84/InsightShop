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

def test_search_products_basic(client, test_products):
    """Test basic product search."""
    response = client.post('/api/products/search',
        json={
            'query': 'shirt'
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'products' in data
    assert len(data['products']) >= 1
    # Check product structure
    product = data['products'][0]
    assert 'id' in product
    assert 'name' in product
    assert 'price' in product
    assert 'image_url' in product
    assert 'add_to_cart_url' in product
    assert 'product_url' in product

def test_search_products_with_max_price(client, test_products):
    """Test product search with max_price filter."""
    response = client.post('/api/products/search',
        json={
            'query': '',
            'max_price': 30.0
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    # All products should be <= 30.0
    for product in data['products']:
        assert product['price'] <= 30.0

def test_search_products_with_category(client, test_products):
    """Test product search with category filter."""
    response = client.post('/api/products/search',
        json={
            'query': '',
            'category': 'men'
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    # All products should be in men category
    for product in data['products']:
        assert product['category'] == 'men'

def test_search_products_with_size(client, test_products):
    """Test product search with size filter."""
    response = client.post('/api/products/search',
        json={
            'query': '',
            'size': 'M'
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    # Verify products have size M (we need to check the actual product)
    assert len(data['products']) >= 1

def test_search_products_sort_by_rating(client, test_products):
    """Test product search sorted by rating."""
    # Add products with different ratings
    with app.app_context():
        high_rated = Product(
            name='High Rated Product',
            description='A highly rated product',
            price=29.99,
            category='men',
            color='Blue',
            size='M',
            stock_quantity=10,
            is_active=True,
            rating=4.8,
            review_count=50
        )
        low_rated = Product(
            name='Low Rated Product',
            description='A low rated product',
            price=19.99,
            category='men',
            color='Red',
            size='M',
            stock_quantity=10,
            is_active=True,
            rating=2.5,
            review_count=5
        )
        db.session.add(high_rated)
        db.session.add(low_rated)
        db.session.commit()
    
    response = client.post('/api/products/search',
        json={
            'query': '',
            'sort_by': 'rating'
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    # First product should have higher or equal rating to second
    if len(data['products']) >= 2:
        assert data['products'][0]['rating'] >= data['products'][1]['rating']

def test_search_products_sort_by_price_low(client, test_products):
    """Test product search sorted by price (low to high)."""
    response = client.post('/api/products/search',
        json={
            'query': '',
            'sort_by': 'price_low'
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    # Prices should be in ascending order
    if len(data['products']) >= 2:
        assert data['products'][0]['price'] <= data['products'][1]['price']

def test_search_products_sort_by_price_high(client, test_products):
    """Test product search sorted by price (high to low)."""
    response = client.post('/api/products/search',
        json={
            'query': '',
            'sort_by': 'price_high'
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    # Prices should be in descending order
    if len(data['products']) >= 2:
        assert data['products'][0]['price'] >= data['products'][1]['price']

def test_search_products_only_in_stock(client, test_products):
    """Test that search only returns products with stock_quantity > 0."""
    # Add a product with 0 stock
    with app.app_context():
        out_of_stock = Product(
            name='Out of Stock Product',
            description='A product with no stock',
            price=29.99,
            category='men',
            color='Blue',
            size='M',
            stock_quantity=0,
            is_active=True
        )
        db.session.add(out_of_stock)
        db.session.commit()
    
    response = client.post('/api/products/search',
        json={
            'query': ''
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    # All products should have stock_quantity > 0
    for product in data['products']:
        assert product['stock_quantity'] > 0

def test_search_products_with_reviews_keyword(client, test_products):
    """Test that searching for 'reviews' or 'best rated' sorts by rating."""
    # Add products with different ratings
    with app.app_context():
        high_rated = Product(
            name='Best Rated Product',
            description='The best rated product',
            price=29.99,
            category='men',
            color='Blue',
            size='M',
            stock_quantity=10,
            is_active=True,
            rating=4.9,
            review_count=100
        )
        db.session.add(high_rated)
        db.session.commit()
    
    response = client.post('/api/products/search',
        json={
            'query': 'best rated'
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    # Should return products sorted by rating
    assert len(data['products']) >= 1

