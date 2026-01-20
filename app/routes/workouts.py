from flask import Blueprint, request, jsonify
from app.models import db, WorkoutLog, WorkoutExercise, Member
from app.auth import require_auth
from datetime import datetime, timezone

workouts_bp = Blueprint('workouts', __name__, url_prefix='/api/workouts')

def utc_now():
    """Return the current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)

@workouts_bp.route('', methods=['GET'])
@require_auth
def get_workouts(current_user):
    """Get all workouts for the current user."""
    workouts = WorkoutLog.query.filter_by(member_id=current_user.id).order_by(WorkoutLog.workout_date.desc()).all()
    return jsonify({
        'workouts': [w.to_dict() for w in workouts]
    }), 200

@workouts_bp.route('/<int:workout_id>', methods=['GET'])
@require_auth
def get_workout(current_user, workout_id):
    """Get a specific workout."""
    workout = WorkoutLog.query.get(workout_id)
    
    if not workout:
        return jsonify({'error': 'Workout not found'}), 404
    
    # Users can only view their own workouts
    if workout.member_id != current_user.id:
        return jsonify({'error': 'Unauthorized - can only view your own workouts'}), 403
    
    return jsonify({
        'workout': workout.to_dict()
    }), 200

@workouts_bp.route('', methods=['POST'])
@require_auth
def create_workout(current_user):
    """Log a new workout session."""
    data = request.get_json()

    if not data or 'exercises' not in data:
        return jsonify({'error': 'Missing required field: exercises'}), 400

    # Validate exercises
    exercises = data.get('exercises', [])
    if not isinstance(exercises, list) or len(exercises) == 0:
        return jsonify({'error': 'exercises must be a non-empty list'}), 400

    for exercise in exercises:
        if not all(k in exercise for k in ['exercise_name', 'sets', 'reps']):
            return jsonify({'error': 'Each exercise must have: exercise_name, sets, reps'}), 400

    # Allow admins to log workouts for any member
    member_id = data.get('member_id')
    if member_id:
        if current_user.role != 'admin':
            return jsonify({'error': 'Only admins can log workouts for other members'}), 403

        # Verify member exists
        member = Member.query.get(member_id)
        if not member:
            return jsonify({'error': 'Member not found'}), 404
    else:
        member_id = current_user.id

    workout_date = datetime.fromisoformat(data.get('workout_date', utc_now().isoformat()))
    duration = data.get('duration')

    workout = WorkoutLog(
        member_id=member_id,
        workout_date=workout_date,
        notes=data.get('notes')
    )

    db.session.add(workout)
    db.session.flush()  # Get the workout ID without committing

    # Add exercises
    for exercise_data in exercises:
        exercise = WorkoutExercise(
            workout_log_id=workout.id,
            exercise_name=exercise_data['exercise_name'],
            sets=exercise_data['sets'],
            reps=exercise_data['reps'],
            weight=exercise_data.get('weight'),
            notes=exercise_data.get('notes')
        )
        db.session.add(exercise)

    db.session.commit()

    return jsonify({
        'message': 'Workout logged successfully',
        'workout': workout.to_dict()
    }), 201

@workouts_bp.route('/<int:workout_id>', methods=['PUT'])
@require_auth
def update_workout(current_user, workout_id):
    """Update a workout."""
    workout = WorkoutLog.query.get(workout_id)
    
    if not workout:
        return jsonify({'error': 'Workout not found'}), 404
    
    # Users can only update their own workouts
    if workout.member_id != current_user.id:
        return jsonify({'error': 'Unauthorized - can only update your own workouts'}), 403
    
    data = request.get_json()
    
    if 'notes' in data:
        workout.notes = data['notes']
    
    if 'workout_date' in data:
        workout.workout_date = datetime.fromisoformat(data['workout_date'])
    
    # Handle exercise updates
    if 'exercises' in data:
        # Delete existing exercises
        WorkoutExercise.query.filter_by(workout_log_id=workout_id).delete()
        
        # Add new exercises
        for exercise_data in data['exercises']:
            if not all(k in exercise_data for k in ['exercise_name', 'sets', 'reps']):
                return jsonify({'error': 'Each exercise must have: exercise_name, sets, reps'}), 400
            
            exercise = WorkoutExercise(
                workout_log_id=workout_id,
                exercise_name=exercise_data['exercise_name'],
                sets=exercise_data['sets'],
                reps=exercise_data['reps'],
                weight=exercise_data.get('weight'),
                notes=exercise_data.get('notes')
            )
            db.session.add(exercise)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Workout updated successfully',
        'workout': workout.to_dict()
    }), 200

@workouts_bp.route('/<int:workout_id>', methods=['DELETE'])
@require_auth
def delete_workout(current_user, workout_id):
    """Delete a workout."""
    workout = WorkoutLog.query.get(workout_id)
    
    if not workout:
        return jsonify({'error': 'Workout not found'}), 404
    
    # Users can only delete their own workouts
    if workout.member_id != current_user.id:
        return jsonify({'error': 'Unauthorized - can only delete your own workouts'}), 403
    
    db.session.delete(workout)
    db.session.commit()
    
    return jsonify({'message': 'Workout deleted successfully'}), 200

@workouts_bp.route('/<int:workout_id>/exercises', methods=['POST'])
@require_auth
def add_exercise(current_user, workout_id):
    """Add an exercise to an existing workout."""
    workout = WorkoutLog.query.get(workout_id)
    
    if not workout:
        return jsonify({'error': 'Workout not found'}), 404
    
    # Users can only add exercises to their own workouts
    if workout.member_id != current_user.id:
        return jsonify({'error': 'Unauthorized - can only modify your own workouts'}), 403
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ['exercise_name', 'sets', 'reps']):
        return jsonify({'error': 'Missing required fields: exercise_name, sets, reps'}), 400
    
    exercise = WorkoutExercise(
        workout_log_id=workout_id,
        exercise_name=data['exercise_name'],
        sets=data['sets'],
        reps=data['reps'],
        weight=data.get('weight'),
        notes=data.get('notes')
    )
    
    db.session.add(exercise)
    db.session.commit()
    
    return jsonify({
        'message': 'Exercise added successfully',
        'exercise': exercise.to_dict()
    }), 201
