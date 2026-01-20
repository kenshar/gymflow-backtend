from flask import Blueprint, request, jsonify, send_file, current_app
from app.models import db, Payment, Receipt, Member, Membership, MembershipPlan
from app.auth import require_auth
from datetime import datetime, timezone, timedelta
import stripe
import os
from io import BytesIO

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

def utc_now():
    """Return the current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def generate_receipt_number():
    """Generate a unique receipt number in format GF-YYYYMMDD-XXXX."""
    today = datetime.now().strftime('%Y%m%d')
    # Count receipts created today to generate sequential number
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = Receipt.query.filter(Receipt.created_at >= today_start).count()
    return f"GF-{today}-{(today_count + 1):04d}"


def generate_receipt_pdf(payment, receipt):
    """Generate a PDF receipt for a payment."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, alignment=TA_CENTER, spaceAfter=30)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, spaceAfter=20)
    normal_style = styles['Normal']
    right_style = ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT)

    elements = []

    # Header
    elements.append(Paragraph("GymFlow", title_style))
    elements.append(Paragraph("Payment Receipt", header_style))
    elements.append(Spacer(1, 20))

    # Receipt details
    receipt_data = [
        ["Receipt Number:", receipt.receipt_number],
        ["Date:", receipt.issued_at.strftime('%B %d, %Y') if receipt.issued_at else "N/A"],
        ["Payment ID:", str(payment.id)],
    ]

    receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
    receipt_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(receipt_table)
    elements.append(Spacer(1, 20))

    # Member information
    elements.append(Paragraph("<b>Member Information</b>", normal_style))
    elements.append(Spacer(1, 10))

    member = payment.member
    member_name = f"{member.first_name or ''} {member.last_name or ''}".strip() or member.username
    member_data = [
        ["Name:", member_name],
        ["Email:", member.email],
    ]

    member_table = Table(member_data, colWidths=[2*inch, 4*inch])
    member_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(member_table)
    elements.append(Spacer(1, 20))

    # Payment details
    elements.append(Paragraph("<b>Payment Details</b>", normal_style))
    elements.append(Spacer(1, 10))

    payment_data = [
        ["Description:", payment.description or "Membership Payment"],
        ["Payment Method:", payment.payment_method.upper()],
        ["Status:", payment.payment_status.upper()],
        ["Amount:", f"{payment.currency} {payment.amount:,.2f}"],
    ]

    payment_table = Table(payment_data, colWidths=[2*inch, 4*inch])
    payment_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (-1, -1), (-1, -1), 14),
    ]))
    elements.append(payment_table)
    elements.append(Spacer(1, 40))

    # Footer
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.gray)
    elements.append(Paragraph("Thank you for your payment!", footer_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("GymFlow - Your Fitness Journey Starts Here", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def create_membership_from_payment(payment, plan_id, start_date=None):
    """Create a membership for a completed payment."""
    plan = MembershipPlan.query.get(plan_id)
    if not plan:
        return None

    if start_date is None:
        start_date = utc_now()
    elif isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)

    end_date = start_date + timedelta(days=plan.duration_days)

    membership = Membership(
        member_id=payment.member_id,
        plan_id=plan_id,
        start_date=start_date,
        end_date=end_date
    )

    db.session.add(membership)
    db.session.flush()

    payment.membership_id = membership.id
    return membership


def create_receipt_for_payment(payment):
    """Create a receipt for a completed payment."""
    receipt_number = generate_receipt_number()
    receipt = Receipt(
        payment_id=payment.id,
        receipt_number=receipt_number,
        issued_at=utc_now()
    )
    db.session.add(receipt)
    db.session.flush()
    return receipt


@payments_bp.route('/cash', methods=['POST'])
@require_auth
def record_cash_payment(current_user):
    """Record a cash payment. Admin only."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required_fields = ['member_id', 'plan_id', 'amount']
    if not all(field in data for field in required_fields):
        return jsonify({'error': f'Missing required fields: {", ".join(required_fields)}'}), 400

    member = Member.query.get(data['member_id'])
    if not member:
        return jsonify({'error': 'Member not found'}), 404

    plan = MembershipPlan.query.get(data['plan_id'])
    if not plan:
        return jsonify({'error': 'Membership plan not found'}), 404

    # Create payment record
    payment = Payment(
        member_id=data['member_id'],
        amount=data['amount'],
        currency=data.get('currency', 'KES'),
        payment_method='cash',
        payment_status='completed',
        description=f"Cash payment for {plan.name}",
        notes=data.get('notes'),
        recorded_by=current_user.id
    )

    db.session.add(payment)
    db.session.flush()

    # Create membership
    start_date = data.get('start_date')
    membership = create_membership_from_payment(payment, data['plan_id'], start_date)

    # Create receipt
    receipt = create_receipt_for_payment(payment)

    db.session.commit()

    return jsonify({
        'message': 'Cash payment recorded successfully',
        'payment': payment.to_dict(),
        'membership': membership.to_dict() if membership else None
    }), 201


@payments_bp.route('/stripe/create-checkout', methods=['POST'])
@require_auth
def create_stripe_checkout(current_user):
    """Create a Stripe checkout session."""
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

    if not stripe.api_key:
        return jsonify({'error': 'Stripe is not configured'}), 500

    data = request.get_json()

    if not data or 'plan_id' not in data:
        return jsonify({'error': 'Missing required field: plan_id'}), 400

    plan = MembershipPlan.query.get(data['plan_id'])
    if not plan:
        return jsonify({'error': 'Membership plan not found'}), 404

    if not plan.price or plan.price <= 0:
        return jsonify({'error': 'Plan has no valid price'}), 400

    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')

    try:
        # Create pending payment record
        payment = Payment(
            member_id=current_user.id,
            amount=plan.price,
            currency='KES',
            payment_method='stripe',
            payment_status='pending',
            description=f"Stripe payment for {plan.name}"
        )
        db.session.add(payment)
        db.session.flush()

        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'kes',
                    'unit_amount': int(plan.price * 100),  # Convert to cents
                    'product_data': {
                        'name': plan.name,
                        'description': plan.description or f'{plan.duration_days} day membership',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{frontend_url}/gymflow-frontend/#/admin/payments?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url}/gymflow-frontend/#/admin/payments?canceled=true",
            customer_email=current_user.email,
            metadata={
                'payment_id': str(payment.id),
                'member_id': str(current_user.id),
                'plan_id': str(plan.id),
            }
        )

        payment.stripe_checkout_session_id = checkout_session.id
        db.session.commit()

        return jsonify({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        }), 200

    except stripe.error.StripeError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@payments_bp.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events."""
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = stripe.Event.construct_from(request.get_json(), stripe.api_key)
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Find the payment by session ID
        payment = Payment.query.filter_by(stripe_checkout_session_id=session['id']).first()

        if payment:
            payment.payment_status = 'completed'
            payment.stripe_payment_id = session.get('payment_intent')

            # Create membership
            plan_id = session['metadata'].get('plan_id')
            if plan_id:
                create_membership_from_payment(payment, int(plan_id))

            # Create receipt
            create_receipt_for_payment(payment)

            db.session.commit()

    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        payment = Payment.query.filter_by(stripe_checkout_session_id=session['id']).first()
        if payment:
            payment.payment_status = 'failed'
            db.session.commit()

    return jsonify({'received': True}), 200


@payments_bp.route('', methods=['GET'])
@require_auth
def get_payments(current_user):
    """Get payments. Admins see all, users see their own."""
    query = Payment.query

    if current_user.role != 'admin':
        query = query.filter_by(member_id=current_user.id)
    else:
        # Filter by member_id if provided
        member_id = request.args.get('member_id')
        if member_id:
            query = query.filter_by(member_id=int(member_id))

    # Filter by status
    status = request.args.get('status')
    if status:
        query = query.filter_by(payment_status=status)

    # Filter by payment method
    method = request.args.get('method')
    if method:
        query = query.filter_by(payment_method=method)

    # Filter by date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        query = query.filter(Payment.created_at >= start)

    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        query = query.filter(Payment.created_at <= end)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    payments = query.order_by(Payment.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'payments': [p.to_dict() for p in payments.items],
        'total': payments.total,
        'pages': payments.pages,
        'current_page': page
    }), 200


@payments_bp.route('/<int:payment_id>', methods=['GET'])
@require_auth
def get_payment(current_user, payment_id):
    """Get a specific payment."""
    payment = Payment.query.get(payment_id)

    if not payment:
        return jsonify({'error': 'Payment not found'}), 404

    # Users can only view their own payments
    if current_user.role != 'admin' and payment.member_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    return jsonify({'payment': payment.to_dict()}), 200


@payments_bp.route('/receipts/<int:receipt_id>/download', methods=['GET'])
@require_auth
def download_receipt(current_user, receipt_id):
    """Download a PDF receipt."""
    receipt = Receipt.query.get(receipt_id)

    if not receipt:
        return jsonify({'error': 'Receipt not found'}), 404

    payment = receipt.payment

    # Users can only download their own receipts
    if current_user.role != 'admin' and payment.member_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Generate PDF
    pdf_buffer = generate_receipt_pdf(payment, receipt)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'receipt_{receipt.receipt_number}.pdf'
    )


@payments_bp.route('/admin/revenue', methods=['GET'])
@require_auth
def get_revenue_stats(current_user):
    """Get revenue statistics. Admin only."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    now = utc_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Helper function to calculate revenue
    def get_revenue(start_date=None, end_date=None, method=None):
        query = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.payment_status == 'completed'
        )
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
        if method:
            query = query.filter(Payment.payment_method == method)
        result = query.scalar()
        return float(result) if result else 0.0

    def get_payment_count(start_date=None, end_date=None, method=None):
        query = Payment.query.filter(Payment.payment_status == 'completed')
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
        if method:
            query = query.filter(Payment.payment_method == method)
        return query.count()

    return jsonify({
        'revenue': {
            'today': get_revenue(start_date=today_start),
            'week': get_revenue(start_date=week_start),
            'month': get_revenue(start_date=month_start),
            'all_time': get_revenue(),
        },
        'revenue_by_method': {
            'cash': get_revenue(method='cash'),
            'stripe': get_revenue(method='stripe'),
            'mpesa': get_revenue(method='mpesa'),
        },
        'payment_counts': {
            'today': get_payment_count(start_date=today_start),
            'week': get_payment_count(start_date=week_start),
            'month': get_payment_count(start_date=month_start),
            'all_time': get_payment_count(),
        },
        'payment_counts_by_method': {
            'cash': get_payment_count(method='cash'),
            'stripe': get_payment_count(method='stripe'),
            'mpesa': get_payment_count(method='mpesa'),
        }
    }), 200
