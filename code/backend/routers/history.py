"""History and progress tracking API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from models import UpdateSetProgressRequest, CompleteSetRequest, UpdateStatusRequest
from database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["History"])


def get_active_workout_id(user_id: str) -> str:
    """Get the active workout ID for a user (first in associated_workout_ids)."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    users_collection = db["users"]
    user_doc = users_collection.find_one({'_id': user_id})
    
    if not user_doc:
        raise HTTPException(status_code=404, detail=f"User with user_id '{user_id}' not found")
    
    associated_workout_ids = user_doc.get('associated_workout_ids', [])
    if not associated_workout_ids:
        raise HTTPException(
            status_code=404,
            detail=f"User '{user_id}' has no associated workouts"
        )
    
    # Return the first workout as the active one
    return associated_workout_ids[0]


def get_workout_structure(workout_id: str) -> Dict[str, Any]:
    """Get workout structure from database."""
    db = get_database()
    workouts_collection = db["workouts"]
    workout_doc = workouts_collection.find_one({'_id': workout_id})
    
    if not workout_doc:
        raise HTTPException(status_code=404, detail=f"Workout with workout_id '{workout_id}' not found")
    
    return workout_doc.get('workout_plan', [])


def get_set_details(set_id: str) -> Optional[Dict[str, Any]]:
    """Get set details from database."""
    db = get_database()
    sets_collection = db["sets"]
    set_doc = sets_collection.find_one({'_id': set_id})
    
    if not set_doc:
        return None
    
    # Get exercise details
    exercise_id = set_doc.get('exercise_id') or set_doc.get('excersise_id')
    exercise_info = None
    if exercise_id:
        exercises_collection = db["exercises"]
        exercise_doc = exercises_collection.find_one({'_id': exercise_id})
        if exercise_doc:
            exercise_info = {
                'id': exercise_doc.get('_id'),
                'name': exercise_doc.get('name'),
                'category': exercise_doc.get('category'),
                'equipment': exercise_doc.get('equipment'),
                'instructions': exercise_doc.get('instructions', [])
            }
    
    return {
        'set_id': set_id,
        'name': set_doc.get('name'),
        'exercise_id': exercise_id,
        'reps': set_doc.get('reps'),
        'weight': set_doc.get('weight'),
        'duration_sec': set_doc.get('duration_sec'),
        'exercise': exercise_info
    }


def get_or_create_progress(user_id: str, workout_id: str) -> Dict[str, Any]:
    """Get or create progress tracking document for a user and workout."""
    db = get_database()
    progress_collection = db["user_workout_progress"]
    progress_id = f"{user_id}_{workout_id}"
    
    progress_doc = progress_collection.find_one({'_id': progress_id})
    
    if not progress_doc:
        # Create new progress document
        progress_doc = {
            '_id': progress_id,
            'user_id': user_id,
            'workout_id': workout_id,
            'current_day_index': 0,
            'completed_sets': [],
            'set_progress': {},
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        progress_collection.insert_one(progress_doc)
        logger.info(f"Created new progress document for user '{user_id}' and workout '{workout_id}'")
    
    return progress_doc


def build_status_response(user_id: str, workout_id: str, progress_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Build status response with current day and sets."""
    workout_plan = get_workout_structure(workout_id)
    
    if not workout_plan:
        raise HTTPException(status_code=404, detail=f"Workout plan is empty for workout '{workout_id}'")
    
    current_day_index = progress_doc.get('current_day_index', 0)
    
    # Handle rollover: if day index exceeds plan length, reset to 0
    if current_day_index >= len(workout_plan):
        current_day_index = 0
        # Update progress document
        db = get_database()
        progress_collection = db["user_workout_progress"]
        progress_id = f"{user_id}_{workout_id}"
        progress_collection.update_one(
            {'_id': progress_id},
            {'$set': {'current_day_index': 0}}
        )
        logger.info(f"Rolled over to day 0 for user '{user_id}' and workout '{workout_id}'")
    
    current_day_plan = workout_plan[current_day_index]
    day_name = current_day_plan.get('day', 'Unknown')
    set_ids = current_day_plan.get('exercises_ids', [])
    
    completed_sets = set(progress_doc.get('completed_sets', []))
    set_progress = progress_doc.get('set_progress', {})
    
    # Build sets list with status
    sets_list = []
    for set_id in set_ids:
        set_details = get_set_details(set_id)
        if not set_details:
            continue
        
        is_complete = set_id in completed_sets
        progress_data = set_progress.get(set_id, {})
        
        sets_list.append({
            'set_id': set_id,
            'set_name': set_details.get('name'),
            'exercise_id': set_details.get('exercise_id'),
            'exercise_name': set_details.get('exercise', {}).get('name') if set_details.get('exercise') else 'Unknown Exercise',
            'target_reps': set_details.get('reps'),
            'target_weight': set_details.get('weight'),
            'target_duration_sec': set_details.get('duration_sec'),
            'completed_reps': progress_data.get('completed_reps'),
            'completed_duration_sec': progress_data.get('completed_duration_sec'),
            'is_complete': is_complete,
            'completed_at': progress_data.get('completed_at'),
            'exercise': set_details.get('exercise')
        })
    
    # Calculate progress
    total_sets = len(sets_list)
    completed_count = sum(1 for s in sets_list if s['is_complete'])
    completion_percentage = int((completed_count / total_sets * 100)) if total_sets > 0 else 0
    
    return {
        'user_id': user_id,
        'workout_id': workout_id,
        'day_name': day_name,
        'current_day_index': current_day_index,
        'sets': sets_list,
        'progress': {
            'completed_sets': completed_count,
            'total_sets': total_sets,
            'completion_percentage': completion_percentage
        }
    }


def check_and_progress_day_if_needed(user_id: str, workout_id: str, progress_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Check if current day is complete and progress if needed. Returns updated progress doc."""
    db = get_database()
    workout_plan = get_workout_structure(workout_id)
    
    if not workout_plan:
        return progress_doc
    
    current_day_index = progress_doc.get('current_day_index', 0)
    
    # Handle rollover if needed
    if current_day_index >= len(workout_plan):
        current_day_index = 0
    
    current_day_plan = workout_plan[current_day_index]
    set_ids_for_day = current_day_plan.get('exercises_ids', [])
    
    completed_sets = set(progress_doc.get('completed_sets', []))
    completed_sets_in_day = [s for s in set_ids_for_day if s in completed_sets]
    all_sets_complete = len(completed_sets_in_day) == len(set_ids_for_day) and len(set_ids_for_day) > 0
    
    if all_sets_complete:
        # Move to next day
        next_day_index = current_day_index + 1
        progress_id = f"{user_id}_{workout_id}"
        progress_collection = db["user_workout_progress"]
        
        # Check if we need to roll over
        if next_day_index >= len(workout_plan):
            next_day_index = 0
            # Clear sets for the new day (day 0)
            new_day_plan = workout_plan[next_day_index]
            new_day_set_ids = set(new_day_plan.get('exercises_ids', []))
            completed_sets = completed_sets - new_day_set_ids
            logger.info(f"Auto-progressing: Day '{current_day_plan.get('day')}' complete, rolling over to '{new_day_plan.get('day')}'")
        else:
            # Clear sets for the current day
            current_day_set_ids = set(set_ids_for_day)
            completed_sets = completed_sets - current_day_set_ids
            next_day_name = workout_plan[next_day_index].get('day', 'Unknown')
            logger.info(f"Auto-progressing: Day '{current_day_plan.get('day')}' complete, moving to '{next_day_name}'")
        
        # Update database
        progress_collection.update_one(
            {'_id': progress_id},
            {
                '$set': {
                    'completed_sets': list(completed_sets),
                    'current_day_index': next_day_index,
                    'updated_at': datetime.utcnow().isoformat()
                }
            }
        )
        
        # Refresh progress doc
        progress_doc = progress_collection.find_one({'_id': progress_id})
        if not progress_doc:
            progress_doc = get_or_create_progress(user_id, workout_id)
    
    return progress_doc


@router.get("/{user_id}/status", response_model=Dict[str, Any])
async def get_status(user_id: str):
    """
    Get current workout status for a user.
    
    Uses the first workout in the user's associated_workout_ids as the active workout.
    
    Returns:
    - Current day information
    - List of sets with completion status
    - Overall progress
    """
    logger.info(f"GET /history/{user_id}/status endpoint called")
    
    try:
        workout_id = get_active_workout_id(user_id)
        progress_doc = get_or_create_progress(user_id, workout_id)
        
        # Check if day should auto-progress
        progress_doc = check_and_progress_day_if_needed(user_id, workout_id, progress_doc)
        
        status = build_status_response(user_id, workout_id, progress_doc)
        
        logger.info(f"Retrieved status for user '{user_id}' - Day: {status['day_name']}, Progress: {status['progress']['completion_percentage']}%")
        return status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for user '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/{user_id}/latest", response_model=Dict[str, Any])
async def get_latest_history(user_id: str):
    """
    Get latest history for a user.
    
    Uses the first workout in the user's associated_workout_ids as the active workout.
    This endpoint is for compatibility with test scripts.
    """
    logger.info(f"GET /history/{user_id}/latest endpoint called")
    
    try:
        workout_id = get_active_workout_id(user_id)
        progress_doc = get_or_create_progress(user_id, workout_id)
        
        # Check if day should auto-progress
        progress_doc = check_and_progress_day_if_needed(user_id, workout_id, progress_doc)
        
        status = build_status_response(user_id, workout_id, progress_doc)
        
        logger.info(f"Retrieved latest history for user '{user_id}' and workout '{workout_id}'")
        return status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get latest history: {str(e)}")


@router.get("/{user_id}/{workout_id}/latest", response_model=Dict[str, Any])
async def get_latest_history_with_workout(user_id: str, workout_id: str):
    """
    Get latest history for a specific user and workout.
    
    This endpoint allows specifying a workout_id explicitly.
    """
    logger.info(f"GET /history/{user_id}/{workout_id}/latest endpoint called")
    
    try:
        progress_doc = get_or_create_progress(user_id, workout_id)
        
        # Check if day should auto-progress
        progress_doc = check_and_progress_day_if_needed(user_id, workout_id, progress_doc)
        
        status = build_status_response(user_id, workout_id, progress_doc)
        
        logger.info(f"Retrieved latest history for user '{user_id}' and workout '{workout_id}'")
        return status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get latest history: {str(e)}")


@router.post("/{user_id}/update", response_model=Dict[str, Any])
async def update_set_progress_endpoint(user_id: str, request: UpdateSetProgressRequest):
    """
    Update progress on a set (e.g., partial reps completed).
    
    This does not mark the set as complete, only updates progress.
    """
    logger.info(f"POST /history/{user_id}/update endpoint called - workout: {request.workout_id}, set: {request.set_id}")
    
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Validate workout exists
        workouts_collection = db["workouts"]
        workout_doc = workouts_collection.find_one({'_id': request.workout_id})
        if not workout_doc:
            raise HTTPException(status_code=404, detail=f"Workout '{request.workout_id}' not found")
        
        # Validate set exists in workout
        workout_plan = workout_doc.get('workout_plan', [])
        set_found = False
        for day_plan in workout_plan:
            if request.set_id in day_plan.get('exercises_ids', []):
                set_found = True
                break
        
        if not set_found:
            raise HTTPException(status_code=404, detail=f"Set '{request.set_id}' not found in workout '{request.workout_id}'")
        
        # Get or create progress
        progress_doc = get_or_create_progress(user_id, request.workout_id)
        progress_id = f"{user_id}_{request.workout_id}"
        
        progress_collection = db["user_workout_progress"]
        set_progress = progress_doc.get('set_progress', {})
        
        # Update set progress
        if request.set_id not in set_progress:
            set_progress[request.set_id] = {}
        
        if request.completed_reps is not None:
            set_progress[request.set_id]['completed_reps'] = request.completed_reps
        if request.completed_duration_sec is not None:
            set_progress[request.set_id]['completed_duration_sec'] = request.completed_duration_sec
        
        set_progress[request.set_id]['updated_at'] = datetime.utcnow().isoformat()
        
        # Update database
        progress_collection.update_one(
            {'_id': progress_id},
            {
                '$set': {
                    'set_progress': set_progress,
                    'updated_at': datetime.utcnow().isoformat()
                }
            }
        )
        
        logger.info(f"Updated progress for set '{request.set_id}' in workout '{request.workout_id}'")
        
        return {
            'message': 'Progress updated successfully',
            'workout_id': request.workout_id,
            'set_id': request.set_id,
            'progress': set_progress[request.set_id]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")


@router.post("/{user_id}/complete", response_model=Dict[str, Any])
async def complete_set_endpoint(user_id: str, request: CompleteSetRequest):
    """
    Mark a set as complete.
    
    After marking a set as complete:
    - If all sets in the current day are complete, automatically move to the next day
    - If all days are complete, roll over to the first day (start again from beginning)
    """
    logger.info(f"POST /history/{user_id}/complete endpoint called - workout: {request.workout_id}, set: {request.set_id}")
    
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Validate workout exists
        workouts_collection = db["workouts"]
        workout_doc = workouts_collection.find_one({'_id': request.workout_id})
        if not workout_doc:
            raise HTTPException(status_code=404, detail=f"Workout '{request.workout_id}' not found")
        
        workout_plan = workout_doc.get('workout_plan', [])
        if not workout_plan:
            raise HTTPException(status_code=404, detail=f"Workout plan is empty for workout '{request.workout_id}'")
        
        # Get or create progress
        progress_doc = get_or_create_progress(user_id, request.workout_id)
        progress_id = f"{user_id}_{request.workout_id}"
        progress_collection = db["user_workout_progress"]
        
        current_day_index = progress_doc.get('current_day_index', 0)
        
        # Handle rollover if needed
        if current_day_index >= len(workout_plan):
            current_day_index = 0
        
        current_day_plan = workout_plan[current_day_index]
        set_ids_for_day = current_day_plan.get('exercises_ids', [])
        
        # Validate set is in current day
        if request.set_id not in set_ids_for_day:
            raise HTTPException(
                status_code=400,
                detail=f"Set '{request.set_id}' is not part of the current day '{current_day_plan.get('day')}'"
            )
        
        completed_sets = set(progress_doc.get('completed_sets', []))
        set_progress = progress_doc.get('set_progress', {})
        
        # Check if set is already complete (before marking)
        was_already_complete = request.set_id in completed_sets
        
        # Mark set as complete
        if request.set_id not in completed_sets:
            completed_sets.add(request.set_id)
            
            # Update progress data
            if request.set_id not in set_progress:
                set_progress[request.set_id] = {}
            
            set_progress[request.set_id]['completed_at'] = datetime.utcnow().isoformat()
            set_progress[request.set_id]['is_complete'] = True
            
            # Get set details to mark progress as complete
            set_details = get_set_details(request.set_id)
            if set_details:
                if set_details.get('reps') and 'completed_reps' not in set_progress[request.set_id]:
                    set_progress[request.set_id]['completed_reps'] = set_details.get('reps')
                if set_details.get('duration_sec') and 'completed_duration_sec' not in set_progress[request.set_id]:
                    set_progress[request.set_id]['completed_duration_sec'] = set_details.get('duration_sec')
        
        # Update database first to save the set completion (even if already complete)
        progress_collection.update_one(
            {'_id': progress_id},
            {
                '$set': {
                    'completed_sets': list(completed_sets),
                    'set_progress': set_progress,
                    'updated_at': datetime.utcnow().isoformat()
                }
            }
        )
        
        # Check if all sets in current day are complete (check AFTER updating)
        # Also check if set was already complete - if so, we might need to progress anyway
        completed_sets_in_day = [s for s in set_ids_for_day if s in completed_sets]
        all_sets_complete = len(completed_sets_in_day) == len(set_ids_for_day) and len(set_ids_for_day) > 0
        
        new_day_started = False
        new_day_name = None
        if was_already_complete:
            message = f"Set '{request.set_id}' was already complete. Checking day progress..."
        else:
            message = f"Set '{request.set_id}' marked as complete"
        
        if all_sets_complete:
            # Move to next day
            next_day_index = current_day_index + 1
            
            # Check if we need to roll over (start from beginning)
            if next_day_index >= len(workout_plan):
                next_day_index = 0
                # Clear completed sets when rolling over (reset for new cycle)
                # Get sets for the new day (day 0) to clear only those
                new_day_plan = workout_plan[next_day_index]
                new_day_set_ids = set(new_day_plan.get('exercises_ids', []))
                # Remove sets that belong to the new day from completed_sets so they can be done again
                completed_sets = completed_sets - new_day_set_ids
                message = f"All sets in '{current_day_plan.get('day')}' completed! Rolling over to first day '{new_day_plan.get('day')}'."
                logger.info(f"Workout plan cycle complete for user '{user_id}' and workout '{request.workout_id}' - rolling over to day 0 and clearing completed sets for new day")
            else:
                next_day_name = workout_plan[next_day_index].get('day', 'Unknown')
                # Clear completed sets for the current day when moving to next day
                # Keep sets that belong to other days, but clear the current day's sets
                current_day_set_ids = set(set_ids_for_day)
                completed_sets = completed_sets - current_day_set_ids
                message = f"All sets in '{current_day_plan.get('day')}' completed! Moving to next day: '{next_day_name}'"
                logger.info(f"Day '{current_day_plan.get('day')}' completed, moving to '{next_day_name}' for user '{user_id}'")
            
            # Update day index
            current_day_index = next_day_index
            new_day_started = True
            new_day_name = workout_plan[next_day_index].get('day', 'Unknown') if next_day_index < len(workout_plan) else None
            
            # Update database again with new day index and cleared completed sets
            progress_collection.update_one(
                {'_id': progress_id},
                {
                    '$set': {
                        'completed_sets': list(completed_sets),
                        'current_day_index': current_day_index,
                        'updated_at': datetime.utcnow().isoformat()
                    }
                }
            )
        
        logger.info(f"Set '{request.set_id}' completed. Day complete: {all_sets_complete}, New day: {new_day_started}")
        
        return {
            'message': message,
            'workout_id': request.workout_id,
            'set_id': request.set_id,
            'day_complete': all_sets_complete,
            'new_day_started': new_day_started,
            'new_day_name': new_day_name,
            'current_day_index': current_day_index
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing set: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to complete set: {str(e)}")


@router.put("/{user_id}/status", response_model=Dict[str, Any])
async def update_status(user_id: str, request: UpdateStatusRequest):
    """
    Update workout status - mark sets as complete.
    
    Request body should contain:
    - workout_id: (optional, uses active workout if not provided)
    - set_id: ID of the set to mark as complete
    
    This is a simplified endpoint that wraps the complete functionality.
    """
    logger.info(f"PUT /history/{user_id}/status endpoint called")
    
    workout_id = request.workout_id or get_active_workout_id(user_id)
    
    complete_request = CompleteSetRequest(workout_id=workout_id, set_id=request.set_id)
    return await complete_set_endpoint(user_id, complete_request)


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint for history router."""
    return {"status": "ok", "service": "history"}

