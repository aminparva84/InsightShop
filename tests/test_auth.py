import pytest
import json
from app import app
from models.database import db
from models.user import User
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

def test_register_success(client):
    """Test successful user registration."""
    response = client.post('/api/auth/register', 
        json={
            'email': 'newuser@example.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        },
        content_type='application/json'
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'message' in data
    assert 'user' in data

def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email."""
    response = client.post('/api/auth/register',
        json={
            'email': 'test@example.com',
            'password': 'password123',
            'first_name': 'Test',
            'last_name': 'User'
        },
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_register_missing_fields(client):
    """Test registration with missing fields."""
    response = client.post('/api/auth/register',
        json={'email': 'test@example.com'},
        content_type='application/json'
    )
    assert response.status_code == 400

def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post('/api/auth/login',
        json={
            'email': 'test@example.com',
            'password': 'password123'
        },
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    assert 'user' in data

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/api/auth/login',
        json={
            'email': 'wrong@example.com',
            'password': 'wrongpassword'
        },
        content_type='application/json'
    )
    assert response.status_code == 401

def test_login_unverified_user(client):
    """Test login with unverified email."""
    with app.app_context():
        user = User(
            email='unverified@example.com',
            first_name='Unverified',
            last_name='User',
            password_hash=bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        )
        user.is_verified = False
        db.session.add(user)
        db.session.commit()
    
    response = client.post('/api/auth/login',
        json={
            'email': 'unverified@example.com',
            'password': 'password123'
        },
        content_type='application/json'
    )
    assert response.status_code == 403

def test_get_current_user(client, test_user):
    """Test getting current user with valid token."""
    # First login to get token
    login_response = client.post('/api/auth/login',
        json={
            'email': 'test@example.com',
            'password': 'password123'
        },
        content_type='application/json'
    )
    token = json.loads(login_response.data)['token']
    
    # Get current user
    response = client.get('/api/auth/me',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user' in data
    assert data['user']['email'] == 'test@example.com'

def test_get_current_user_no_token(client):
    """Test getting current user without token."""
    response = client.get('/api/auth/me')
    assert response.status_code == 401

