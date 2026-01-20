from flask import Blueprint, request, jsonify
from app.models import db, Member
from app.auth import require_auth, hash_password

members_bp = Blueprint('members', __name__, url_prefix='/api/members')

@members_bp.route('', methods=['POST'])
@require_auth
def create_member(current_user):
    """Create a new member (admin use)."""
    # Only admins can create members
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

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
        last_name=data.get('last_name'),
        phone=data.get('phone'),
        role='member'
    )

    db.session.add(member)
    db.session.commit()

    return jsonify({
        'message': 'Member created successfully',
        'member': member.to_dict()
    }), 201

@members_bp.route('', methods=['GET'])
@require_auth
def get_members(current_user):
    """Get all members for admin dashboard."""
    # Only admins can view all members
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    members = Member.query.all()
    return jsonify({
        'members': [m.to_dict() for m in members]
    }), 200

@members_bp.route('/<int:member_id>', methods=['GET'])
@require_auth
def get_member(current_user, member_id):
    """Get a specific member by ID."""
    member = Member.query.get(member_id)

    if not member:
        return jsonify({'error': 'Member not found'}), 404

    # Users can view their own profile, admins can view any profile
    if current_user.id != member_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    return jsonify({
        'member': member.to_dict()
    }), 200

@members_bp.route('/<int:member_id>', methods=['PUT'])
@require_auth
def update_member(current_user, member_id):
    """Update a member's profile."""
    data = request.get_json()
    member = Member.query.get(member_id)

    if not member:
        return jsonify({'error': 'Member not found'}), 404

    # Users can update their own profile, admins can update any profile
    if current_user.id != member_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    # Update allowed fields
    if 'first_name' in data:
        member.first_name = data['first_name']
    if 'last_name' in data:
        member.last_name = data['last_name']
    if 'email' in data:
        member.email = data['email']
    if 'phone' in data:
        member.phone = data['phone']

    db.session.commit()

    return jsonify({
        'message': 'Member updated successfully',
        'member': member.to_dict()
    }), 200

@members_bp.route('/<int:member_id>', methods=['DELETE'])
@require_auth
def delete_member(current_user, member_id):
    """Delete a member."""
    # Only admins can delete members
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    member = Member.query.get(member_id)

    if not member:
        return jsonify({'error': 'Member not found'}), 404

    db.session.delete(member)
    db.session.commit()

    return jsonify({'message': 'Member deleted successfully'}), 200

@members_bp.route('/<int:member_id>/membership-status', methods=['GET'])
@require_auth
def get_membership_status(current_user, member_id):
    """Get a member's active membership status."""
    member = Member.query.get(member_id)
    
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    
    active_memberships = [m for m in member.memberships if m.is_active()]
    
    return jsonify({
        'member_id': member_id,
        'is_active': len(active_memberships) > 0,
        'active_memberships': [m.to_dict() for m in active_memberships],
        'total_memberships': len(member.memberships)
    }), 200
