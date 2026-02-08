from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.database import db
from models.user import User
from utils.email import send_activation_email, send_email
from config import Config
import bcrypt
import requests
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def verify_jwt_token(token):
    """Verify JWT token and return payload."""
    try:
        import jwt
        from config import Config
        
        # Decode token using PyJWT with the secret key
        decoded = jwt.decode(
            token,
            Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )
        return decoded
    except Exception:
        return None

def get_current_user_optional():
    """Get current user if authenticated, otherwise return None."""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            token = auth_header[7:]
            payload = verify_jwt_token(token)
            if payload:
                user_id = payload.get('sub') or payload.get('user_id')
                if user_id:
                    user = User.query.get(user_id)
                    return user
        except Exception:
            pass
    return None

def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def require_auth(f):
    """Decorator to require authentication."""
    @jwt_required()
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        if user_id is not None and not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except (TypeError, ValueError):
                user_id = None
        user = User.query.get(user_id) if user_id is not None else None
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        if not user.is_verified:
            return jsonify({'error': 'Email not verified'}), 403
        
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        if not email or not password or not first_name or not last_name:
            return jsonify({'error': 'All fields are required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        password_hash = hash_password(password)
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash
        )
        
        # Generate verification token
        verification_token = user.generate_verification_token()
        
        db.session.add(user)
        db.session.commit()
        
        # Send activation email
        send_activation_email(email, first_name, verification_token)
        
        return jsonify({
            'message': 'Registration successful. Please check your email to activate your account.',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify', methods=['POST'])
def verify_email():
    """Verify user email with token."""
    try:
        data = request.get_json()
        token = data.get('token', '')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        # Find user with this token
        user = User.query.filter_by(verification_token=token).first()
        if not user:
            return jsonify({'error': 'Invalid token'}), 400
        
        # Verify token
        if user.verify_token(token):
            db.session.commit()
            return jsonify({
                'message': 'Email verified successfully',
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Token expired or invalid'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email and password."""
    try:
        data = request.get_json()
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check password
        if not user.password_hash or not verify_password(password, user.password_hash):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if verified
        if not user.is_verified:
            return jsonify({'error': 'Please verify your email before logging in'}), 403
        
        # Generate token
        token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/google', methods=['POST'])
def google_login():
    """Handle Google OAuth login/registration."""
    try:
        data = request.get_json()
        
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        # Handle credential-based login (One Tap)
        if data.get('credential'):
            credential = data['credential']
            try:
                import base64
                parts = credential.split('.')
                if len(parts) < 2:
                    return jsonify({'error': 'Invalid JWT format'}), 400
                
                payload = parts[1]
                padding = len(payload) % 4
                if padding:
                    payload += '=' * (4 - padding)
                
                decoded_bytes = base64.urlsafe_b64decode(payload)
                import json
                decoded = json.loads(decoded_bytes)
                
                email = decoded.get('email', '').lower().strip()
                first_name = decoded.get('given_name', '')
                last_name = decoded.get('family_name', '')
                picture = decoded.get('picture', '')
                google_id = decoded.get('sub', '')
                
                if not email:
                    return jsonify({'error': 'Google credential missing email'}), 400
                
            except Exception as e:
                return jsonify({'error': f'Invalid Google credential: {str(e)}'}), 400
        
        # Handle OAuth token-based login
        elif data.get('accessToken'):
            access_token = data['accessToken']
            email = data.get('email', '').lower().strip()
            first_name = data.get('firstName', '')
            last_name = data.get('lastName', '')
            picture = data.get('picture', '')
            google_id = data.get('googleId', '')
            
            # Verify token with Google
            try:
                verify_response = requests.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=5
                )
                
                if verify_response.status_code != 200:
                    return jsonify({'error': 'Invalid Google token'}), 401
                
                user_info = verify_response.json()
                email = user_info.get('email', email).lower().strip()
                first_name = user_info.get('given_name', first_name)
                last_name = user_info.get('family_name', last_name)
                picture = user_info.get('picture', picture)
                google_id = user_info.get('id', google_id)
                
            except Exception as e:
                return jsonify({'error': f'Failed to verify Google account: {str(e)}'}), 400
        else:
            return jsonify({'error': 'Missing Google credential or access token'}), 400
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                google_id=google_id,
                profile_picture=picture
            )
            db.session.add(user)
        else:
            # Update existing user with Google info
            if google_id:
                user.google_id = google_id
            if picture:
                user.profile_picture = picture
            user.is_verified = True  # Google users are auto-verified
        
        db.session.commit()
        
        # Generate token
        token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current authenticated user."""
    return jsonify({'user': request.current_user.to_dict()}), 200

