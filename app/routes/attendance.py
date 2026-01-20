from flask import Blueprint, request, jsonify
from app.models import db, Attendance, Member
from app.auth import require_auth
from datetime import datetime, timezone

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

def utc_now():
    """Returning the current UTC time rn (timezone-aware). No cap fr fr."""
    return datetime.now(timezone.utc)

@attendance_bp.route('', methods=['GET'])
@require_auth
def get_attendances(current_user):
    """Getting all attendance records (admin) or user's own (member). Pulling that attendance tea fr."""
    # If query param member_id is provided and user is admin, get that member's attendance
    member_id = request.args.get('member_id', type=int)
    
    if member_id:
        # For now, allow users to query their own attendance
        if member_id != current_user.id:
            return jsonify({'error': 'Unauthorized - can only view your own attendance'}), 403
    else:
        member_id = current_user.id
    
    attendances = Attendance.query.filter_by(member_id=member_id).order_by(Attendance.check_in_time.desc()).all()
    
    return jsonify({
        'attendances': [att.to_dict() for att in attendances]
    }), 200

@attendance_bp.route('/<int:attendance_id>', methods=['GET'])
@require_auth
def get_attendance(current_user, attendance_id):
    """Getting a specific attendance record. Lowkey this is the tea you asked for bestie."""
    attendance = Attendance.query.get(attendance_id)
    
    if not attendance:
        return jsonify({'error': 'Attendance record not found'}), 404
    
    # Check if user is viewing their own record
    if attendance.member_id != current_user.id:
        return jsonify({'error': 'Unauthorized - can only view your own attendance'}), 403
    
    return jsonify({
        'attendance': attendance.to_dict()
    }), 200

@attendance_bp.route('/check-in', methods=['POST'])
@require_auth
def check_in(current_user):
    """Checking in to the gym fr fr. Getting those gains energy lowkey."""
    # Check if already checked in
    active_attendance = Attendance.query.filter_by(
        member_id=current_user.id,
        check_out_time=None
    ).first()
    
    if active_attendance:
        return jsonify({'error': 'Already checked in. Check out first'}), 400
    
    attendance = Attendance(
        member_id=current_user.id,
        check_in_time=utc_now()
    )
    
    db.session.add(attendance)
    db.session.commit()
    
    return jsonify({
        'message': 'Check-in successful',
        'attendance': attendance.to_dict()
    }), 201

@attendance_bp.route('/check-out', methods=['POST'])
@require_auth
def check_out(current_user):
    """Checking out from the gym no cap. Them workout gains gonna be calculated fr."""
    data = request.get_json() or {}
    
    # Get the most recent active check-in
    attendance = Attendance.query.filter_by(
        member_id=current_user.id,
        check_out_time=None
    ).order_by(Attendance.check_in_time.desc()).first()
    
    if not attendance:
        return jsonify({'error': 'No active check-in found'}), 404
    
    attendance.check_out_time = utc_now()
    if 'notes' in data:
        attendance.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Check-out successful',
        'attendance': attendance.to_dict()
    }), 200

@attendance_bp.route('/<int:attendance_id>', methods=['DELETE'])
@require_auth
def delete_attendance(current_user, attendance_id):
    """Deleting an attendance record bestie. Wiping it like it never happened fr."""
    attendance = Attendance.query.get(attendance_id)
    
    if not attendance:
        return jsonify({'error': 'Attendance record not found'}), 404
    
    # Check if user owns this record
    if attendance.member_id != current_user.id:
        return jsonify({'error': 'Unauthorized - can only delete your own records'}), 403
    
    db.session.delete(attendance)
    db.session.commit()
    
    return jsonify({'message': 'Attendance record deleted'}), 200

@attendance_bp.route('/stats', methods=['GET'])
@require_auth
def get_attendance_stats(current_user):
    """Getting attendance statistics for the current user. Them stats be looking lowkey fire fr."""
    attendances = Attendance.query.filter_by(member_id=current_user.id).all()

    total_check_ins = len(attendances)
    total_minutes = sum(a.duration_minutes() for a in attendances)
    avg_session = total_minutes // total_check_ins if total_check_ins > 0 else 0

    return jsonify({
        'stats': {
            'total_check_ins': total_check_ins,
            'total_minutes': total_minutes,
            'average_session_minutes': avg_session
        }
    }), 200

@attendance_bp.route('/today', methods=['GET'])
@require_auth
def get_today_attendance(current_user):
    """Get all attendance records for today (for admin dashboard)"""
    # Only admins can view all attendance
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    today = datetime.now(timezone.utc).date()
    attendances = Attendance.query.filter(
        db.func.date(Attendance.check_in_time) == today
    ).all()

    return jsonify({
        'attendance': [a.to_dict() for a in attendances]
    }), 200

@attendance_bp.route('', methods=['POST'])
@require_auth
def admin_check_in(current_user):
    """Admin check-in for a member"""
    # Only admins can check in other members
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()

    if not data or 'member_id' not in data:
        return jsonify({'error': 'member_id is required'}), 400

    member_id = data['member_id']
    member = Member.query.get(member_id)

    if not member:
        return jsonify({'error': 'Member not found'}), 404

    # Check if already checked in today
    today = datetime.now(timezone.utc).date()
    existing = Attendance.query.filter(
        Attendance.member_id == member_id,
        db.func.date(Attendance.check_in_time) == today
    ).first()

    if existing:
        return jsonify({'error': 'Member already checked in today'}), 400

    attendance = Attendance(
        member_id=member_id,
        check_in_time=utc_now(),
        notes=data.get('notes')
    )

    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        'message': 'Check-in successful',
        'attendance': attendance.to_dict()
    }), 201
