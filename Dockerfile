# Multi-stage build for InsightShop

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source
COPY frontend/ ./

# Build React app
RUN npm run build

# Stage 2: Python backend with frontend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create directories for database, instance (Flask DB), and vector DB
RUN mkdir -p /app/data /app/instance /app/vector_db

# Expose port
EXPOSE 5000

# Set environment variables (App Runner can override at runtime)
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
# Required in production by config.py; 32+ chars so app starts in container
ENV FLASK_ENV=production
ENV JWT_SECRET=InsightShop-AppRunner-Default-ChangeInConsole32

# Single worker for faster startup and to avoid 4x init_db/seed races with SQLite
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "120", "app:app"]

