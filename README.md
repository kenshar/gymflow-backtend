# GymFlow Backend

A comprehensive gym management system backend built with Flask, featuring authentication, member management, attendance tracking, workout logging, and admin controls.

## 🚀 Features

- **Authentication**: JWT-based with token blacklisting and password reset
- **Member Management**: Full CRUD operations with role-based access control
- **Membership Plans**: Purchase, renew, and cancel gym memberships
- **Attendance Tracking**: Check-in/out with duration calculation and statistics
- **Workout Logging**: Log workouts with exercises and tracking
- **Admin Dashboard**: Comprehensive system analytics and member management
- **Security**: Account lockout, password hashing, role-based access

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL or SQLite
- pipenv (or pip)
- Git

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/kenshar/gymflow-backtend.git
cd gymflow-backtend
```

### 2. Install Dependencies
```bash
pipenv install
```

### 3. Create Environment File
Create a `.env` file in the root directory:
```env
FLASK_ENV=development
DATABASE_URL=sqlite:///gymflow.db
SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=30
```

### 4. Activate Virtual Environment
```bash
pipenv shell
```

### 5. Initialize Database
```bash
flask db upgrade
```

### 6. Run the Server
```bash
python run.py
```

The server will start on `http://localhost:5000`

## 📚 API Endpoints

### Authentication Routes (`/api/auth`)
- `POST /register` - Register new member
- `POST /login` - Login with credentials
- `GET /me` - Get current user profile
- `POST /refresh` - Refresh JWT token
- `GET /verify` - Verify token validity
- `POST /logout` - Logout (blacklist token)
- `POST /forgot-password` - Request password reset
- `PUT /reset-password` - Reset password with token

### Member Routes (`/api/members`)
- `GET /` - List all members
- `GET /<id>` - Get member details
- `PUT /<id>` - Update member profile
- `DELETE /<id>` - Delete member account
- `GET /<id>/membership-status` - Check active memberships

### Membership Routes (`/api/memberships`)
- `GET /plans` - List available plans
- `GET /` - Get user's memberships
- `GET /<id>` - Get specific membership
- `POST /` - Purchase new membership
- `PUT /<id>` - Renew/extend membership
- `DELETE /<id>` - Cancel membership

### Attendance Routes (`/api/attendance`)
- `GET /` - Get attendance history
- `GET /<id>` - Get specific attendance record
- `POST /check-in` - Check in to gym
- `POST /check-out` - Check out from gym
- `DELETE /<id>` - Delete attendance record
- `GET /stats` - Get attendance statistics

### Workout Routes (`/api/workouts`)
- `GET /` - Get workout history
- `GET /<id>` - Get specific workout
- `POST /` - Log new workout
- `PUT /<id>` - Update workout
- `DELETE /<id>` - Delete workout
- `POST /<id>/exercises` - Add exercise to workout

### Admin Routes (`/api/admin`)
- `GET /dashboard` - System statistics
- `GET /members` - List all members with filtering
- `PUT /members/<id>/role` - Update member role
- `POST /members/<id>/unlock` - Unlock locked account
- `DELETE /members/<id>` - Delete member (admin)
- `GET /memberships` - List all memberships
- `GET /attendance` - List all attendance records
- `GET /workouts` - List all workouts
- `GET /members/<id>/stats` - Detailed member statistics

## 🔐 Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Token Example
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." http://localhost:5000/api/members
```

## 👥 Roles

Three roles with different access levels:
- **admin** - Full system access, manage all members and data
- **trainer** - Can view member data and manage workouts
- **member** - Can only access their own data

## 🗂️ Project Structure

```
gymflow-backtend/
├── app/
│   ├── __init__.py           # App factory
│   ├── models.py             # Database models
│   ├── auth.py               # Auth utilities
│   └── routes/
│       ├── auth.py           # Authentication endpoints
│       ├── members.py        # Member management
│       ├── memberships.py    # Membership management
│       ├── attendance.py     # Attendance tracking
│       ├── workouts.py       # Workout logging
│       └── admin.py          # Admin endpoints
├── migrations/               # Database migrations
├── tests/                    # Test suite
├── run.py                    # Entry point
├── Pipfile                   # Dependencies
└── README.md                 # This file
```

## 🧪 Running Tests

```bash
pytest
# or with coverage
pytest --cov=app
```

## 🚀 Deployment

### Using Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Using Docker (if available)
```bash
docker build -t gymflow-backend .
docker run -p 5000:5000 gymflow-backend
```

## 📝 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | `production` | Flask environment |
| `DATABASE_URL` | Required | Database connection string |
| `SECRET_KEY` | Required | JWT signing key |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_EXPIRY_MINUTES` | `30` | Token expiry time |

## 🔒 Security Features

✅ JWT token authentication with expiry
✅ Password hashing with Argon2
✅ Account lockout after 5 failed attempts
✅ Token blacklisting for logout
✅ Role-based access control
✅ Password reset with secure tokens
✅ CORS configuration
✅ UTC timezone-aware datetimes

## 📦 Dependencies

- Flask - Web framework
- Flask-SQLAlchemy - ORM
- Flask-CORS - Cross-origin requests
- python-jose - JWT handling
- passlib - Password hashing
- python-dotenv - Environment management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/feature-name`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/feature-name`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👥 Authors

- Kennedy Ng'ang'a (kenshar)
- Branice Simaloi (simaloibranice-boop)
- Allan Ratemo (pyrxallan)

## 📞 Support

For issues and questions, please open an issue on GitHub.
