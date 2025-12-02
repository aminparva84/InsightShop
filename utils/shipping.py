"""
Shipping API Service
Handles integration with FedEx and UPS shipping APIs for rate calculation.
"""
import requests
import os
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from config import Config
import logging

logger = logging.getLogger(__name__)

class ShippingService:
    """Service for calculating shipping rates from FedEx and UPS."""
    
    def __init__(self):
        # FedEx API Configuration
        self.fedex_api_key = os.getenv('FEDEX_API_KEY', '')
        self.fedex_secret_key = os.getenv('FEDEX_SECRET_KEY', '')
        self.fedex_account_number = os.getenv('FEDEX_ACCOUNT_NUMBER', '')
        self.fedex_meter_number = os.getenv('FEDEX_METER_NUMBER', '')
        self.fedex_use_production = os.getenv('FEDEX_USE_PRODUCTION', 'false').lower() == 'true'
        
        # UPS API Configuration
        self.ups_api_key = os.getenv('UPS_API_KEY', '')
        self.ups_username = os.getenv('UPS_USERNAME', '')
        self.ups_password = os.getenv('UPS_PASSWORD', '')
        self.ups_account_number = os.getenv('UPS_ACCOUNT_NUMBER', '')
        self.ups_use_production = os.getenv('UPS_USE_PRODUCTION', 'false').lower() == 'true'
        
        # Store origin address (configure in environment variables)
        self.origin_address = {
            'street': os.getenv('SHIPPING_ORIGIN_STREET', '123 Main St'),
            'city': os.getenv('SHIPPING_ORIGIN_CITY', 'New York'),
            'state': os.getenv('SHIPPING_ORIGIN_STATE', 'NY'),
            'zip': os.getenv('SHIPPING_ORIGIN_ZIP', '10001'),
            'country': os.getenv('SHIPPING_ORIGIN_COUNTRY', 'US')
        }
        
        # Default shipping rates (fallback)
        self.default_rates = {
            'ground': Decimal('5.00'),
            'express': Decimal('15.00'),
            'overnight': Decimal('25.00')
        }
    
    def calculate_rates(
        self,
        destination: Dict[str, str],
        weight: float,
        dimensions: Optional[Dict[str, float]] = None,
        value: Optional[Decimal] = None
    ) -> Dict[str, List[Dict]]:
        """
        Calculate shipping rates from FedEx and UPS.
        
        Args:
            destination: Dict with 'street', 'city', 'state', 'zip', 'country'
            weight: Package weight in pounds
            dimensions: Optional dict with 'length', 'width', 'height' in inches
            value: Optional package value for insurance
        
        Returns:
            Dict with 'fedex' and 'ups' keys, each containing list of rate options
        """
        results = {
            'fedex': [],
            'ups': [],
            'errors': []
        }
        
        # Calculate FedEx rates
        try:
            fedex_rates = self._calculate_fedex_rates(destination, weight, dimensions, value)
            results['fedex'] = fedex_rates
        except Exception as e:
            logger.error(f"FedEx rate calculation error: {str(e)}")
            results['errors'].append(f"FedEx: {str(e)}")
            # Add fallback rates
            results['fedex'] = self._get_fedex_fallback_rates()
        
        # Calculate UPS rates
        try:
            ups_rates = self._calculate_ups_rates(destination, weight, dimensions, value)
            results['ups'] = ups_rates
        except Exception as e:
            logger.error(f"UPS rate calculation error: {str(e)}")
            results['errors'].append(f"UPS: {str(e)}")
            # Add fallback rates
            results['ups'] = self._get_ups_fallback_rates()
        
        return results
    
    def _calculate_fedex_rates(
        self,
        destination: Dict[str, str],
        weight: float,
        dimensions: Optional[Dict[str, float]] = None,
        value: Optional[Decimal] = None
    ) -> List[Dict]:
        """Calculate FedEx shipping rates."""
        if not self.fedex_api_key or not self.fedex_secret_key:
            logger.warning("FedEx credentials not configured, using fallback rates")
            return self._get_fedex_fallback_rates()
        
        try:
            # FedEx API endpoint (using REST API)
            base_url = 'https://apis.fedex.com' if self.fedex_use_production else 'https://apis-sandbox.fedex.com'
            
            # Get OAuth token
            token_url = f"{base_url}/oauth/token"
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': self.fedex_api_key,
                'client_secret': self.fedex_secret_key
            }
            
            token_response = requests.post(token_url, data=token_data, timeout=10)
            if token_response.status_code != 200:
                raise Exception(f"FedEx authentication failed: {token_response.status_code}")
            
            access_token = token_response.json().get('access_token')
            if not access_token:
                raise Exception("Failed to get FedEx access token")
            
            # Calculate rates
            rate_url = f"{base_url}/rate/v1/rates/quotes"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'X-locale': 'en_US'
            }
            
            # Build rate request payload
            payload = {
                'accountNumber': {
                    'value': self.fedex_account_number
                },
                'requestedShipment': {
                    'shipper': {
                        'address': {
                            'streetLines': [self.origin_address['street']],
                            'city': self.origin_address['city'],
                            'stateOrProvinceCode': self.origin_address['state'],
                            'postalCode': self.origin_address['zip'],
                            'countryCode': self.origin_address['country']
                        }
                    },
                    'recipients': [{
                        'address': {
                            'streetLines': [destination.get('street', '')],
                            'city': destination.get('city', ''),
                            'stateOrProvinceCode': destination.get('state', ''),
                            'postalCode': destination.get('zip', ''),
                            'countryCode': destination.get('country', 'US')
                        }
                    }],
                    'rateRequestType': ['ACCOUNT', 'LIST'],
                    'requestedPackageLineItems': [{
                        'weight': {
                            'units': 'LB',
                            'value': weight
                        }
                    }]
                }
            }
            
            # Add dimensions if provided
            if dimensions:
                payload['requestedShipment']['requestedPackageLineItems'][0]['dimensions'] = {
                    'length': dimensions.get('length', 1),
                    'width': dimensions.get('width', 1),
                    'height': dimensions.get('height', 1),
                    'units': 'IN'
                }
            
            # Add service types to request
            service_types = [
                'FEDEX_GROUND',
                'FEDEX_2_DAY',
                'FEDEX_EXPRESS_SAVER',
                'STANDARD_OVERNIGHT',
                'PRIORITY_OVERNIGHT'
            ]
            
            rates = []
            for service_type in service_types:
                payload['requestedShipment']['serviceType'] = service_type
                
                response = requests.post(rate_url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'output' in data and 'rateReplyDetails' in data['output']:
                        for rate_detail in data['output']['rateReplyDetails']:
                            if 'ratedShipmentDetails' in rate_detail:
                                for rated_shipment in rate_detail['ratedShipmentDetails']:
                                    if 'totalNetCharge' in rated_shipment:
                                        rates.append({
                                            'service': self._format_fedex_service_name(service_type),
                                            'service_code': service_type,
                                            'carrier': 'FedEx',
                                            'price': float(rated_shipment['totalNetCharge']['amount']),
                                            'currency': rated_shipment['totalNetCharge'].get('currency', 'USD'),
                                            'estimated_days': rate_detail.get('commit', {}).get('daysInTransit', None)
                                        })
                                        break  # Use first rated shipment
            
            # If no rates found, return fallback
            if not rates:
                return self._get_fedex_fallback_rates()
            
            return sorted(rates, key=lambda x: x['price'])
            
        except Exception as e:
            logger.error(f"FedEx API error: {str(e)}")
            return self._get_fedex_fallback_rates()
    
    def _calculate_ups_rates(
        self,
        destination: Dict[str, str],
        weight: float,
        dimensions: Optional[Dict[str, float]] = None,
        value: Optional[Decimal] = None
    ) -> List[Dict]:
        """Calculate UPS shipping rates."""
        if not self.ups_api_key or not self.ups_username or not self.ups_password:
            logger.warning("UPS credentials not configured, using fallback rates")
            return self._get_ups_fallback_rates()
        
        try:
            # UPS API endpoint
            base_url = 'https://onlinetools.ups.com' if self.ups_use_production else 'https://wwwcie.ups.com'
            
            # UPS Rating API
            rate_url = f"{base_url}/api/rating/v1/Rate"
            
            # Build request payload
            payload = {
                'RateRequest': {
                    'Request': {
                        'RequestOption': 'Rate',
                        'TransactionReference': {
                            'CustomerContext': 'InsightShop Shipping Rate Request'
                        }
                    },
                    'Shipment': {
                        'Shipper': {
                            'Name': 'InsightShop',
                            'ShipperNumber': self.ups_account_number,
                            'Address': {
                                'AddressLine': [self.origin_address['street']],
                                'City': self.origin_address['city'],
                                'StateProvinceCode': self.origin_address['state'],
                                'PostalCode': self.origin_address['zip'],
                                'CountryCode': self.origin_address['country']
                            }
                        },
                        'ShipTo': {
                            'Name': destination.get('name', 'Customer'),
                            'Address': {
                                'AddressLine': [destination.get('street', '')],
                                'City': destination.get('city', ''),
                                'StateProvinceCode': destination.get('state', ''),
                                'PostalCode': destination.get('zip', ''),
                                'CountryCode': destination.get('country', 'US')
                            }
                        },
                        'ShipFrom': {
                            'Name': 'InsightShop',
                            'Address': {
                                'AddressLine': [self.origin_address['street']],
                                'City': self.origin_address['city'],
                                'StateProvinceCode': self.origin_address['state'],
                                'PostalCode': self.origin_address['zip'],
                                'CountryCode': self.origin_address['country']
                            }
                        },
                        'Package': {
                            'PackagingType': {
                                'Code': '02',  # Customer Supplied Package
                                'Description': 'Package'
                            },
                            'Dimensions': {
                                'UnitOfMeasurement': {
                                    'Code': 'IN',
                                    'Description': 'Inches'
                                },
                                'Length': str(dimensions.get('length', 10) if dimensions else 10),
                                'Width': str(dimensions.get('width', 10) if dimensions else 10),
                                'Height': str(dimensions.get('height', 10) if dimensions else 10)
                            },
                            'PackageWeight': {
                                'UnitOfMeasurement': {
                                    'Code': 'LBS',
                                    'Description': 'Pounds'
                                },
                                'Weight': str(weight)
                            }
                        }
                    }
                }
            }
            
            # Add service types
            service_codes = {
                '03': 'UPS Ground',
                '12': 'UPS 3 Day Select',
                '02': 'UPS 2nd Day Air',
                '01': 'UPS Next Day Air',
                '14': 'UPS Next Day Air Early'
            }
            
            rates = []
            for service_code, service_name in service_codes.items():
                payload['RateRequest']['Shipment']['Service'] = {
                    'Code': service_code,
                    'Description': service_name
                }
                
                # UPS uses Basic Authentication
                auth = (self.ups_username, self.ups_password)
                headers = {
                    'Content-Type': 'application/json',
                    'transId': 'InsightShop-' + str(os.urandom(8).hex()),
                    'transactionSrc': 'InsightShop'
                }
                
                response = requests.post(
                    rate_url,
                    json=payload,
                    headers=headers,
                    auth=auth,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'RateResponse' in data and 'RatedShipment' in data['RateResponse']:
                        rated_shipment = data['RateResponse']['RatedShipment']
                        if 'TotalCharges' in rated_shipment:
                            rates.append({
                                'service': service_name,
                                'service_code': service_code,
                                'carrier': 'UPS',
                                'price': float(rated_shipment['TotalCharges']['MonetaryValue']),
                                'currency': rated_shipment['TotalCharges'].get('CurrencyCode', 'USD'),
                                'estimated_days': self._get_ups_estimated_days(service_code)
                            })
            
            # If no rates found, return fallback
            if not rates:
                return self._get_ups_fallback_rates()
            
            return sorted(rates, key=lambda x: x['price'])
            
        except Exception as e:
            logger.error(f"UPS API error: {str(e)}")
            return self._get_ups_fallback_rates()
    
    def _get_fedex_fallback_rates(self) -> List[Dict]:
        """Get fallback FedEx rates when API is unavailable."""
        return [
            {
                'service': 'FedEx Ground',
                'service_code': 'FEDEX_GROUND',
                'carrier': 'FedEx',
                'price': float(self.default_rates['ground']),
                'currency': 'USD',
                'estimated_days': 5
            },
            {
                'service': 'FedEx 2Day',
                'service_code': 'FEDEX_2_DAY',
                'carrier': 'FedEx',
                'price': float(self.default_rates['express']),
                'currency': 'USD',
                'estimated_days': 2
            },
            {
                'service': 'FedEx Overnight',
                'service_code': 'STANDARD_OVERNIGHT',
                'carrier': 'FedEx',
                'price': float(self.default_rates['overnight']),
                'currency': 'USD',
                'estimated_days': 1
            }
        ]
    
    def _get_ups_fallback_rates(self) -> List[Dict]:
        """Get fallback UPS rates when API is unavailable."""
        return [
            {
                'service': 'UPS Ground',
                'service_code': '03',
                'carrier': 'UPS',
                'price': float(self.default_rates['ground']),
                'currency': 'USD',
                'estimated_days': 5
            },
            {
                'service': 'UPS 2nd Day Air',
                'service_code': '02',
                'carrier': 'UPS',
                'price': float(self.default_rates['express']),
                'currency': 'USD',
                'estimated_days': 2
            },
            {
                'service': 'UPS Next Day Air',
                'service_code': '01',
                'carrier': 'UPS',
                'price': float(self.default_rates['overnight']),
                'currency': 'USD',
                'estimated_days': 1
            }
        ]
    
    def _format_fedex_service_name(self, service_code: str) -> str:
        """Format FedEx service code to readable name."""
        service_names = {
            'FEDEX_GROUND': 'FedEx Ground',
            'FEDEX_2_DAY': 'FedEx 2Day',
            'FEDEX_EXPRESS_SAVER': 'FedEx Express Saver',
            'STANDARD_OVERNIGHT': 'FedEx Standard Overnight',
            'PRIORITY_OVERNIGHT': 'FedEx Priority Overnight'
        }
        return service_names.get(service_code, service_code)
    
    def _get_ups_estimated_days(self, service_code: str) -> Optional[int]:
        """Get estimated delivery days for UPS service."""
        days_map = {
            '03': 5,  # Ground
            '12': 3,  # 3 Day Select
            '02': 2,  # 2nd Day Air
            '01': 1,  # Next Day Air
            '14': 1   # Next Day Air Early
        }
        return days_map.get(service_code)
    
    def calculate_package_weight(self, cart_items: List[Dict]) -> float:
        """Calculate total package weight from cart items."""
        # Default weight per item (in pounds) - can be enhanced with product weight field
        default_weight_per_item = 0.5
        total_weight = 0.0
        
        for item in cart_items:
            quantity = item.get('quantity', 1)
            # If product has weight field, use it; otherwise use default
            product = item.get('product', {})
            item_weight = product.get('weight', default_weight_per_item)
            total_weight += item_weight * quantity
        
        # Minimum weight
        return max(total_weight, 0.1)
    
    def calculate_package_dimensions(self, cart_items: List[Dict]) -> Dict[str, float]:
        """Calculate package dimensions from cart items."""
        # Default dimensions (in inches) - can be enhanced with product dimensions
        default_length = 10
        default_width = 8
        default_height = 6
        
        # For now, return default dimensions
        # In production, calculate based on items
        return {
            'length': default_length,
            'width': default_width,
            'height': default_height
        }

