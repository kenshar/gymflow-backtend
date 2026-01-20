from flask import Blueprint, request, jsonify
from app.models import db, Membership, MembershipPlan, Member
from app.auth import require_auth
from datetime import datetime, timezone, timedelta

memberships_bp = Blueprint('memberships', __name__, url_prefix='/api/memberships')

def utc_now():
    """Returning the current UTC time rn (timezone-aware). No cap fr fr."""
    return datetime.now(timezone.utc)

@memberships_bp.route('/plans', methods=['GET'])
@require_auth
def get_plans(current_user):
    """Getting all available membership plans."""
    plans = MembershipPlan.query.all()
    return jsonify({
        'plans': [p.to_dict() for p in plans]
    }), 200

@memberships_bp.route('/plans', methods=['POST'])
@require_auth
def create_plan(current_user):
    """Create a new membership plan."""
    # Only admins can create plans
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()

    if not data or not all(k in data for k in ['name', 'duration_days']):
        return jsonify({'error': 'Missing required fields: name, duration_days'}), 400

    if MembershipPlan.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Plan with this name already exists'}), 409

    plan = MembershipPlan(
        name=data['name'],
        duration_days=data['duration_days'],
        price=data.get('price'),
        description=data.get('description')
    )

    db.session.add(plan)
    db.session.commit()

    return jsonify({
        'message': 'Plan created successfully',
        'plan': plan.to_dict()
    }), 201

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
    """Creating/purchasing a new membership. Supports admin creating for any member."""
    data = request.get_json()

    if not data or 'plan_id' not in data:
        return jsonify({'error': 'Missing required field: plan_id'}), 400

    plan = MembershipPlan.query.get(data['plan_id'])
    if not plan:
        return jsonify({'error': 'Membership plan not found'}), 404

    # Admin can create for any member, regular users create for themselves
    member_id = data.get('member_id')
    if member_id and member_id != current_user.id:
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required to create membership for others'}), 403
    else:
        member_id = current_user.id

    # Verify member exists
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'error': 'Member not found'}), 404

    # Parse start_date if provided, otherwise use now
    if data.get('start_date'):
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
    else:
        start_date = utc_now()

    end_date = start_date + timedelta(days=plan.duration_days)

    membership = Membership(
        member_id=member_id,
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
