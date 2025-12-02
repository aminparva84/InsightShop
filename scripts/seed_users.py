"""Script to seed superadmin and demo users."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
from models.user import User
import bcrypt

def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_users():
    """Create superadmin and demo users."""
    with app.app_context():
        try:
            # Check if superadmin already exists (try both email formats)
            superadmin = User.query.filter_by(email='superadmin@insightshop.com').first() or \
                        User.query.filter_by(email='superadmin').first()
            if not superadmin:
                print("Creating superadmin user...")
                superadmin = User(
                    email='superadmin@insightshop.com',
                    first_name='Super',
                    last_name='Admin',
                    password_hash=hash_password('Super12345')
                )
                superadmin.is_verified = True
                superadmin.is_admin = True
                superadmin.is_superadmin = True
                db.session.add(superadmin)
                print("[OK] Superadmin created: superadmin@insightshop.com / Super12345")
                print("  (Login with email: superadmin@insightshop.com or try 'superadmin')")
            else:
                # Update existing superadmin
                superadmin.is_superadmin = True
                superadmin.is_admin = True
                superadmin.is_verified = True
                if not superadmin.password_hash:
                    superadmin.password_hash = hash_password('Super12345')
                print(f"[OK] Superadmin updated: {superadmin.email} / Super12345")
            
            # Create demo users
            demo_users = [
                {
                    'email': 'john.doe@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'password': 'Demo12345',
                    'is_verified': True
                },
                {
                    'email': 'jane.smith@example.com',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'password': 'Demo12345',
                    'is_verified': True
                },
                {
                    'email': 'mike.johnson@example.com',
                    'first_name': 'Mike',
                    'last_name': 'Johnson',
                    'password': 'Demo12345',
                    'is_verified': True
                },
                {
                    'email': 'sarah.williams@example.com',
                    'first_name': 'Sarah',
                    'last_name': 'Williams',
                    'password': 'Demo12345',
                    'is_verified': True
                },
                {
                    'email': 'david.brown@example.com',
                    'first_name': 'David',
                    'last_name': 'Brown',
                    'password': 'Demo12345',
                    'is_verified': True
                }
            ]
            
            created_count = 0
            updated_count = 0
            
            for user_data in demo_users:
                existing_user = User.query.filter_by(email=user_data['email']).first()
                if not existing_user:
                    user = User(
                        email=user_data['email'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        password_hash=hash_password(user_data['password'])
                    )
                    user.is_verified = user_data['is_verified']
                    user.is_admin = False
                    user.is_superadmin = False
                    db.session.add(user)
                    created_count += 1
                    print(f"[OK] Created demo user: {user_data['email']} / {user_data['password']}")
                else:
                    # Update existing user
                    existing_user.is_verified = user_data['is_verified']
                    existing_user.is_admin = False
                    existing_user.is_superadmin = False
                    if not existing_user.password_hash:
                        existing_user.password_hash = hash_password(user_data['password'])
                    updated_count += 1
                    print(f"[OK] Updated demo user: {user_data['email']} / {user_data['password']}")
            
            db.session.commit()
            
            print(f"\n[SUCCESS] User seeding completed!")
            print(f"   - Superadmin: 1 user")
            print(f"   - Demo users: {created_count} created, {updated_count} updated")
            print(f"\nLogin Credentials:")
            print(f"   Superadmin: superadmin@insightshop.com / Super12345")
            print(f"   Demo users: [email] / Demo12345")
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Error seeding users: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    # First, add the superadmin column if it doesn't exist
    from scripts.add_superadmin_column import add_superadmin_column
    print("Step 1: Adding is_superadmin column...")
    add_superadmin_column()
    
    print("\nStep 2: Seeding users...")
    success = seed_users()
    if success:
        print("\n[SUCCESS] All done!")
    else:
        print("\n[ERROR] Seeding failed!")
        sys.exit(1)

