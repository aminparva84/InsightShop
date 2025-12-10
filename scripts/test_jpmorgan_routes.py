"""
Test script to verify J.P. Morgan Payments API routes are accessible.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment to avoid Unicode issues
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    from app import app
    from utils.jpmorgan_payments import get_jpmorgan_client
    
    print("=" * 60)
    print("Testing J.P. Morgan Payments Routes")
    print("=" * 60)
    print()
    
    # Check routes
    with app.app_context():
        routes = [str(rule) for rule in app.url_map.iter_rules() if 'jpmorgan' in str(rule)]
        print("Registered JPMorgan routes:")
        for route in routes:
            print(f"  - {route}")
        print()
        
        # Test client initialization
        print("Testing client initialization...")
        client = get_jpmorgan_client()
        print(f"[OK] Client initialized")
        print(f"  Access Token URL: {client.access_token_url}")
        print(f"  API Base URL: {client.api_base_url}")
        print(f"  Merchant ID: {client.merchant_id}")
        print()
        
        # Test token endpoint (using test client)
        print("Testing token retrieval...")
        with app.test_client() as test_client:
            # Mock the requests.post to avoid actual API call in route test
            from unittest.mock import patch, Mock
            
            with patch('utils.jpmorgan_payments.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.json.return_value = {
                    'access_token': 'test_token_12345',
                    'expires_in': 3600
                }
                mock_response.raise_for_status = Mock()
                mock_post.return_value = mock_response
                
                response = test_client.get('/api/payments/jpmorgan/token')
                print(f"  Token endpoint status: {response.status_code}")
                if response.status_code == 200:
                    print("[OK] Token endpoint works")
                else:
                    print(f"[ERROR] Token endpoint failed: {response.data}")
        print()
        
        print("[SUCCESS] Route verification complete!")
        print()
        print("Available endpoints:")
        print("  1. GET  /api/payments/jpmorgan/token")
        print("  2. POST /api/payments/jpmorgan/create-payment")
        print("  3. GET  /api/payments/jpmorgan/payment-status/<transaction_id>")
        
except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()


