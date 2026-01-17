from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

def utc_now():
    """Return current UTC time (timezone-aware)"""
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
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    memberships = db.relationship("Membership", back_populates="member", cascade="all, delete-orphan")
    attendances = db.relationship("Attendance", back_populates="member", cascade="all, delete-orphan")
    workout_logs = db.relationship("WorkoutLog", back_populates="member", cascade="all, delete-orphan")
    
    def is_active(self):
        """Check if member has an active membership"""
        if not self.memberships:
            return False
        active_membership = [m for m in self.memberships if m.is_active()]
        return len(active_membership) > 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'is_active': self.is_active(),
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
        """Check if membership is active"""
        return utc_now() < self.end_date
    
    def is_expired(self):
        """Check if membership is expired"""
        return utc_now() > self.end_date
    
    def days_remaining(self):
        """Calculate days remaining until expiry"""
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
        """Calculate session duration in minutes"""
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