"""
Tests for J.P. Morgan Payments API Integration
"""
import pytest
import json
from app import app
from models.database import db
from models.user import User
from models.order import Order
from models.payment import Payment
from utils.jpmorgan_payments import JPMorganPaymentsClient, get_jpmorgan_client
import bcrypt
from unittest.mock import patch, Mock


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
        password_hash = bcrypt.hashpw('testpass123'.encode('utf-8'), bcrypt.gensalt())
        user = User(
            email='test@example.com',
            password_hash=password_hash,
            is_verified=True
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_order(client, test_user):
    """Create a test order."""
    with app.app_context():
        order = Order(
            user_id=test_user.id,
            total=12.34,
            currency='USD',
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        return order


def test_jpmorgan_client_initialization():
    """Test that JPMorganPaymentsClient can be initialized."""
    client = JPMorganPaymentsClient()
    assert client is not None
    assert client.access_token_url is not None
    assert client.client_id is not None
    assert client.client_secret is not None


def test_get_jpmorgan_client_singleton():
    """Test that get_jpmorgan_client returns a singleton."""
    client1 = get_jpmorgan_client()
    client2 = get_jpmorgan_client()
    assert client1 is client2


@patch('utils.jpmorgan_payments.requests.post')
def test_get_access_token_success(mock_post):
    """Test successful access token retrieval."""
    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = {
        'access_token': 'test_token_12345',
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': 'jpm:payments:sandbox'
    }
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    client = JPMorganPaymentsClient()
    token = client._get_access_token()
    
    assert token == 'test_token_12345'
    assert client._cached_token == 'test_token_12345'
    mock_post.assert_called_once()


@patch('utils.jpmorgan_payments.requests.post')
def test_get_access_token_error(mock_post):
    """Test access token retrieval with error."""
    # Mock error response
    mock_response = Mock()
    mock_response.json.return_value = {
        'error': 'invalid_client',
        'error_description': 'Client authentication failed'
    }
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    client = JPMorganPaymentsClient()
    
    with pytest.raises(Exception) as exc_info:
        client._get_access_token()
    
    assert 'Failed to retrieve access token' in str(exc_info.value)


@patch('utils.jpmorgan_payments.requests.post')
def test_create_payment_success(mock_post):
    """Test successful payment creation."""
    # Mock token response
    mock_token_response = Mock()
    mock_token_response.json.return_value = {
        'access_token': 'test_token_12345',
        'expires_in': 3600
    }
    mock_token_response.raise_for_status = Mock()
    
    # Mock payment response
    mock_payment_response = Mock()
    mock_payment_response.json.return_value = {
        'transactionId': 'test-txn-123',
        'responseStatus': 'SUCCESS',
        'responseCode': 'APPROVED',
        'responseMessage': 'Transaction approved'
    }
    mock_payment_response.raise_for_status = Mock()
    
    # Set up mock to return different responses
    mock_post.side_effect = [mock_token_response, mock_payment_response]
    
    client = JPMorganPaymentsClient()
    result = client.create_payment(
        amount=1234,
        currency='USD',
        card_number='4012000033330026',
        expiry_month=5,
        expiry_year=2027
    )
    
    assert result['transactionId'] == 'test-txn-123'
    assert result['responseStatus'] == 'SUCCESS'
    assert mock_post.call_count == 2  # Token + Payment


def test_jpmorgan_token_endpoint(client):
    """Test the /api/payments/jpmorgan/token endpoint."""
    with patch('utils.jpmorgan_payments.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'test_token_12345',
            'expires_in': 3600
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        response = client.get('/api/payments/jpmorgan/token')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'access_token' in data
        assert data['access_token'] == 'test_token_12345'


def test_create_jpmorgan_payment_endpoint_missing_order_id(client):
    """Test payment endpoint with missing order_id."""
    response = client.post(
        '/api/payments/jpmorgan/create-payment',
        json={}
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Order ID is required' in data['error']


def test_create_jpmorgan_payment_endpoint_missing_card(client, test_order):
    """Test payment endpoint with missing card details."""
    response = client.post(
        '/api/payments/jpmorgan/create-payment',
        json={'order_id': test_order.id}
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Card number' in data['error']


def test_create_jpmorgan_payment_endpoint_success(client, test_order):
    """Test successful payment creation via endpoint."""
    with patch('utils.jpmorgan_payments.requests.post') as mock_post:
        # Mock token response
        mock_token_response = Mock()
        mock_token_response.json.return_value = {
            'access_token': 'test_token_12345',
            'expires_in': 3600
        }
        mock_token_response.raise_for_status = Mock()
        
        # Mock payment response
        mock_payment_response = Mock()
        mock_payment_response.json.return_value = {
            'transactionId': 'test-txn-123',
            'responseStatus': 'SUCCESS',
            'responseCode': 'APPROVED',
            'responseMessage': 'Transaction approved'
        }
        mock_payment_response.raise_for_status = Mock()
        
        mock_post.side_effect = [mock_token_response, mock_payment_response]
        
        response = client.post(
            '/api/payments/jpmorgan/create-payment',
            json={
                'order_id': test_order.id,
                'card_number': '4012000033330026',
                'expiry_month': 5,
                'expiry_year': 2027
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'payment' in data
        assert 'jpmorgan_response' in data
        assert data['jpmorgan_response']['responseStatus'] == 'SUCCESS'
        
        # Verify payment was created in database
        with app.app_context():
            payment = Payment.query.filter_by(order_id=test_order.id).first()
            assert payment is not None
            assert payment.payment_method == 'jpmorgan'
            assert payment.transaction_id == 'test-txn-123'
            assert payment.status == 'completed'

