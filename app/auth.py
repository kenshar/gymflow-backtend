from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from flask import request, jsonify, current_app
from functools import wraps
import os

# Use pbkdf2_sha256 for password hashing (no length limits, secure)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    """Hash the password using pbkdf2_sha256 for security."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify the plain password against the hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta=None):
    """Generate the JWT access token with expiry."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key')
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Verify and decode the JWT token."""
    try:
        secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key')
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def extract_token_from_header():
    """Extract the JWT token from Authorization header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]

def require_auth(f):
    """Decorator to protect routes by verifying JWT tokens."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extract_token_from_header()
        
        if not token:
            return jsonify({'error': 'Missing authorization token'}), 401
        
        # Check if token is blacklisted
        from app.models import Member, TokenBlacklist
        blacklisted = TokenBlacklist.query.filter_by(token=token).first()
        if blacklisted:
            return jsonify({'error': 'Token has been revoked'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        member_id = payload.get('sub')
        if not member_id:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get current user from database
        current_user = Member.query.get(member_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Pass current_user to the route function
        return f(current_user, *args, **kwargs)
    
    return decorated_function


def require_role(required_role):
    """Decorator to check if the user has the required role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if not current_user.has_role(required_role):
                return jsonify({'error': f'Unauthorized - requires {required_role} role'}), 403
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator


def generate_password_reset_token(member_id: int) -> str:
    """Generate a password reset token."""
    import secrets
    return secrets.token_urlsafe(32)


def blacklist_token(token: str, member_id: int, expires_at):
    """Add the token to blacklist."""
    from app.models import db, TokenBlacklist
    blacklisted = TokenBlacklist(token=token, member_id=member_id, expires_at=expires_at)
    db.session.add(blacklisted)
    db.session.commit()