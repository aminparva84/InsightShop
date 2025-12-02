"""Test script to verify the sale system is working correctly."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models.database import db
from models.product import Product
from models.sale import Sale
from datetime import date
from config import Config

# Create minimal app context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, Config.DB_PATH)}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def test_sale_system():
    """Test that the sale system is working correctly."""
    with app.app_context():
        try:
            print("=" * 60)
            print("Testing Sale System")
            print("=" * 60)
            
            # 1. Check if sales exist
            sales = Sale.query.all()
            print(f"\n1. Found {len(sales)} sale(s) in database:")
            for sale in sales:
                print(f"   - {sale.name}: {sale.discount_percentage}% off")
                print(f"     Active: {sale.is_active}, Start: {sale.start_date}, End: {sale.end_date}")
                print(f"     Currently Active: {sale.is_currently_active()}")
            
            # 2. Check active sales
            active_sales = Sale.query.filter_by(is_active=True).all()
            print(f"\n2. Active sales: {len(active_sales)}")
            for sale in active_sales:
                print(f"   - {sale.name}: {sale.discount_percentage}% off")
            
            # 3. Test product sale price calculation
            products = Product.query.filter_by(is_active=True).limit(5).all()
            print(f"\n3. Testing sale price calculation on {len(products)} products:")
            
            for product in products:
                sale_data = product.get_sale_price()
                product_dict = product.to_dict()
                
                print(f"\n   Product: {product.name}")
                print(f"   Original Price: ${float(product.price):.2f}")
                
                if sale_data:
                    print(f"   [ON SALE]")
                    print(f"   Sale Price: ${sale_data['sale_price']:.2f}")
                    print(f"   Discount: {sale_data['discount_percentage']:.0f}%")
                    print(f"   Sale: {sale_data.get('sale', {}).get('name', 'Unknown')}")
                else:
                    print(f"   [Not on sale]")
                
                # Verify to_dict includes sale info
                if product_dict.get('on_sale'):
                    print(f"   [OK] Product.to_dict() shows on_sale=True")
                    print(f"   Price in dict: ${product_dict['price']:.2f} (should be sale price)")
                    print(f"   Original price: ${product_dict['original_price']:.2f}")
                else:
                    print(f"   Product.to_dict() shows on_sale=False")
                    print(f"   Price in dict: ${product_dict['price']:.2f}")
            
            # 4. Test sale matching
            if active_sales:
                print(f"\n4. Testing sale matching:")
                test_product = products[0] if products else None
                if test_product:
                    for sale in active_sales:
                        matches = sale.matches_product(test_product)
                        print(f"   {sale.name} matches {test_product.name}: {matches}")
            
            print("\n" + "=" * 60)
            print("Sale System Test Complete")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Error testing sale system: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_sale_system()
    sys.exit(0 if success else 1)

