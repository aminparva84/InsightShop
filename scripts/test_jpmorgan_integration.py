"""
Test script to verify J.P. Morgan Payments API integration.
This script tests the actual API calls with real credentials.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.jpmorgan_payments import get_jpmorgan_client
import json


def test_token_retrieval():
    """Test OAuth2 token retrieval."""
    print("=" * 60)
    print("Testing OAuth2 Token Retrieval")
    print("=" * 60)
    
    try:
        client = get_jpmorgan_client()
        print("[OK] Client initialized")
        print(f"  Access Token URL: {client.access_token_url}")
        print(f"  Client ID: {client.client_id[:20]}...")
        print(f"  API Base URL: {client.api_base_url}")
        print(f"  Merchant ID: {client.merchant_id}")
        print()
        
        print("Requesting access token...")
        token = client._get_access_token(force_refresh=True)
        
        print("[OK] Token retrieved successfully!")
        print(f"  Token (first 50 chars): {token[:50]}...")
        print(f"  Token length: {len(token)}")
        print()
        
        # Test token caching
        print("Testing token caching...")
        token2 = client._get_access_token(force_refresh=False)
        assert token == token2, "Token should be cached"
        print("[OK] Token caching works correctly")
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        print()
        return False


def test_payment_creation():
    """Test payment creation."""
    print("=" * 60)
    print("Testing Payment Creation")
    print("=" * 60)
    
    try:
        client = get_jpmorgan_client()
        
        print("Creating test payment...")
        print("  Amount: $12.34 (1234 cents)")
        print("  Card: 4012000033330026")
        print("  Expiry: 05/2027")
        print()
        
        response = client.create_payment(
            amount=1234,  # $12.34 in cents
            currency='USD',
            card_number='4012000033330026',
            expiry_month=5,
            expiry_year=2027,
            capture_method='NOW',
            merchant_company_name='InsightShop',
            merchant_product_name='InsightShop Application',
            merchant_version='1.0.0'
        )
        
        print("[OK] Payment request sent successfully!")
        print()
        print("Response:")
        print(json.dumps(response, indent=2))
        print()
        
        # Check response
        transaction_id = response.get('transactionId')
        response_status = response.get('responseStatus')
        response_code = response.get('responseCode')
        
        print(f"Transaction ID: {transaction_id}")
        print(f"Response Status: {response_status}")
        print(f"Response Code: {response_code}")
        print()
        
        if response_status == 'SUCCESS' and response_code == 'APPROVED':
            print("[OK] Payment approved successfully!")
            return True, transaction_id
        else:
            print(f"[WARNING] Payment not approved: {response_code}")
            return False, transaction_id
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        print()
        return False, None


def test_payment_status(transaction_id):
    """Test payment status retrieval."""
    if not transaction_id:
        print("Skipping status check (no transaction ID)")
        return False
    
    print("=" * 60)
    print("Testing Payment Status Retrieval")
    print("=" * 60)
    
    try:
        client = get_jpmorgan_client()
        
        print(f"Retrieving status for transaction: {transaction_id}")
        print()
        
        status = client.get_payment_status(transaction_id)
        
        print("[OK] Status retrieved successfully!")
        print()
        print("Status Response:")
        print(json.dumps(status, indent=2))
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        print()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("J.P. Morgan Payments API Integration Test")
    print("=" * 60)
    print()
    
    results = {
        'token_retrieval': False,
        'payment_creation': False,
        'payment_status': False
    }
    
    # Test 1: Token retrieval
    results['token_retrieval'] = test_token_retrieval()
    
    if not results['token_retrieval']:
        print("⚠ Skipping payment tests (token retrieval failed)")
        print_summary(results)
        return
    
    # Test 2: Payment creation
    payment_success, transaction_id = test_payment_creation()
    results['payment_creation'] = payment_success
    
    # Test 3: Payment status
    if transaction_id:
        results['payment_status'] = test_payment_status(transaction_id)
    
    # Summary
    print_summary(results)


def print_summary(results):
    """Print test summary."""
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print()
    
    all_passed = all(results.values())
    if all_passed:
        print("[SUCCESS] All tests passed!")
    else:
        print("[WARNING] Some tests failed. Check the output above for details.")
    print()


if __name__ == '__main__':
    main()

