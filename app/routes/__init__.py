from app.routes.auth import auth_bp
from app.routes.members import members_bp
from app.routes.memberships import memberships_bp
from app.routes.attendance import attendance_bp
from app.routes.workouts import workouts_bp

__all__ = ['auth_bp', 'members_bp', 'memberships_bp', 'attendance_bp', 'workouts_bp']
