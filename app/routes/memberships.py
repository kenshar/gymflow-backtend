from flask import Blueprint, request, jsonify
from app.models import db, Membership, MembershipPlan, Member
from app.auth import require_auth
from datetime import datetime, timezone, timedelta

memberships_bp = Blueprint('memberships', __name__, url_prefix='/api/memberships')

def utc_now():
    """Returning the current UTC time rn (timezone-aware). No cap fr fr."""
    return datetime.now(timezone.utc)

@memberships_bp.route('/plans', methods=['GET'])
def get_plans():
    """Getting all available membership plans. Slay with these options bestie fr fr."""
    plans = MembershipPlan.query.all()
    return jsonify({
        'plans': [p.to_dict() for p in plans]
    }), 200

@memberships_bp.route('', methods=['GET'])
@require_auth
def get_memberships(current_user):
    """Getting all memberships for the current user. Pulling the membership energy lowkey."""
    memberships = Membership.query.filter_by(member_id=current_user.id).all()
    return jsonify({
        'memberships': [m.to_dict() for m in memberships]
    }), 200

@memberships_bp.route('/<int:membership_id>', methods=['GET'])
@require_auth
def get_membership(current_user, membership_id):
    """Getting a specific membership rn. That tea be hitting different fr."""
    membership = Membership.query.get(membership_id)
    
    if not membership:
        return jsonify({'error': 'Membership not found'}), 404
    
    # Users can only view their own membership
    if membership.member_id != current_user.id:
        return jsonify({'error': 'Unauthorized - can only view your own memberships'}), 403
    
    return jsonify({
        'membership': membership.to_dict()
    }), 200

@memberships_bp.route('', methods=['POST'])
@require_auth
def create_membership(current_user):
    """Creating/purchasing a new membership for the current user. That commitment energy no cap fr."""
    data = request.get_json()
    
    if not data or 'plan_id' not in data:
        return jsonify({'error': 'Missing required field: plan_id'}), 400
    
    plan = MembershipPlan.query.get(data['plan_id'])
    if not plan:
        return jsonify({'error': 'Membership plan not found'}), 404
    
    start_date = utc_now()
    end_date = start_date + timedelta(days=plan.duration_days)
    
    membership = Membership(
        member_id=current_user.id,
        plan_id=plan.id,
        start_date=start_date,
        end_date=end_date
    )
    
    db.session.add(membership)
    db.session.commit()
    
    return jsonify({
        'message': 'Membership created successfully',
        'membership': membership.to_dict()
    }), 201

@memberships_bp.route('/<int:membership_id>', methods=['PUT'])
@require_auth
def renew_membership(current_user, membership_id):
    """Renewing/extending an existing membership rn. Resetting that timer bestie fr."""
    membership = Membership.query.get(membership_id)
    
    if not membership:
        return jsonify({'error': 'Membership not found'}), 404
    
    # Users can only renew their own membership
    if membership.member_id != current_user.id:
        return jsonify({'error': 'Unauthorized - can only renew your own memberships'}), 403
    
    data = request.get_json()
    plan_id = data.get('plan_id', membership.plan_id)
    
    plan = MembershipPlan.query.get(plan_id)
    if not plan:
        return jsonify({'error': 'Membership plan not found'}), 404
    
    # Extend from current end date or from today if expired
    if membership.is_expired():
        new_end_date = utc_now() + timedelta(days=plan.duration_days)
    else:
        new_end_date = membership.end_date + timedelta(days=plan.duration_days)
    
    membership.plan_id = plan_id
    membership.end_date = new_end_date
    
    db.session.commit()
    
    return jsonify({
        'message': 'Membership renewed successfully',
        'membership': membership.to_dict()
    }), 200

@memberships_bp.route('/<int:membership_id>', methods=['DELETE'])
@require_auth
def cancel_membership(current_user, membership_id):
    """Canceling a membership fr fr. The breakup energy lowkey. Not it bestie."""
    membership = Membership.query.get(membership_id)
    
    if not membership:
        return jsonify({'error': 'Membership not found'}), 404
    
    # Users can only cancel their own membership
    if membership.member_id != current_user.id:
        return jsonify({'error': 'Unauthorized - can only cancel your own memberships'}), 403
    
    db.session.delete(membership)
    db.session.commit()
    
    return jsonify({'message': 'Membership cancelled successfully'}), 200
