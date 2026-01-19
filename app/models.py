from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

def utc_now():
    """Returning the current UTC time rn (timezone-aware). No cap, this is lowkey essential fr fr."""
    return datetime.now(timezone.utc)

class Member(db.Model):
    __tablename__ = "members"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='member')  # admin, trainer, member
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    password_reset_token = db.Column(db.String(255), nullable=True, unique=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    memberships = db.relationship("Membership", back_populates="member", cascade="all, delete-orphan")
    attendances = db.relationship("Attendance", back_populates="member", cascade="all, delete-orphan")
    workout_logs = db.relationship("WorkoutLog", back_populates="member", cascade="all, delete-orphan")
    
    def is_account_locked(self):
        """Checking if this account is locked rn.."""
        if not self.locked_until:
            return False
        return utc_now() < self.locked_until
    
    def unlock_account(self):
        """Unlocking the account cuz it got locked."""
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def increment_failed_attempts(self):
        """Incrementing failed login attempts and locking if needed. Stop trying fr, you're not it."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = utc_now() + timedelta(minutes=30)
    
    def reset_failed_attempts(self):
        """Resetting failed login attempts. No cap, you're coming back strong bestie."""
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def is_active(self):
        """Checking if this member is giving active membership vibes rn. That's the energy we need."""
        if not self.memberships:
            return False
        active_membership = [m for m in self.memberships if m.is_active()]
        return len(active_membership) > 0
    
    def has_role(self, role):
        """Checking if this member's role is hitting different fr. That's the vibe we're seeking."""
        return self.role == role or self.role == 'admin'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active(),
            'is_locked': self.is_account_locked(),
            'created_at': self.created_at.isoformat(),
        }


class MembershipPlan(db.Model):
    __tablename__ = "membership_plans"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    duration_days = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    memberships = db.relationship("Membership", back_populates="plan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'duration_days': self.duration_days,
            'price': self.price,
            'description': self.description,
        }


class Membership(db.Model):
    __tablename__ = "memberships"
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("membership_plans.id"), nullable=False, index=True)
    start_date = db.Column(db.DateTime, nullable=False, default=utc_now)
    end_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    member = db.relationship("Member", back_populates="memberships")
    plan = db.relationship("MembershipPlan", back_populates="memberships")
    
    def is_active(self):
        """Checking if the membership is actively slaying rn. Membership period still going strong."""
        return utc_now() < self.end_date
    
    def is_expired(self):
        """Checking if the membership expired. Time flies when you're having gym seshes fr fr."""
        return utc_now() > self.end_date
    
    def days_remaining(self):
        """Calculating days remaining until expiry. Lowkey the countdown that matters fr."""
        if self.is_expired():
            return 0
        return (self.end_date - utc_now()).days
    
    def to_dict(self):
        return {
            'id': self.id,
            'member_id': self.member_id,
            'plan': self.plan.to_dict(),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_active': self.is_active(),
            'is_expired': self.is_expired(),
            'days_remaining': self.days_remaining(),
        }


class Attendance(db.Model):
    __tablename__ = "attendances"
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False, index=True)
    check_in_time = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)
    check_out_time = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationships
    member = db.relationship("Member", back_populates="attendances")
    
    def duration_minutes(self):
        """Calculating the session duration in minutes. That's your grind time no cap fr."""
        if not self.check_out_time:
            return 0
        return int((self.check_out_time - self.check_in_time).total_seconds() / 60)
    
    def to_dict(self):
        return {
            'id': self.id,
            'member_id': self.member_id,
            'check_in_time': self.check_in_time.isoformat(),
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'duration_minutes': self.duration_minutes(),
            'notes': self.notes,
        }


class WorkoutLog(db.Model):
    __tablename__ = "workout_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False, index=True)
    workout_date = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    member = db.relationship("Member", back_populates="workout_logs")
    exercises = db.relationship("WorkoutExercise", back_populates="workout_log", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'member_id': self.member_id,
            'workout_date': self.workout_date.isoformat(),
            'exercises': [ex.to_dict() for ex in self.exercises],
            'notes': self.notes,
        }


class WorkoutExercise(db.Model):
    __tablename__ = "workout_exercises"
    
    id = db.Column(db.Integer, primary_key=True)
    workout_log_id = db.Column(db.Integer, db.ForeignKey("workout_logs.id"), nullable=False, index=True)
    exercise_name = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationships
    workout_log = db.relationship("WorkoutLog", back_populates="exercises")
    
    def to_dict(self):
        return {
            'id': self.id,
            'exercise_name': self.exercise_name,
            'sets': self.sets,
            'reps': self.reps,
            'weight': self.weight,
            'notes': self.notes,
        }


class TokenBlacklist(db.Model):
    __tablename__ = "token_blacklist"
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(500), unique=True, nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False, index=True)
    blacklisted_at = db.Column(db.DateTime, default=utc_now)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def is_blacklisted(self):
        """Checking if the token is still blacklisted fr. This token got canceled no cap fr."""
        return utc_now() < self.expires_at