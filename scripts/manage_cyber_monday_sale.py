"""Deactivate Thanksgiving sale and activate Cyber Monday sale with 45% discount."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models.database import db
from models.sale import Sale
from datetime import date, timedelta
import os
from config import Config

# Create minimal app context
app = Flask(__name__, instance_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance'))
# Use instance folder for database
db_path = os.path.join(app.instance_path, Config.DB_PATH) if not os.path.isabs(Config.DB_PATH) else Config.DB_PATH
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def manage_cyber_monday_sale():
    """Deactivate Thanksgiving sales and create/activate Cyber Monday sale."""
    with app.app_context():
        try:
            # Find and deactivate all Thanksgiving sales
            thanksgiving_sales = Sale.query.filter(
                Sale.event_name == 'thanksgiving',
                Sale.is_active == True
            ).all()
            
            deactivated_count = 0
            for sale in thanksgiving_sales:
                sale.is_active = False
                deactivated_count += 1
                print(f"Deactivated: {sale.name} (ID: {sale.id})")
            
            if deactivated_count > 0:
                db.session.commit()
                print(f"\nDeactivated {deactivated_count} Thanksgiving sale(s)")
            else:
                print("\nNo active Thanksgiving sales found to deactivate")
            
            # Check if Cyber Monday sale already exists
            today = date.today()
            current_year = today.year
            
            # Cyber Monday is the Monday after Thanksgiving (4th Thursday in November)
            # Calculate Thanksgiving date
            from utils.seasonal_events import get_thanksgiving, get_cyber_monday
            thanksgiving_date = get_thanksgiving(current_year)
            cyber_monday_date = get_cyber_monday(current_year)
            
            # Check if we're past Cyber Monday this year, use next year's date
            if cyber_monday_date < today:
                cyber_monday_date = get_cyber_monday(current_year + 1)
            
            existing_cyber_monday = Sale.query.filter(
                Sale.event_name == 'cyber_monday',
                Sale.is_active == True
            ).first()
            
            if existing_cyber_monday:
                # Update existing sale
                existing_cyber_monday.discount_percentage = 45.0
                existing_cyber_monday.is_active = True
                existing_cyber_monday.start_date = today
                existing_cyber_monday.end_date = cyber_monday_date + timedelta(days=7)  # Run for a week
                existing_cyber_monday.name = 'Cyber Monday Sale'
                existing_cyber_monday.description = 'Get amazing deals on Cyber Monday! 45% off on all products!'
                db.session.commit()
                print(f"\nUpdated existing Cyber Monday sale (ID: {existing_cyber_monday.id})")
                print(f"   Discount: 45%")
                print(f"   Start Date: {today}")
                print(f"   End Date: {existing_cyber_monday.end_date}")
                print(f"   Status: ACTIVE")
            else:
                # Create new Cyber Monday sale
                cyber_monday_sale = Sale(
                    name='Cyber Monday Sale',
                    description='Get amazing deals on Cyber Monday! 45% off on all products!',
                    sale_type='holiday',
                    event_name='cyber_monday',
                    discount_percentage=45.0,
                    start_date=today,
                    end_date=cyber_monday_date + timedelta(days=7),  # Run for a week
                    product_filters=None,  # Apply to all products
                    is_active=True,
                    auto_activate=False
                )
                
                db.session.add(cyber_monday_sale)
                db.session.commit()
                print(f"\nCreated new Cyber Monday sale (ID: {cyber_monday_sale.id})")
                print(f"   Discount: 45%")
                print(f"   Start Date: {today}")
                print(f"   End Date: {cyber_monday_sale.end_date}")
                print(f"   Status: ACTIVE")
            
            print("\nCyber Monday sale is now active with 45% discount!")
            print("Thanksgiving sales have been deactivated.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\nError managing sales: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    manage_cyber_monday_sale()
