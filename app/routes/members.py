from flask import Blueprint, request, jsonify
from app.models import db, Member
from app.auth import require_auth

members_bp = Blueprint('members', __name__, url_prefix='/api/members')

@members_bp.route('', methods=['GET'])
@require_auth
def get_members(current_user):
    """Get all members"""
    members = Member.query.all()
    return jsonify({
        'members': [m.to_dict() for m in members]
    }), 200

@members_bp.route('/<int:member_id>', methods=['GET'])
@require_auth
def get_member(current_user, member_id):
    """Get a specific member"""
    member = Member.query.get(member_id)
    
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    
    return jsonify({
        'member': member.to_dict()
    }), 200

@members_bp.route('/<int:member_id>', methods=['PUT'])
@require_auth
def update_member(current_user, member_id):
    """Update a member's profile"""
    # Users can only update their own profile
    if member_id != current_user.id:
        return jsonify({'error': 'Unauthorized - can only update your own profile'}), 403
    
    data = request.get_json()
    member = Member.query.get(member_id)
    
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    
    # Update allowed fields
    if 'first_name' in data:
        member.first_name = data['first_name']
    if 'last_name' in data:
        member.last_name = data['last_name']
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
    """Delete a member account"""
    # Users can only delete their own account
    if member_id != current_user.id:
        return jsonify({'error': 'Unauthorized - can only delete your own account'}), 403
    
    member = Member.query.get(member_id)
    
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    
    db.session.delete(member)
    db.session.commit()
    
    return jsonify({'message': 'Member deleted successfully'}), 200

@members_bp.route('/<int:member_id>/membership-status', methods=['GET'])
@require_auth
def get_membership_status(current_user, member_id):
    """Get a member's active membership status"""
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
