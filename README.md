# InsightShop - Modern Online Clothing Store with AI Assistant

A full-stack e-commerce application with an AI-powered shopping assistant, built with Flask (Python) backend and React frontend, designed for deployment on AWS App Runner.

## Features

- 🛍️ **1000+ Products**: Comprehensive clothing catalog with men's, women's, and kids' categories
- 🤖 **AI Shopping Assistant**: Powered by AWS Bedrock, helps customers find products through natural conversation
- 🛒 **Shopping Cart**: Full cart functionality with add, remove, and update capabilities
- 💳 **Payment Processing**: Integrated payment system (Stripe-ready)
- 👤 **User Accounts**: Email verification and Google OAuth login
- 📦 **Order Management**: Complete order tracking and history
- 🔍 **Vector Search**: Semantic product search using ChromaDB
- 📱 **Responsive Design**: Modern, mobile-friendly UI

## Tech Stack

### Backend
- Flask (Python)
- SQLite with SQLAlchemy
- ChromaDB for vector search
- AWS Bedrock for AI
- JWT authentication
- Boto3 for AWS services

### Frontend
- React 18
- React Router
- Axios for API calls
- Modern CSS with responsive design

## Documentation

Additional guides and references are in the **[docs/](docs/)** folder, including:

- [QUICK_START.md](docs/QUICK_START.md) – Quick start guide  
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) – Architecture overview  
- [AWS_DEPLOYMENT_GUIDE.md](docs/AWS_DEPLOYMENT_GUIDE.md) – AWS deployment  
- [ENV_SETUP_GUIDE.md](docs/ENV_SETUP_GUIDE.md) – Environment setup  
- [docs/USER_CREDENTIALS.md](docs/USER_CREDENTIALS.md) – Seeded user credentials  

See the full list in the `docs/` directory.

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- AWS Account (for Bedrock)
- Docker (for containerization)

### Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd InsightShop
```

2. **Backend Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env file)
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "from app import app; from models.database import init_db; init_db(app)"
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```

4. **Run Backend**
```bash
# From project root
python app.py
```

### Environment Variables

Create a `.env` file with the following variables:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# JWT
JWT_SECRET=your-secret-key-min-32-characters-long

# Email (WorkMail or SES)
FROM_EMAIL=noreply@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com
WORKMAIL_SMTP_SERVER=smtp.mail.us-east-1.awsapps.com
WORKMAIL_SMTP_PORT=465
WORKMAIL_SMTP_USERNAME=your_username
WORKMAIL_SMTP_PASSWORD=your_password
USE_WORKMAIL=true

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Application
BASE_URL=http://localhost:5000
DEBUG=True
```

### Database Seeding

To seed the database with 1000 products:

```bash
python scripts/seed_products.py
```

## Deployment to AWS App Runner

### 1. Build Docker Image

```bash
docker build -t insightshop:latest .
```

### 2. Push to ECR (Elastic Container Registry)

```bash
# Create ECR repository
aws ecr create-repository --repository-name insightshop

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag insightshop:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/insightshop:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/insightshop:latest
```

### 3. Create App Runner Service

Use AWS Console or CLI to create an App Runner service:

```bash
aws apprunner create-service \
  --service-name insightshop \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/insightshop:latest",
      "ImageConfiguration": {
        "Port": "5000",
        "RuntimeEnvironmentVariables": {
          "FLASK_ENV": "production"
        }
      }
    }
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }'
```

### 4. Configure Environment Variables

Set all environment variables in the App Runner service configuration through the AWS Console.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/google` - Google OAuth login
- `POST /api/auth/verify` - Verify email
- `GET /api/auth/me` - Get current user

### Products
- `GET /api/products` - List products (with filters)
- `GET /api/products/:id` - Get product details
- `GET /api/products/categories` - Get categories
- `GET /api/products/colors` - Get colors

### Cart
- `GET /api/cart` - Get cart items
- `POST /api/cart` - Add to cart
- `PUT /api/cart/:id` - Update cart item
- `DELETE /api/cart/:id` - Remove from cart
- `DELETE /api/cart/clear` - Clear cart

### Orders
- `POST /api/orders` - Create order
- `GET /api/orders` - Get user orders
- `GET /api/orders/:id` - Get order details

### Payments
- `POST /api/payments/create-intent` - Create payment intent
- `POST /api/payments/confirm` - Confirm payment
- `GET /api/payments` - Get payments

### AI Agent
- `POST /api/ai/chat` - Chat with AI assistant
- `POST /api/ai/search` - AI-powered search
- `POST /api/ai/filter` - AI-powered filtering
- `POST /api/ai/compare` - Compare products

### Members
- `GET /api/members/dashboard` - Get dashboard data
- `GET /api/members/orders` - Get orders
- `GET /api/members/payments` - Get payments

## SEO Features

- Meta tags for all pages
- SEO-friendly URLs (slugs)
- Structured product data
- Sitemap generation (can be added)

## Security Features

- JWT authentication
- Password hashing (bcrypt)
- Email verification
- OAuth integration
- CORS configuration
- SQL injection protection (SQLAlchemy)

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.

