#!/bin/bash

# InsightShop Startup Script

echo "Starting InsightShop..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before continuing."
    exit 1
fi

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

# Initialize database
echo "Initializing database..."
python -c "from app import app; from models.database import init_db; init_db(app)"

# Check if products are seeded
python -c "from app import app; from models.product import Product; app.app_context().push(); print(f'Products in database: {Product.query.count()}')"

echo "Setup complete!"
echo "To start the application:"
echo "  Backend: python app.py"
echo "  Frontend: cd frontend && npm start"

