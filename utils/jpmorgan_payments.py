"""
J.P. Morgan Payments API Integration Utility

This module handles OAuth2 token retrieval and payment processing
for the J.P. Morgan Payments API.
"""

import requests
import time
import uuid
from typing import Optional, Dict, Any
from config import Config


class JPMorganPaymentsClient:
    """Client for interacting with J.P. Morgan Payments API."""
    
    def __init__(self):
        self.access_token_url = Config.JPMORGAN_ACCESS_TOKEN_URL
        self.client_id = Config.JPMORGAN_CLIENT_ID
        self.client_secret = Config.JPMORGAN_CLIENT_SECRET
        self.api_base_url = Config.JPMORGAN_API_BASE_URL
        self.merchant_id = Config.JPMORGAN_MERCHANT_ID
        self.scope = Config.JPMORGAN_SCOPE
        
        # Cache for access token
        self._cached_token: Optional[str] = None
        self._token_expires_at: float = 0
    
    def _get_access_token(self, force_refresh: bool = False) -> str:
        """
        Retrieve an OAuth2 access token from J.P. Morgan Payments API.
        
        Args:
            force_refresh: If True, force a new token even if cached token is valid
            
        Returns:
            Access token string
            
        Raises:
            Exception: If token retrieval fails
        """
        # Return cached token if still valid and not forcing refresh
        if not force_refresh and self._cached_token and time.time() < self._token_expires_at:
            return self._cached_token
        
        if not self.client_id or not self.client_secret:
            raise ValueError("J.P. Morgan Payments credentials not configured. Set JPMORGAN_CLIENT_ID and JPMORGAN_CLIENT_SECRET.")
        
        # Prepare request data
        data = {
            'grant_type': 'client_credentials',
            'scope': self.scope,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(
                self.access_token_url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            if 'error' in token_data:
                error_msg = token_data.get('error_description', token_data.get('error', 'Unknown error'))
                raise Exception(f"Failed to retrieve access token: {error_msg}")
            
            access_token = token_data.get('access_token')
            if not access_token:
                raise Exception("Access token not found in response")
            
            # Cache the token with expiration buffer (subtract 60 seconds for safety)
            expires_in = token_data.get('expires_in', 3600)
            self._cached_token = access_token
            self._token_expires_at = time.time() + expires_in - 60
            
            return access_token
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while retrieving access token: {str(e)}")
        except Exception as e:
            raise Exception(f"Error retrieving access token: {str(e)}")
    
    def create_payment(
        self,
        amount: float,
        currency: str = 'USD',
        card_number: str = None,
        expiry_month: int = None,
        expiry_year: int = None,
        capture_method: str = 'NOW',
        merchant_company_name: str = 'Payment Company',
        merchant_product_name: str = 'Application Name',
        merchant_version: str = '1.235',
        merchant_category_code: str = '4899',
        is_bill_payment: bool = True,
        initiator_type: str = 'CARDHOLDER',
        account_on_file: str = 'NOT_STORED',
        is_amount_final: bool = True,
        request_id: str = None
    ) -> Dict[str, Any]:
        """
        Create a payment request using J.P. Morgan Payments API.
        
        Args:
            amount: Payment amount (in smallest currency unit, e.g., cents for USD)
            currency: Currency code (default: 'USD')
            card_number: Credit card number
            expiry_month: Card expiry month (1-12)
            expiry_year: Card expiry year (4 digits)
            capture_method: Capture method ('NOW' or 'LATER')
            merchant_company_name: Merchant company name
            merchant_product_name: Merchant product name
            merchant_version: Merchant software version
            merchant_category_code: Merchant category code
            is_bill_payment: Whether this is a bill payment
            initiator_type: Initiator type (default: 'CARDHOLDER')
            account_on_file: Account on file status (default: 'NOT_STORED')
            is_amount_final: Whether amount is final
            request_id: Optional request ID (UUID format)
            
        Returns:
            Payment response dictionary
            
        Raises:
            Exception: If payment creation fails
        """
        # Get access token
        access_token = self._get_access_token()
        
        # Generate request ID if not provided
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Prepare payment request payload
        payment_data = {
            'captureMethod': capture_method,
            'amount': int(amount),  # Ensure integer for amount
            'currency': currency,
            'merchant': {
                'merchantSoftware': {
                    'companyName': merchant_company_name,
                    'productName': merchant_product_name,
                    'version': merchant_version
                },
                'merchantCategoryCode': merchant_category_code
            },
            'initiatorType': initiator_type,
            'accountOnFile': account_on_file,
            'isAmountFinal': is_amount_final
        }
        
        # Add card payment method if card details provided
        if card_number and expiry_month and expiry_year:
            payment_data['paymentMethodType'] = {
                'card': {
                    'accountNumber': card_number,
                    'expiry': {
                        'month': expiry_month,
                        'year': expiry_year
                    },
                    'isBillPayment': is_bill_payment
                }
            }
        
        # Prepare headers
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'merchant-id': self.merchant_id,
            'minorVersion': '',
            'request-id': request_id
        }
        
        # Make payment request
        url = f"{self.api_base_url}/payments"
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payment_data,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get('error_description', error_data.get('error', str(e)))
            except:
                error_detail = str(e)
            
            raise Exception(f"Payment request failed: {error_detail}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while processing payment: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing payment: {str(e)}")
    
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Retrieve payment status by transaction ID.
        
        Args:
            transaction_id: Transaction ID from payment response
            
        Returns:
            Payment status dictionary
            
        Raises:
            Exception: If status retrieval fails
        """
        access_token = self._get_access_token()
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'merchant-id': self.merchant_id,
            'minorVersion': '',
            'request-id': str(uuid.uuid4())
        }
        
        url = f"{self.api_base_url}/payments/{transaction_id}"
        
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception(f"Payment not found or status endpoint not available: {transaction_id}")
            raise Exception(f"Error retrieving payment status: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error retrieving payment status: {str(e)}")


# Singleton instance
_jpmorgan_client: Optional[JPMorganPaymentsClient] = None


def get_jpmorgan_client() -> JPMorganPaymentsClient:
    """Get or create the singleton JPMorganPaymentsClient instance."""
    global _jpmorgan_client
    if _jpmorgan_client is None:
        _jpmorgan_client = JPMorganPaymentsClient()
    return _jpmorgan_client

