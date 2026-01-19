from flask import Blueprint, request, jsonify
from app.models import db, Member, TokenBlacklist
from app.auth import hash_password, verify_password, create_access_token, require_auth, decode_token, extract_token_from_header, blacklist_token, generate_password_reset_token
from datetime import timedelta, timezone, datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new member"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'Missing required fields: username, email, password'}), 400
    
    if Member.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if Member.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    member = Member(
        username=data['username'],
        email=data['email'],
        password_hash=hash_password(data['password']),
        first_name=data.get('first_name'),
        last_name=data.get('last_name')
    )
    
    db.session.add(member)
    db.session.commit()
    
    access_token = create_access_token(data={"sub": str(member.id)})
    
    return jsonify({
        'message': 'Member registered successfully',
        'member': member.to_dict(),
        'access_token': access_token,
        'token_type': 'bearer'
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with username and password"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['username', 'password']):
        return jsonify({'error': 'Missing username or password'}), 400
    
    member = Member.query.filter_by(username=data['username']).first()
    
    # Check if account is locked
    if member and member.is_account_locked():
        return jsonify({'error': 'Account is locked. Try again later.'}), 403
    
    if not member or not verify_password(data['password'], member.password_hash):
        # Increment failed attempts
        if member:
            member.increment_failed_attempts()
            db.session.commit()
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Reset failed attempts on successful login
    if member.failed_login_attempts > 0:
        member.reset_failed_attempts()
        db.session.commit()
    
    access_token = create_access_token(data={"sub": str(member.id)})
    
    return jsonify({
        'message': 'Login successful',
        'member': member.to_dict(),
        'access_token': access_token,
        'token_type': 'bearer'
    }), 200

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user(current_user):
    """Get current authenticated user profile"""
    return jsonify({
        'member': current_user.to_dict()
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@require_auth
def refresh_token(current_user):
    """Refresh JWT token (extend session)"""
    new_access_token = create_access_token(data={"sub": current_user.id})
    
    return jsonify({
        'message': 'Token refreshed successfully',
        'access_token': new_access_token,
        'token_type': 'bearer'
    }), 200

@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """Verify if token is valid (without requiring full auth)"""
    token = extract_token_from_header()
    
    if not token:
        return jsonify({'valid': False, 'error': 'No token provided'}), 401
    
    # Check if blacklisted
    blacklisted = TokenBlacklist.query.filter_by(token=token).first()
    if blacklisted:
        return jsonify({'valid': False, 'error': 'Token has been revoked'}), 401
    
    payload = decode_token(token)
    
    if not payload:
        return jsonify({'valid': False, 'error': 'Invalid or expired token'}), 401
    
    member_id = payload.get('sub')
    member = Member.query.get(member_id)
    
    if not member:
        return jsonify({'valid': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'valid': True,
        'member_id': member_id,
        'message': 'Token is valid'
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout(current_user):
    """Logout - blacklist the current token"""
    token = extract_token_from_header()
    
    if not token:
        return jsonify({'error': 'No token to blacklist'}), 400
    
    payload = decode_token(token)
    if not payload:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get expiry from token
    exp = payload.get('exp')
    if not exp:
        return jsonify({'error': 'Cannot determine token expiry'}), 400
    
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    
    # Blacklist the token
    blacklist_token(token, current_user.id, expires_at)
    
    return jsonify({
        'message': 'Logged out successfully - token has been revoked'
    }), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset token"""
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    
    member = Member.query.filter_by(email=data['email']).first()
    
    if not member:
        # Don't reveal if email exists for security
        return jsonify({
            'message': 'If email exists, a password reset token will be sent'
        }), 200
    
    # Generate reset token
    reset_token = generate_password_reset_token(member.id)
    member.password_reset_token = reset_token
    member.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    
    db.session.commit()
    
    # In production, send email with reset link
    # For now, return the token (ONLY for testing)
    return jsonify({
        'message': 'Password reset token generated',
        'reset_token': reset_token  # Remove in production!
    }), 200

@auth_bp.route('/reset-password', methods=['PUT'])
def reset_password():
    """Reset password with reset token"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['reset_token', 'new_password']):
        return jsonify({'error': 'reset_token and new_password are required'}), 400
    
    member = Member.query.filter_by(password_reset_token=data['reset_token']).first()
    
    if not member:
        return jsonify({'error': 'Invalid reset token'}), 401
    
    if not member.password_reset_expires or datetime.now(timezone.utc) > member.password_reset_expires:
        return jsonify({'error': 'Reset token has expired'}), 401
    
    # Update password
    member.password_hash = hash_password(data['new_password'])
    member.password_reset_token = None
    member.password_reset_expires = None
    
    db.session.commit()
    
    return jsonify({
        'message': 'Password reset successfully'
    }), 200