from flask import Blueprint, request, jsonify
from app.models import db, Member, Membership, Attendance, WorkoutLog
from app.auth import require_auth, require_role
from datetime import datetime, timezone

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def utc_now():
    """Returning the current UTC time rn (timezone-aware). No cap fr fr."""
    return datetime.now(timezone.utc)

@admin_bp.route('/dashboard', methods=['GET'])
@require_auth
@require_role('admin')
def dashboard(current_user):
    """Getting admin dashboard statistics rn. Pulling the system tea lowkey bestie fr."""
    total_members = Member.query.count()
    total_active_memberships = Membership.query.filter(
        Membership.end_date > utc_now()
    ).count()
    total_check_ins = Attendance.query.count()
    total_workouts = WorkoutLog.query.count()
    
    return jsonify({
        'stats': {
            'total_members': total_members,
            'total_active_memberships': total_active_memberships,
            'total_check_ins': total_check_ins,
            'total_workouts': total_workouts,
        }
    }), 200

@admin_bp.route('/members', methods=['GET'])
@require_auth
@require_role('admin')
def list_all_members(current_user):
    """Listing all members (admin only). Serving the full roster no cap fr."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Member.query
    
    # Filter by role if provided
    role = request.args.get('role')
    if role:
        query = query.filter_by(role=role)
    
    # Filter by status if provided
    status = request.args.get('status')
    if status == 'active':
        # Get members with active memberships
        active_member_ids = db.session.query(Membership.member_id).filter(
            Membership.end_date > utc_now()
        ).distinct().all()
        active_ids = [m[0] for m in active_member_ids]
        query = query.filter(Member.id.in_(active_ids))
    elif status == 'locked':
        query = query.filter(Member.locked_until > utc_now())
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'members': [m.to_dict() for m in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@admin_bp.route('/members/<int:member_id>/role', methods=['PUT'])
@require_auth
@require_role('admin')
def update_member_role(current_user, member_id):
    """Updating a member's role (admin only). That power move energy fr fr."""
    if member_id == current_user.id:
        return jsonify({'error': 'Cannot change your own role'}), 400
    
    data = request.get_json()
    if not data or 'role' not in data:
        return jsonify({'error': 'role is required'}), 400
    
    valid_roles = ['admin', 'trainer', 'member']
    if data['role'] not in valid_roles:
        return jsonify({'error': f'role must be one of: {", ".join(valid_roles)}'}), 400
    
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    
    member.role = data['role']
    db.session.commit()
    
    return jsonify({
        'message': f'Member role updated to {data["role"]}',
        'member': member.to_dict()
    }), 200

@admin_bp.route('/members/<int:member_id>/unlock', methods=['POST'])
@require_auth
@require_role('admin')
def unlock_member_account(current_user, member_id):
    """Unlocking a locked member account (admin only). Freeing them energy fr fr."""
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    
    if not member.is_account_locked():
        return jsonify({'message': 'Account is not locked'}), 200
    
    member.unlock_account()
    db.session.commit()
    
    return jsonify({
        'message': 'Member account unlocked',
        'member': member.to_dict()
    }), 200

@admin_bp.route('/members/<int:member_id>', methods=['DELETE'])
@require_auth
@require_role('admin')
def delete_member_admin(current_user, member_id):
    """Deleting a member (admin only). The nuclear option energy no cap fr."""
    if member_id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account via admin endpoint'}), 400
    
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    
    db.session.delete(member)
    db.session.commit()
    
    return jsonify({'message': 'Member deleted successfully'}), 200

@admin_bp.route('/memberships', methods=['GET'])
@require_auth
@require_role('admin')
def list_all_memberships(current_user):
    """Listing all memberships (admin only). Serving the membership tea  fr."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Membership.query
    
    # Filter by status if provided
    status = request.args.get('status')
    if status == 'active':
        query = query.filter(Membership.end_date > utc_now())
    elif status == 'expired':
        query = query.filter(Membership.end_date <= utc_now())
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'memberships': [m.to_dict() for m in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@admin_bp.route('/attendance', methods=['GET'])
@require_auth
@require_role('admin')
def list_all_attendance(current_user):
    """Listing all attendance records (admin only). Pulling the check-in tea fr fr."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = Attendance.query.order_by(Attendance.check_in_time.desc())
    
    # Filter by member_id if provided
    member_id = request.args.get('member_id', type=int)
    if member_id:
        query = query.filter_by(member_id=member_id)
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'attendance': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@admin_bp.route('/workouts', methods=['GET'])
@require_auth
@require_role('admin')
def list_all_workouts(current_user):
    """Listing all workouts (admin only). Serving the gains energy no cap fr."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = WorkoutLog.query.order_by(WorkoutLog.workout_date.desc())
    
    # Filter by member_id if provided
    member_id = request.args.get('member_id', type=int)
    if member_id:
        query = query.filter_by(member_id=member_id)
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'workouts': [w.to_dict() for w in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@admin_bp.route('/members/<int:member_id>/stats', methods=['GET'])
@require_auth
@require_role('admin')
def get_member_stats(current_user, member_id):
    """Getting detailed statistics for a member (admin only). Pulling the analytics tea fr."""
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    
    total_check_ins = Attendance.query.filter_by(member_id=member_id).count()
    total_workouts = WorkoutLog.query.filter_by(member_id=member_id).count()
    
    # Calculate total workout duration
    attendances = Attendance.query.filter_by(member_id=member_id).all()
    total_minutes = sum(a.duration_minutes() for a in attendances)
    
    active_membership = None
    for m in member.memberships:
        if m.is_active():
            active_membership = m.to_dict()
            break
    
    return jsonify({
        'member': member.to_dict(),
        'stats': {
            'total_check_ins': total_check_ins,
            'total_workouts': total_workouts,
            'total_minutes': total_minutes,
            'active_membership': active_membership
        }
    }), 200
