"""
Tests for payment routes with logging functionality.
"""
import pytest
import json
from app import app
from models.database import db
from models.user import User
from models.order import Order
from models.payment import Payment
from models.payment_log import PaymentLog
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
            first_name='Test',
            last_name='User',
            password_hash=password_hash
        )
        user.is_verified = True
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def auth_token(client, test_user):
    """Get auth token for test user."""
    with app.app_context():
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        return json.loads(response.data)['token']


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


def test_stripe_payment_intent_logs_attempt(client, test_user, test_order, auth_token):
    """Test that Stripe payment intent creation logs the attempt."""
    with app.app_context():
        with patch('routes.payments.stripe') as mock_stripe:
            mock_intent = Mock()
            mock_intent.id = 'pi_test_123'
            mock_intent.client_secret = 'pi_test_123_secret'
            mock_intent.to_dict.return_value = {'id': 'pi_test_123', 'status': 'requires_payment_method'}
            
            mock_stripe.PaymentIntent.create.return_value = mock_intent
            
            response = client.post(
                '/api/payments/create-intent',
                json={'order_id': test_order.id},
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            assert response.status_code == 200
            
            # Check that payment log was created
            logs = PaymentLog.query.filter_by(order_id=test_order.id).all()
            assert len(logs) > 0
            assert logs[0].payment_method == 'stripe'
            assert logs[0].status == 'pending'
            assert logs[0].payment_intent_id == 'pi_test_123'


def test_jpmorgan_payment_logs_attempt(client, test_user, test_order, auth_token):
    """Test that J.P. Morgan payment creation logs the attempt."""
    with app.app_context():
        with patch('routes.payments.get_jpmorgan_client') as mock_client:
            mock_jpmorgan = Mock()
            mock_jpmorgan.create_payment.return_value = {
                'transactionId': 'txn_test_123',
                'responseStatus': 'SUCCESS',
                'responseCode': 'APPROVED',
                'responseMessage': 'Transaction approved',
                'paymentMethodType': {
                    'card': {
                        'maskedAccountNumber': '4012XXXXXX0026',
                        'cardTypeName': 'VISA'
                    }
                }
            }
            mock_client.return_value = mock_jpmorgan
            
            response = client.post(
                '/api/payments/jpmorgan/create-payment',
                json={
                    'order_id': test_order.id,
                    'card_number': '4012000033330026',
                    'expiry_month': 5,
                    'expiry_year': 2027
                },
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            assert response.status_code == 200
            
            # Check that payment log was created
            logs = PaymentLog.query.filter_by(order_id=test_order.id).all()
            assert len(logs) > 0
            log = logs[0]
            assert log.payment_method == 'jpmorgan'
            assert log.status == 'completed'
            assert log.external_transaction_id == 'txn_test_123'
            assert log.card_last4 == '0026'
            assert log.card_brand == 'VISA'


def test_failed_payment_logs_error(client, test_user, test_order, auth_token):
    """Test that failed payments are logged with error messages."""
    with app.app_context():
        with patch('routes.payments.get_jpmorgan_client') as mock_client:
            mock_jpmorgan = Mock()
            mock_jpmorgan.create_payment.side_effect = Exception('Payment failed: Card declined')
            mock_client.return_value = mock_jpmorgan
            
            response = client.post(
                '/api/payments/jpmorgan/create-payment',
                json={
                    'order_id': test_order.id,
                    'card_number': '4012000033330026',
                    'expiry_month': 5,
                    'expiry_year': 2027
                },
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            assert response.status_code == 500
            
            # Check that error was logged
            logs = PaymentLog.query.filter_by(order_id=test_order.id).all()
            assert len(logs) > 0
            log = logs[0]
            assert log.status == 'failed'
            assert log.error_message is not None
            assert 'failed' in log.error_message.lower()


def test_payment_logs_capture_request_data(client, test_user, test_order, auth_token):
    """Test that request data is captured in payment logs."""
    with app.app_context():
        with patch('routes.payments.get_jpmorgan_client') as mock_client:
            mock_jpmorgan = Mock()
            mock_jpmorgan.create_payment.return_value = {
                'transactionId': 'txn_test_123',
                'responseStatus': 'SUCCESS',
                'responseCode': 'APPROVED'
            }
            mock_client.return_value = mock_jpmorgan
            
            response = client.post(
                '/api/payments/jpmorgan/create-payment',
                json={
                    'order_id': test_order.id,
                    'card_number': '4012000033330026',
                    'expiry_month': 5,
                    'expiry_year': 2027
                },
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            assert response.status_code == 200
            
            # Check request data was logged
            logs = PaymentLog.query.filter_by(order_id=test_order.id).all()
            assert len(logs) > 0
            log_dict = logs[0].to_dict()
            assert log_dict['request_data'] is not None
            assert isinstance(log_dict['request_data'], dict)
            # Card number should be masked
            if 'card_number' in log_dict['request_data']:
                assert '****' in log_dict['request_data']['card_number']


def test_payment_logs_capture_response_data(client, test_user, test_order, auth_token):
    """Test that response data is captured in payment logs."""
    with app.app_context():
        with patch('routes.payments.get_jpmorgan_client') as mock_client:
            mock_response = {
                'transactionId': 'txn_test_123',
                'responseStatus': 'SUCCESS',
                'responseCode': 'APPROVED',
                'responseMessage': 'Transaction approved',
                'amount': 1234,
                'currency': 'USD'
            }
            mock_jpmorgan = Mock()
            mock_jpmorgan.create_payment.return_value = mock_response
            mock_client.return_value = mock_jpmorgan
            
            response = client.post(
                '/api/payments/jpmorgan/create-payment',
                json={
                    'order_id': test_order.id,
                    'card_number': '4012000033330026',
                    'expiry_month': 5,
                    'expiry_year': 2027
                },
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            assert response.status_code == 200
            
            # Check response data was logged
            logs = PaymentLog.query.filter_by(order_id=test_order.id).all()
            assert len(logs) > 0
            log_dict = logs[0].to_dict()
            assert log_dict['response_data'] is not None
            assert isinstance(log_dict['response_data'], dict)
            assert log_dict['response_data']['responseStatus'] == 'SUCCESS'

