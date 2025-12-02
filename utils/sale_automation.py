"""Automation utilities for managing sales based on dates and events."""

from models.database import db
from models.sale import Sale
from datetime import date, timedelta
from utils.seasonal_events import get_cyber_monday, get_thanksgiving, get_current_holidays_and_events


def auto_activate_sales():
    """
    Automatically activate sales based on their start dates and auto_activate flag.
    This should be called daily (via cron or scheduled task).
    """
    try:
        today = date.today()
        activated_count = 0
        deactivated_count = 0
        
        # Activate sales that should start today
        sales_to_activate = Sale.query.filter(
            Sale.start_date <= today,
            Sale.is_active == False,
            Sale.auto_activate == True
        ).all()
        
        for sale in sales_to_activate:
            sale.is_active = True
            activated_count += 1
            print(f"Auto-activated sale: {sale.name} (ID: {sale.id})")
        
        # Note: We don't auto-deactivate based on end_date
        # Sales stay active until manually deactivated by admin
        # This gives admins control over when sales end
        
        if activated_count > 0:
            db.session.commit()
            print(f"Auto-activated {activated_count} sale(s)")
        
        return {
            'activated': activated_count,
            'deactivated': deactivated_count,
            'date': today.isoformat()
        }
    except Exception as e:
        db.session.rollback()
        print(f"Error in auto_activate_sales: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': str(e),
            'activated': 0,
            'deactivated': 0
        }


def sync_holiday_sales():
    """
    Sync holiday sales with current dates (e.g., Cyber Monday, Thanksgiving).
    Creates or updates sales for upcoming holidays if they don't exist.
    """
    try:
        today = date.today()
        current_year = today.year
        created_count = 0
        updated_count = 0
        
        # Get current holidays
        current_events = get_current_holidays_and_events()
        
        # Handle Cyber Monday
        cyber_monday_date = get_cyber_monday(current_year)
        if cyber_monday_date < today:
            cyber_monday_date = get_cyber_monday(current_year + 1)
        
        # Check if Cyber Monday sale exists
        cyber_monday_sale = Sale.query.filter_by(event_name='cyber_monday').first()
        if not cyber_monday_sale:
            # Create Cyber Monday sale if we're within 7 days of Cyber Monday
            days_until = (cyber_monday_date - today).days
            if -7 <= days_until <= 7:  # Within a week before or after
                cyber_monday_sale = Sale(
                    name='Cyber Monday Sale',
                    description='Get amazing deals on Cyber Monday! 45% off on all products!',
                    sale_type='holiday',
                    event_name='cyber_monday',
                    discount_percentage=45.0,
                    start_date=today if today >= cyber_monday_date else cyber_monday_date,
                    end_date=cyber_monday_date + timedelta(days=7),
                    product_filters=None,
                    is_active=True if today >= cyber_monday_date else False,
                    auto_activate=True
                )
                db.session.add(cyber_monday_sale)
                created_count += 1
                print(f"Created Cyber Monday sale (ID: {cyber_monday_sale.id})")
        else:
            # Update existing Cyber Monday sale dates if needed
            if cyber_monday_sale.start_date < today and not cyber_monday_sale.is_active:
                cyber_monday_sale.is_active = True
                updated_count += 1
                print(f"Updated Cyber Monday sale (ID: {cyber_monday_sale.id})")
        
        # Handle Thanksgiving
        thanksgiving_date = get_thanksgiving(current_year)
        if thanksgiving_date < today:
            thanksgiving_date = get_thanksgiving(current_year + 1)
        
        thanksgiving_sale = Sale.query.filter_by(event_name='thanksgiving').first()
        if not thanksgiving_sale:
            # Create Thanksgiving sale if we're within 7 days
            days_until = (thanksgiving_date - today).days
            if -7 <= days_until <= 7:
                thanksgiving_sale = Sale(
                    name='Thanksgiving Sale',
                    description='Celebrate Thanksgiving with amazing deals!',
                    sale_type='holiday',
                    event_name='thanksgiving',
                    discount_percentage=40.0,
                    start_date=today if today >= thanksgiving_date else thanksgiving_date,
                    end_date=thanksgiving_date + timedelta(days=3),
                    product_filters=None,
                    is_active=True if today >= thanksgiving_date else False,
                    auto_activate=True
                )
                db.session.add(thanksgiving_sale)
                created_count += 1
                print(f"Created Thanksgiving sale (ID: {thanksgiving_sale.id})")
        
        if created_count > 0 or updated_count > 0:
            db.session.commit()
        
        return {
            'created': created_count,
            'updated': updated_count,
            'date': today.isoformat()
        }
    except Exception as e:
        db.session.rollback()
        print(f"Error in sync_holiday_sales: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': str(e),
            'created': 0,
            'updated': 0
        }


def run_sale_automation():
    """
    Main function to run all sale automation tasks.
    Call this daily via cron or scheduled task.
    """
    results = {
        'auto_activate': auto_activate_sales(),
        'sync_holidays': sync_holiday_sales(),
        'timestamp': date.today().isoformat()
    }
    return results

