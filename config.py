import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    
    # Bedrock Configuration
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    # SQLite Database
    DB_PATH = os.getenv('DB_PATH', 'insightshop.db')
    
    # JWT Configuration
    jwt_secret_env = os.getenv('JWT_SECRET')
    is_production = os.getenv('ENVIRONMENT', '').lower() == 'production' or os.getenv('FLASK_ENV', '').lower() == 'production'
    
    if is_production and (not jwt_secret_env or jwt_secret_env == 'your-secret-key-change-in-production'):
        raise ValueError(
            "CRITICAL SECURITY ERROR: JWT_SECRET must be set in production environment. "
            "Set JWT_SECRET environment variable to a strong random string (min 32 characters)."
        )
    
    JWT_SECRET = jwt_secret_env if jwt_secret_env else 'your-secret-key-change-in-production'
    
    if is_production and len(JWT_SECRET) < 32:
        raise ValueError(
            "CRITICAL SECURITY ERROR: JWT_SECRET must be at least 32 characters long in production. "
            f"Current length: {len(JWT_SECRET)}"
        )
    
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION = 7 * 24 * 60 * 60  # 7 days in seconds
    
    # Email Configuration
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@insightshop.com')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@insightshop.com')
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    
    # WorkMail SMTP Configuration (for email sending)
    WORKMAIL_SMTP_SERVER = os.getenv('WORKMAIL_SMTP_SERVER', 'smtp.mail.us-east-1.awsapps.com')
    WORKMAIL_SMTP_PORT = int(os.getenv('WORKMAIL_SMTP_PORT', '465'))
    WORKMAIL_SMTP_USERNAME = os.getenv('WORKMAIL_SMTP_USERNAME', '')
    WORKMAIL_SMTP_PASSWORD = os.getenv('WORKMAIL_SMTP_PASSWORD', '')
    USE_WORKMAIL = os.getenv('USE_WORKMAIL', 'true').lower() == 'true'
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    
    # Facebook OAuth Configuration (optional)
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '')
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', JWT_SECRET)
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Vector Database Configuration
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', './vector_db')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    
    # Payment Configuration (Stripe or similar)
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')

