from flask import Blueprint, request, jsonify
from app.models import db, Member
from app.auth import hash_password, verify_password, create_access_token, require_auth, decode_token, extract_token_from_header
from datetime import timedelta

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
    
    access_token = create_access_token(data={"sub": member.id})
    
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
    
    if not member or not verify_password(data['password'], member.password_hash):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(data={"sub": member.id})
    
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