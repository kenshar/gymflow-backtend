from flask import Blueprint, request, jsonify
from app.models import db, Attendance, Member
from app.auth import require_auth
from datetime import datetime, timezone

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

def utc_now():
    """Return current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)

@attendance_bp.route('', methods=['GET'])
@require_auth
def get_attendances(current_user):
    """Get all attendance records (admin) or user's own (member)"""
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
    """Get a specific attendance record"""
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
    """Check in to the gym"""
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
    """Check out from the gym"""
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
    """Delete an attendance record"""
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
    """Get attendance statistics for current user"""
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
