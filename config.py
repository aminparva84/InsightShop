import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    # Optional: API keys from env (used when admin has not set a key in AI Assistant panel)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
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
    
    # J.P. Morgan Payments API Configuration
    JPMORGAN_ACCESS_TOKEN_URL = os.getenv('JPMORGAN_ACCESS_TOKEN_URL', 'https://id.payments.jpmorgan.com/am/oauth2/alpha/access_token')
    JPMORGAN_CLIENT_ID = os.getenv('JPMORGAN_CLIENT_ID', '92848822-381a-45ef-a20e-208dcf9efbed')
    JPMORGAN_CLIENT_SECRET = os.getenv('JPMORGAN_CLIENT_SECRET', '-0oVQVFeiXDW_0SQtaALMH62WVOiWF0Tw_QQV07qMai-oTs-aME5HSWfO9YQeh4tRabRa92eAdQfH4fdnzspsw')
    JPMORGAN_API_BASE_URL = os.getenv('JPMORGAN_API_BASE_URL', 'https://api-mock.payments.jpmorgan.com/api/v2')
    JPMORGAN_MERCHANT_ID = os.getenv('JPMORGAN_MERCHANT_ID', '998482157630')
    JPMORGAN_SCOPE = os.getenv('JPMORGAN_SCOPE', 'jpm:payments:sandbox')
    
    # S3 Backup Configuration
    S3_BACKUP_BUCKET = os.getenv('S3_BACKUP_BUCKET', 'insightshop-backups')
    INSTANCE_ID = os.getenv('INSTANCE_ID', None)  # For multi-tenant SaaS
    
    # Shipping API Configuration
    # FedEx API Credentials
    FEDEX_API_KEY = os.getenv('FEDEX_API_KEY', '')
    FEDEX_SECRET_KEY = os.getenv('FEDEX_SECRET_KEY', '')
    FEDEX_ACCOUNT_NUMBER = os.getenv('FEDEX_ACCOUNT_NUMBER', '')
    FEDEX_METER_NUMBER = os.getenv('FEDEX_METER_NUMBER', '')
    FEDEX_USE_PRODUCTION = os.getenv('FEDEX_USE_PRODUCTION', 'false').lower() == 'true'
    
    # UPS API Credentials
    UPS_API_KEY = os.getenv('UPS_API_KEY', '')
    UPS_USERNAME = os.getenv('UPS_USERNAME', '')
    UPS_PASSWORD = os.getenv('UPS_PASSWORD', '')
    UPS_ACCOUNT_NUMBER = os.getenv('UPS_ACCOUNT_NUMBER', '')
    UPS_USE_PRODUCTION = os.getenv('UPS_USE_PRODUCTION', 'false').lower() == 'true'
    
    # Shipping Origin Address
    SHIPPING_ORIGIN_STREET = os.getenv('SHIPPING_ORIGIN_STREET', '123 Main St')
    SHIPPING_ORIGIN_CITY = os.getenv('SHIPPING_ORIGIN_CITY', 'New York')
    SHIPPING_ORIGIN_STATE = os.getenv('SHIPPING_ORIGIN_STATE', 'NY')
    SHIPPING_ORIGIN_ZIP = os.getenv('SHIPPING_ORIGIN_ZIP', '10001')
    SHIPPING_ORIGIN_COUNTRY = os.getenv('SHIPPING_ORIGIN_COUNTRY', 'US')

