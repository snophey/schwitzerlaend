"""History-related API endpoints for tracking workout completion progress."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from models import UpdateSetProgressRequest, CompleteSetRequest
from database import get_database
from bson import ObjectId
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/health")
async def health_check():
    """Health check endpoint to verify history router is loaded."""
    return {"status": "ok", "router": "history"}


def create_initial_history_entry(user_id: str, workout_id: str, db):
    """Create the initial history entry for a user's workout."""
    logger.info(f"Creating initial history entry for user {user_id}, workout {workout_id}")
    
    workouts_collection = db["workouts"]
    workout_doc = workouts_collection.find_one({'_id': workout_id})
    
    if not workout_doc:
        raise HTTPException(status_code=404, detail=f"Workout '{workout_id}' not found")
    
    workout_plan = workout_doc.get('workout_plan', [])
    if not workout_plan:
        raise HTTPException(status_code=400, detail="Workout plan is empty")
    
    # Start with the first day
    first_day = workout_plan[0]
    day_name = first_day.get('day')
    set_ids = first_day.get('exercises_ids', [])
    
    # Get set details to create progress tracking
    sets_collection = db["sets"]
    sets_progress = []
    
    for set_id in set_ids:
        set_doc = sets_collection.find_one({'_id': set_id})
        if set_doc:
            set_progress = {
                'set_id': set_id,
                'target_reps': set_doc.get('reps'),
                'completed_reps': 0,
                'target_weight': set_doc.get('weight'),
                'target_duration_sec': set_doc.get('duration_sec'),
                'is_complete': False,
                'completed_at': None
            }
            sets_progress.append(set_progress)
    
    history_id = str(ObjectId())
    now = datetime.utcnow().isoformat() + 'Z'
    
    history_doc = {
        '_id': history_id,
        'user_id': user_id,
        'workout_id': workout_id,
        'current_day_index': 0,
        'day_name': day_name,
        'sets_progress': sets_progress,
        'created_at': now,
        'updated_at': now
    }
    
    history_collection = db["history"]
    history_collection.insert_one(history_doc)
    
    logger.info(f"Created history entry {history_id} for {day_name} with {len(sets_progress)} sets")
    return history_doc


@router.get("/{user_id}/latest", response_model=Dict[str, Any])
async def get_latest_history(user_id: str):
    """
    Get the latest workout history for a user.
    
    - **user_id**: ID of the user
    
    Returns the current day's workout progress including all sets and their completion status.
    If no history exists, creates an initial history entry from the user's first workout.
    """
    logger.info(f"GET /history/{user_id}/latest endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot get history")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        history_collection = db["history"]
        
        # Find the most recent history entry for this user
        logger.info(f"Searching for history for user {user_id}")
        history_doc = history_collection.find_one(
            {'user_id': user_id},
            sort=[('updated_at', -1)]
        )
        
        # If no history exists, create initial entry
        if not history_doc:
            logger.info(f"No history found for user {user_id}, creating initial entry")
            
            # Get user's first workout
            users_collection = db["users"]
            user_doc = users_collection.find_one({'_id': user_id})
            
            if not user_doc:
                logger.error(f"User '{user_id}' not found in database")
                raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
            
            logger.info(f"Found user {user_id}: {user_doc}")
            
            workout_ids = user_doc.get('associated_workout_ids', [])
            if not workout_ids:
                logger.error(f"User '{user_id}' has no associated workouts")
                raise HTTPException(status_code=404, detail=f"No workouts found for user '{user_id}'")
            
            logger.info(f"User has workout IDs: {workout_ids}")
            
            # Create initial history from first workout
            logger.info(f"Creating initial history for user {user_id} with workout {workout_ids[0]}")
            history_doc = create_initial_history_entry(user_id, workout_ids[0], db)
            logger.info(f"Successfully created history: {history_doc.get('_id')}")
        
        # Enrich the response with set and exercise details
        sets_collection = db["sets"]
        exercises_collection = db["exercises"]
        
        enriched_sets = []
        for set_progress in history_doc.get('sets_progress', []):
            set_id = set_progress.get('set_id')
            set_doc = sets_collection.find_one({'_id': set_id})
            
            if set_doc:
                exercise_id = set_doc.get('exercise_id') or set_doc.get('excersise_id')
                exercise_doc = exercises_collection.find_one({'_id': exercise_id}) if exercise_id else None
                
                enriched_set = {
                    **set_progress,
                    'set_name': set_doc.get('name'),
                    'exercise_id': exercise_id,
                    'exercise_name': exercise_doc.get('name') if exercise_doc else None,
                    'exercise_details': {
                        'category': exercise_doc.get('category'),
                        'equipment': exercise_doc.get('equipment'),
                        'primaryMuscles': exercise_doc.get('primaryMuscles'),
                        'instructions': exercise_doc.get('instructions')
                    } if exercise_doc else None
                }
                enriched_sets.append(enriched_set)
        
        # Calculate progress statistics
        total_sets = len(enriched_sets)
        completed_sets = sum(1 for s in enriched_sets if s.get('is_complete'))
        
        response = {
            'history_id': history_doc.get('_id'),
            'user_id': history_doc.get('user_id'),
            'workout_id': history_doc.get('workout_id'),
            'current_day_index': history_doc.get('current_day_index'),
            'day_name': history_doc.get('day_name'),
            'sets': enriched_sets,
            'progress': {
                'total_sets': total_sets,
                'completed_sets': completed_sets,
                'remaining_sets': total_sets - completed_sets,
                'completion_percentage': round((completed_sets / total_sets * 100) if total_sets > 0 else 0, 1)
            },
            'created_at': history_doc.get('created_at'),
            'updated_at': history_doc.get('updated_at')
        }
        
        logger.info(f"Retrieved history for user {user_id}: {day_name} - {completed_sets}/{total_sets} sets complete")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving history for user '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.post("/{user_id}/update", response_model=Dict[str, Any])
async def update_set_progress(user_id: str, request: UpdateSetProgressRequest):
    """
    Update progress on a specific set (e.g., number of reps completed).
    
    - **user_id**: ID of the user
    - **set_id**: ID of the set to update
    - **completed_reps**: Number of reps completed (optional)
    - **completed_duration_sec**: Duration completed in seconds (optional)
    
    Returns the updated history entry.
    """
    logger.info(f"POST /history/{user_id}/update endpoint called for set {request.set_id}")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot update history")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        history_collection = db["history"]
        
        # Get the latest history entry
        history_doc = history_collection.find_one(
            {'user_id': user_id},
            sort=[('updated_at', -1)]
        )
        
        if not history_doc:
            raise HTTPException(status_code=404, detail=f"No history found for user '{user_id}'")
        
        # Find and update the specific set in sets_progress
        sets_progress = history_doc.get('sets_progress', [])
        set_found = False
        
        for set_progress in sets_progress:
            if set_progress.get('set_id') == request.set_id:
                set_found = True
                if request.completed_reps is not None:
                    set_progress['completed_reps'] = request.completed_reps
                if request.completed_duration_sec is not None:
                    set_progress['completed_duration_sec'] = request.completed_duration_sec
                break
        
        if not set_found:
            raise HTTPException(status_code=404, detail=f"Set '{request.set_id}' not found in current history")
        
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Update the document
        result = history_collection.update_one(
            {'_id': history_doc['_id']},
            {
                '$set': {
                    'sets_progress': sets_progress,
                    'updated_at': now
                }
            }
        )
        
        if result.modified_count == 0:
            logger.warning(f"Update did not modify document for user {user_id}")
        
        logger.info(f"Updated set progress for set {request.set_id} in user {user_id}'s history")
        
        return {
            'message': 'Set progress updated successfully',
            'history_id': history_doc['_id'],
            'set_id': request.set_id,
            'updated_at': now
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating history for user '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update history: {str(e)}")


@router.post("/{user_id}/complete", response_model=Dict[str, Any])
async def complete_set(user_id: str, request: CompleteSetRequest):
    """
    Mark a set as complete. When all sets in a day are complete, automatically
    creates a new history entry for the next day in the workout plan.
    
    - **user_id**: ID of the user
    - **set_id**: ID of the set to mark as complete
    
    Returns the updated history entry, and indicates if a new day was started.
    """
    logger.info(f"POST /history/{user_id}/complete endpoint called for set {request.set_id}")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot complete set")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        history_collection = db["history"]
        
        # Get the latest history entry
        history_doc = history_collection.find_one(
            {'user_id': user_id},
            sort=[('updated_at', -1)]
        )
        
        if not history_doc:
            raise HTTPException(status_code=404, detail=f"No history found for user '{user_id}'")
        
        # Find and mark the specific set as complete
        sets_progress = history_doc.get('sets_progress', [])
        set_found = False
        
        for set_progress in sets_progress:
            if set_progress.get('set_id') == request.set_id:
                set_found = True
                set_progress['is_complete'] = True
                set_progress['completed_at'] = datetime.utcnow().isoformat() + 'Z'
                break
        
        if not set_found:
            raise HTTPException(status_code=404, detail=f"Set '{request.set_id}' not found in current history")
        
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Update the current document
        history_collection.update_one(
            {'_id': history_doc['_id']},
            {
                '$set': {
                    'sets_progress': sets_progress,
                    'updated_at': now
                }
            }
        )
        
        # Check if all sets are complete
        all_complete = all(s.get('is_complete', False) for s in sets_progress)
        new_day_started = False
        new_day_name = None
        
        if all_complete:
            logger.info(f"All sets complete for user {user_id}, moving to next day")
            
            # Get the workout to find the next day
            workouts_collection = db["workouts"]
            workout_id = history_doc.get('workout_id')
            workout_doc = workouts_collection.find_one({'_id': workout_id})
            
            if workout_doc:
                workout_plan = workout_doc.get('workout_plan', [])
                current_day_index = history_doc.get('current_day_index', 0)
                next_day_index = current_day_index + 1
                
                # Check if there's a next day in the plan
                if next_day_index < len(workout_plan):
                    next_day = workout_plan[next_day_index]
                    day_name = next_day.get('day')
                    set_ids = next_day.get('exercises_ids', [])
                    
                    # Create progress tracking for the new day
                    sets_collection = db["sets"]
                    new_sets_progress = []
                    
                    for set_id in set_ids:
                        set_doc = sets_collection.find_one({'_id': set_id})
                        if set_doc:
                            set_progress = {
                                'set_id': set_id,
                                'target_reps': set_doc.get('reps'),
                                'completed_reps': 0,
                                'target_weight': set_doc.get('weight'),
                                'target_duration_sec': set_doc.get('duration_sec'),
                                'is_complete': False,
                                'completed_at': None
                            }
                            new_sets_progress.append(set_progress)
                    
                    # Create new history entry for the next day
                    new_history_id = str(ObjectId())
                    new_history_doc = {
                        '_id': new_history_id,
                        'user_id': user_id,
                        'workout_id': workout_id,
                        'current_day_index': next_day_index,
                        'day_name': day_name,
                        'sets_progress': new_sets_progress,
                        'created_at': now,
                        'updated_at': now
                    }
                    
                    history_collection.insert_one(new_history_doc)
                    new_day_started = True
                    new_day_name = day_name
                    
                    logger.info(f"Created new history entry for {day_name} (day {next_day_index + 1})")
                else:
                    logger.info(f"User {user_id} has completed the entire workout plan!")
        
        response = {
            'message': f"Set '{request.set_id}' marked as complete",
            'history_id': history_doc['_id'],
            'set_id': request.set_id,
            'day_complete': all_complete,
            'new_day_started': new_day_started,
            'updated_at': now
        }
        
        if new_day_started:
            response['new_day_name'] = new_day_name
            response['message'] = f"Day complete! Started new day: {new_day_name}"
        elif all_complete:
            response['message'] = "Congratulations! You've completed the entire workout plan!"
        
        logger.info(f"Marked set {request.set_id} as complete for user {user_id}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing set for user '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to complete set: {str(e)}")
