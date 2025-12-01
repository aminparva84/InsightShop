from models.database import db
from datetime import datetime
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth users
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False, index=True)  # Admin role
    verification_token = db.Column(db.String(255), nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # OAuth fields
    google_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    facebook_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def __init__(self, email, first_name, last_name, password_hash=None, google_id=None, facebook_id=None, profile_picture=None):
        self.email = email.lower().strip()
        self.first_name = first_name
        self.last_name = last_name
        self.password_hash = password_hash
        self.google_id = google_id
        self.facebook_id = facebook_id
        self.profile_picture = profile_picture
        self.is_verified = False if password_hash else True  # OAuth users are auto-verified
    
    def generate_verification_token(self):
        """Generate a unique verification token."""
        self.verification_token = str(uuid.uuid4())
        from datetime import timedelta
        self.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        return self.verification_token
    
    def generate_reset_token(self):
        """Generate a unique password reset token."""
        self.reset_token = str(uuid.uuid4())
        from datetime import timedelta
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    
    def verify_token(self, token):
        """Verify if the token is valid and not expired."""
        if self.verification_token == token:
            if self.verification_token_expires and self.verification_token_expires > datetime.utcnow():
                self.is_verified = True
                self.verification_token = None
                self.verification_token_expires = None
                return True
        return False
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_verified': self.is_verified,
            'is_admin': self.is_admin,
            'profile_picture': self.profile_picture,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

