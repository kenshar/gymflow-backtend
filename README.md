# gymflow-backtend

# GymFlow - Authentication & Login Checklist

## CHECKLIST

### Core Authentication
[x] Password hashing with bcrypt
[x] JWT token generation with expiry
[x] JWT token verification and decoding
[x] UTC-aware datetime handling
[x] Token extraction from Authorization headers
[x] Auth decorator for protecting routes

### API Endpoints
[x] `POST /api/auth/register` - Register new member
    Required: `username`, `email`, `password`
    Optional: `first_name`, `last_name`
    Returns: JWT access token
  
[x] `POST /api/auth/login` - Login with credentials
    Required: `username`, `password`
    Returns: JWT access token
  
[x] `GET /api/auth/me` - Get current user profile
    Requires: Valid JWT token
    Returns: Current member details
  
[x] `POST /api/auth/refresh` - Refresh token
    Requires: Valid JWT token
    Returns: New JWT access token
  
[x] `GET /api/auth/verify` - Verify token validity
    Optional: JWT token (public endpoint)
    Returns: Token validation status

### Database Models
[x] Member model with password hashing
[x] Password hash storage (not plaintext)
[x] Member timestamps (created_at, updated_at)
[x] Relationship support for future features

### Security
[x] Bcrypt password hashing
[x] HS256 JWT algorithm
[x] Token expiry (30 minutes default)
[x] Duplicate username/email prevention
[x] Invalid credential handling

## Not Yet Implemented

[ ] Email verification on registration
[ ] Password reset flow
[ ] OAuth/Social login (Google, GitHub, etc.)
[ ] Multi-factor authentication (MFA)
[ ] Email-based login
[ ] Account lockout after failed attempts
[ ] Logout endpoint (token blacklisting)
[ ] Role-based access control (Admin, Trainer, Member)
[ ] Refresh token rotation
[ ] CORS configuration refinement

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.12
- PostgreSQL
- pipenv

### Installation
```bash
pipenv install