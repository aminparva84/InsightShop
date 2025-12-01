"""
Tests for payment logging functionality.
"""
import pytest
import json
from app import app
from models.database import db
from models.user import User
from models.order import Order
from models.payment import Payment
from models.payment_log import PaymentLog
from utils.payment_logger import log_payment_attempt
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
def test_order(client, test_user):
    """Create a test order."""
    with app.app_context():
        # Re-query user to ensure it's in the session
        user = User.query.filter_by(email='test@example.com').first()
        order = Order(
            user_id=user.id,
            shipping_name='Test User',
            shipping_address='123 Test St',
            shipping_city='Test City',
            shipping_state='CA',
            shipping_zip='12345',
            shipping_country='USA',
            subtotal=10.00,
            tax=1.00,
            shipping_cost=1.34,
            total=12.34,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        return order


def test_payment_log_model(client):
    """Test PaymentLog model creation and serialization."""
    with app.app_context():
        log = PaymentLog(
            order_id=1,
            user_id=1,
            payment_method='stripe',
            amount=12.34,
            currency='USD',
            status='completed',
            transaction_id='TXN-123',
            request_data=json.dumps({'order_id': 1}),
            response_data=json.dumps({'status': 'succeeded'}),
            card_last4='1234',
            card_brand='Visa'
        )
        db.session.add(log)
        db.session.commit()
        
        assert log.id is not None
        assert log.payment_method == 'stripe'
        assert log.status == 'completed'
        
        # Test to_dict
        log_dict = log.to_dict()
        assert log_dict['payment_method'] == 'stripe'
        assert log_dict['amount'] == 12.34
        assert isinstance(log_dict['request_data'], dict)
        assert isinstance(log_dict['response_data'], dict)


def test_log_payment_attempt_success(client, test_user, test_order):
    """Test logging a successful payment attempt."""
    with app.app_context():
        # Re-query to ensure objects are in session
        order = Order.query.get(test_order.id)
        user = User.query.get(test_user.id)
        
        with app.test_request_context():
            log = log_payment_attempt(
                order_id=order.id,
                user_id=user.id,
                payment_method='stripe',
                amount=12.34,
                currency='USD',
                status='completed',
                transaction_id='TXN-123',
                request_data={'order_id': order.id},
                response_data={'status': 'succeeded'},
                card_last4='1234',
                card_brand='Visa'
            )
            
            assert log is not None
            assert log.id is not None
            assert log.status == 'completed'
            assert log.user_id == user.id
            assert log.order_id == order.id
            
            # Verify it's in database
            saved_log = PaymentLog.query.get(log.id)
            assert saved_log is not None
            assert saved_log.status == 'completed'


def test_log_payment_attempt_failed(client, test_user, test_order):
    """Test logging a failed payment attempt."""
    with app.app_context():
        order = Order.query.get(test_order.id)
        user = User.query.get(test_user.id)
        
        with app.test_request_context():
            log = log_payment_attempt(
                order_id=order.id,
                user_id=user.id,
                payment_method='jpmorgan',
                amount=12.34,
                currency='USD',
                status='failed',
                error_message='Card declined',
                request_data={'order_id': order.id, 'card_number': '4012****0026'},
                card_last4='0026',
                card_brand='Visa'
            )
            
            assert log is not None
            assert log.status == 'failed'
            assert log.error_message == 'Card declined'
            assert log.card_last4 == '0026'


def test_log_payment_attempt_without_user(client, test_order):
    """Test logging payment attempt for guest user."""
    with app.app_context():
        order = Order.query.get(test_order.id)
        
        with app.test_request_context():
            log = log_payment_attempt(
                order_id=order.id,
                user_id=None,
                payment_method='stripe',
                amount=12.34,
                currency='USD',
                status='pending',
                transaction_id='TXN-GUEST-123'
            )
            
            assert log is not None
            assert log.user_id is None
            assert log.order_id == order.id


def test_log_payment_attempt_captures_ip_and_user_agent(client, test_user, test_order):
    """Test that IP address and user agent are captured."""
    with app.app_context():
        with app.test_request_context(
            headers={'User-Agent': 'Mozilla/5.0 Test Browser'},
            environ_base={'REMOTE_ADDR': '192.168.1.1'}
        ):
            log = log_payment_attempt(
                order_id=test_order.id,
                user_id=test_user.id,
                payment_method='stripe',
                amount=12.34,
                currency='USD',
                status='completed'
            )
            
            assert log.ip_address is not None
            assert log.user_agent is not None


def test_log_payment_attempt_handles_dict_data(client, test_user, test_order):
    """Test that dict request/response data is converted to JSON."""
    with app.app_context():
        order = Order.query.get(test_order.id)
        user = User.query.get(test_user.id)
        
        with app.test_request_context():
            request_dict = {'order_id': order.id, 'amount': 12.34}
            response_dict = {'status': 'succeeded', 'transaction_id': 'TXN-123'}
            
            log = log_payment_attempt(
                order_id=order.id,
                user_id=user.id,
                payment_method='stripe',
                amount=12.34,
                currency='USD',
                status='completed',
                request_data=request_dict,
                response_data=response_dict
            )
            
            # Verify data is stored as JSON string
            assert isinstance(log.request_data, str)
            assert isinstance(log.response_data, str)
            
            # Verify it can be parsed back
            log_dict = log.to_dict()
            assert isinstance(log_dict['request_data'], dict)
            assert isinstance(log_dict['response_data'], dict)
            assert log_dict['request_data']['order_id'] == order.id


def test_log_payment_attempt_error_handling(client, test_user, test_order):
    """Test that logging errors don't break payment processing."""
    with app.app_context():
        with app.test_request_context():
            # Force an error by using invalid data
            # The function should handle it gracefully
            with patch('utils.payment_logger.db.session.add', side_effect=Exception("DB Error")):
                log = log_payment_attempt(
                    order_id=test_order.id,
                    user_id=test_user.id,
                    payment_method='stripe',
                    amount=12.34,
                    currency='USD',
                    status='completed'
                )
                
                # Should return None on error, not raise exception
                assert log is None


def test_payment_log_query_filters(client, test_user, test_order):
    """Test querying payment logs with filters."""
    with app.app_context():
        order = Order.query.get(test_order.id)
        user = User.query.get(test_user.id)
        
        # Create multiple logs with different statuses
        log1 = PaymentLog(
            order_id=order.id,
            user_id=user.id,
            payment_method='stripe',
            amount=12.34,
            currency='USD',
            status='completed'
        )
        log2 = PaymentLog(
            order_id=order.id,
            user_id=user.id,
            payment_method='jpmorgan',
            amount=25.00,
            currency='USD',
            status='failed'
        )
        log3 = PaymentLog(
            order_id=order.id,
            user_id=user.id,
            payment_method='stripe',
            amount=50.00,
            currency='USD',
            status='pending'
        )
        
        db.session.add_all([log1, log2, log3])
        db.session.commit()
        
        # Test filtering by status
        completed_logs = PaymentLog.query.filter_by(status='completed').all()
        assert len(completed_logs) == 1
        assert completed_logs[0].status == 'completed'
        
        # Test filtering by payment method
        stripe_logs = PaymentLog.query.filter_by(payment_method='stripe').all()
        assert len(stripe_logs) == 2
        
        # Test filtering by user
        user_logs = PaymentLog.query.filter_by(user_id=user.id).all()
        assert len(user_logs) == 3


def test_payment_log_serialization(client, test_user, test_order):
    """Test PaymentLog serialization with all fields."""
    with app.app_context():
        order = Order.query.get(test_order.id)
        user = User.query.get(test_user.id)
        
        log = PaymentLog(
            order_id=order.id,
            user_id=user.id,
            payment_method='jpmorgan',
            amount=99.99,
            currency='USD',
            status='completed',
            transaction_id='TXN-123',
            payment_intent_id='PI-456',
            external_transaction_id='EXT-789',
            request_data=json.dumps({'test': 'data'}),
            response_data=json.dumps({'response': 'data'}),
            error_message=None,
            ip_address='192.168.1.1',
            user_agent='Test Agent',
            card_last4='1234',
            card_brand='Visa'
        )
        db.session.add(log)
        db.session.commit()
        
        log_dict = log.to_dict()
        
        assert log_dict['order_id'] == order.id
        assert log_dict['user_id'] == user.id
        assert log_dict['payment_method'] == 'jpmorgan'
        assert log_dict['amount'] == 99.99
        assert log_dict['currency'] == 'USD'
        assert log_dict['status'] == 'completed'
        assert log_dict['transaction_id'] == 'TXN-123'
        assert log_dict['payment_intent_id'] == 'PI-456'
        assert log_dict['external_transaction_id'] == 'EXT-789'
        assert isinstance(log_dict['request_data'], dict)
        assert isinstance(log_dict['response_data'], dict)
        assert log_dict['ip_address'] == '192.168.1.1'
        assert log_dict['user_agent'] == 'Test Agent'
        assert log_dict['card_last4'] == '1234'
        assert log_dict['card_brand'] == 'Visa'
        assert 'created_at' in log_dict
        assert 'updated_at' in log_dict

