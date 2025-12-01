from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models.database import db, init_db
import os

app = Flask(__name__, static_folder='frontend/build', static_url_path='', instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance'))
app.config.from_object(Config)
# Use instance folder for database
db_path = os.path.join(app.instance_path, Config.DB_PATH) if not os.path.isabs(Config.DB_PATH) else Config.DB_PATH
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = Config.SECRET_KEY  # Required for session
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = Config.JWT_EXPIRATION

# Initialize database (only if not in test mode and not already initialized)
if not app.config.get('TESTING') and not hasattr(app, '_db_initialized'):
    init_db(app)
    app._db_initialized = True

# Enable CORS for React frontend
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# JWT Manager
jwt = JWTManager(app)

# Import and register blueprints
from routes.auth import auth_bp
from routes.products import products_bp
from routes.cart import cart_bp
from routes.orders import orders_bp
from routes.payments import payments_bp
from routes.ai_agent import ai_agent_bp
from routes.members import members_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(products_bp, url_prefix='/api/products')
app.register_blueprint(cart_bp, url_prefix='/api/cart')
app.register_blueprint(orders_bp, url_prefix='/api/orders')
app.register_blueprint(payments_bp, url_prefix='/api/payments')
app.register_blueprint(ai_agent_bp, url_prefix='/api/ai')
app.register_blueprint(members_bp, url_prefix='/api/members')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# Serve React static files in production
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)
    else:
        return app.send_static_file('index.html')

# Health check endpoint
@app.route('/api/health')
def health():
    return {'status': 'healthy', 'service': 'InsightShop API'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)

