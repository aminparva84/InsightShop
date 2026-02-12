# Load .env first so AWS_SECRETS_INSIGHTSHOP is set, then fetch secrets from AWS
import os
from dotenv import load_dotenv
load_dotenv()
from utils.secrets_loader import load_into_env
load_into_env()

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models.database import db, init_db

# SPA build: index.html at frontend/build, assets at frontend/build/static (CRA)
# Use static_url_path='/static' so Flask's static route only matches /static/*, not /* (avoids 404 on reload for /products, /cart, etc.)
_build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'build')
app = Flask(__name__, static_folder=os.path.join(_build_dir, 'static'), static_url_path='/static', instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance'))
# Allow API routes to match with or without trailing slash (avoids 404 when request has trailing slash)
app.url_map.strict_slashes = False
app.config.from_object(Config)
# Use instance folder for database
db_path = os.path.join(app.instance_path, Config.DB_PATH) if not os.path.isabs(Config.DB_PATH) else Config.DB_PATH
# Ensure instance (and any parent) directory exists so SQLite can create the DB file
_db_dir = os.path.dirname(db_path)
if _db_dir and not os.path.exists(_db_dir):
    os.makedirs(_db_dir, exist_ok=True)
# Use forward slashes in URI so SQLite works on Windows (backslashes can break the URI)
_db_uri_path = db_path.replace('\\', '/')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{_db_uri_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Log resolved DB path so you can verify if connection is severed
print(f"[DB] Path: {os.path.abspath(db_path)} (from DB_PATH={Config.DB_PATH!r})")
app.config['SECRET_KEY'] = Config.SECRET_KEY  # Required for session
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = Config.JWT_EXPIRATION

# Session configuration for guest cart
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cross-site cookies
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Initialize database (only if not in test mode and not already initialized)
if not app.config.get('TESTING') and not hasattr(app, '_db_initialized'):
    try:
        init_db(app)
        app._db_initialized = True
    except Exception as e:
        print(f"[DB] WARNING: Database initialization failed: {e}")
        print("[DB] App will start; /api/health may report degraded until DB is fixed.")
        app._db_initialized = False

# Enable CORS for React frontend with credentials support for sessions
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True  # Allow cookies/sessions
    }
})

# JWT Manager
jwt = JWTManager(app)

@jwt.invalid_token_loader
def invalid_token_callback(reason):
    from flask import jsonify
    return jsonify({'error': 'Invalid or malformed token', 'message': 'Please log in again'}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    from flask import jsonify
    return jsonify({'error': 'Token has expired', 'message': 'Please log in again'}), 401

@jwt.unauthorized_loader
def unauthorized_callback(reason):
    from flask import jsonify
    return jsonify({'error': 'Authorization required', 'message': reason or 'Please log in'}), 401

# Import and register blueprints
from routes.auth import auth_bp
from routes.products import products_bp
from routes.cart import cart_bp
from routes.orders import orders_bp
from routes.payments import payments_bp
from routes.ai_agent import ai_agent_bp
from routes.members import members_bp
from routes.admin import admin_bp
from routes.admin_sales import admin_sales_bp
from routes.sales import sales_bp
from routes.sale_automation import sale_automation_bp
from routes.reviews import reviews_bp
from routes.shipping import shipping_bp
from routes.returns import returns_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(products_bp, url_prefix='/api/products')
app.register_blueprint(cart_bp, url_prefix='/api/cart')
app.register_blueprint(orders_bp, url_prefix='/api/orders')
app.register_blueprint(payments_bp, url_prefix='/api/payments')
app.register_blueprint(ai_agent_bp, url_prefix='/api/ai')
app.register_blueprint(members_bp, url_prefix='/api/members')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(admin_sales_bp, url_prefix='/api/admin')
app.register_blueprint(sales_bp, url_prefix='/api/sales')
app.register_blueprint(sale_automation_bp, url_prefix='/api/sale-automation')
app.register_blueprint(reviews_bp, url_prefix='/api')
app.register_blueprint(shipping_bp, url_prefix='/api/shipping')
app.register_blueprint(returns_bp, url_prefix='/api/returns')

# LLMO: serve robots.txt and ai-info.txt for AI crawlers (before SPA catch-all)
_llmo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'llmo')

@app.route('/robots.txt')
def serve_robots():
    """Serve robots.txt; allow Google-Extended and other crawlers."""
    from flask import send_from_directory
    if os.path.exists(_llmo_dir):
        return send_from_directory(_llmo_dir, 'robots.txt', mimetype='text/plain')
    from flask import Response
    return Response('User-agent: *\nAllow: /\n', mimetype='text/plain')

@app.route('/ai-info.txt')
def serve_ai_info():
    """Serve machine-readable summary for AI crawlers (LLMO)."""
    from flask import send_from_directory
    if os.path.exists(_llmo_dir):
        return send_from_directory(_llmo_dir, 'ai-info.txt', mimetype='text/plain')
    from flask import Response
    return Response('# InsightShop\nSee JSON-LD on homepage.\n', mimetype='text/plain')

# Serve React SPA: any non-API path returns index.html so client-side router can handle /products, /cart, etc. (fixes reload 404)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    from flask import send_from_directory, abort, jsonify
    # Don't serve index.html for API paths (let API routes or 404 handle them)
    if path.startswith('api/'):
        abort(404)
    # Check if frontend build exists (index.html lives in build dir, assets in build/static)
    index_path = os.path.join(_build_dir, 'index.html')
    if not os.path.exists(_build_dir) or not os.path.exists(index_path):
        return jsonify({
            'message': 'Frontend not built. Please run "npm run build" in the frontend directory, or start the React dev server with "npm start" on port 3000.',
            'api_endpoints': {
                'health': '/api/health',
                'products': '/api/products',
                'auth': '/api/auth'
            },
            'development_mode': 'For development, run the React dev server separately: cd frontend && npm start'
        }), 200
    # Serve root-level build files (e.g. logo.png, favicon.png from public/) so they load when backend serves the SPA
    _public_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'public')
    if path:
        safe_path = os.path.normpath(path).replace('\\', '/').lstrip('/')
        if safe_path and '..' not in safe_path:
            file_path = os.path.join(_build_dir, *safe_path.split('/'))
            if os.path.isfile(file_path):
                return send_from_directory(_build_dir, safe_path)
            # Fallback: serve from frontend/public (e.g. logo.png) when not yet in build
            public_file = os.path.join(_public_dir, *safe_path.split('/'))
            if os.path.isfile(public_file):
                return send_from_directory(_public_dir, safe_path)
    # SPA fallback: serve index.html so React Router can handle the path
    return send_from_directory(_build_dir, 'index.html')

# Serve product images from static/images directory
@app.route('/api/images/<filename>')
def serve_image(filename):
    """Serve product images from static/images directory."""
    from flask import send_from_directory
    static_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images')
    if os.path.exists(static_images_dir) and os.path.exists(os.path.join(static_images_dir, filename)):
        return send_from_directory(static_images_dir, filename)
    else:
        from flask import abort
        abort(404)

# Serve background images from generated_images directory
@app.route('/api/images/generated/<filename>')
def serve_generated_image(filename):
    """Serve images from generated_images directory."""
    from flask import send_from_directory
    generated_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated_images')
    if os.path.exists(generated_images_dir) and os.path.exists(os.path.join(generated_images_dir, filename)):
        return send_from_directory(generated_images_dir, filename)
    else:
        from flask import abort
        abort(404)

# Health check endpoint (SQL DB + vector DB connectivity)
@app.route('/api/health')
def health():
    payload = {'status': 'healthy', 'service': 'InsightShop API'}
    sql_ok = False
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        payload['db'] = 'connected'
        sql_ok = True
    except Exception as e:
        payload['status'] = 'degraded'
        payload['db'] = 'error'
        payload['db_error'] = str(e)

    try:
        from utils.vector_db import is_vector_db_available
        payload['vector_db'] = 'connected' if is_vector_db_available() else 'unavailable'
    except Exception as e:
        payload['vector_db'] = 'error'
        payload['vector_db_error'] = str(e)

    if not sql_ok:
        return payload, 503
    return payload, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)

