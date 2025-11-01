"""Workout-related API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from models import CreateWorkoutRequest
from database import get_database
from bson import ObjectId

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workouts", tags=["Workouts"])


@router.post("/", response_model=Dict[str, Any])
async def create_workout(request: CreateWorkoutRequest):
    """
    Create a new workout consisting of sets.
    
    - **workout_plan**: Array of day plans, each containing:
      - **day**: Day of the week (e.g., "Monday", "Tuesday")
      - **exercises_ids**: Array of set IDs for that day
    
    Returns the created workout with a generated ID.
    """
    logger.info(f"POST /workouts/ endpoint called with {len(request.workout_plan)} day plan(s)")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot create workout")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        workouts_collection = db["workouts"]
        
        # Validate that all referenced set IDs exist
        sets_collection = db["sets"]
        all_set_ids = set()
        for day_plan in request.workout_plan:
            all_set_ids.update(day_plan.exercises_ids)
        
        # Check if all set IDs exist
        for set_id in all_set_ids:
            set_doc = sets_collection.find_one({'_id': set_id})
            if not set_doc:
                logger.warning(f"Set with ID '{set_id}' not found")
                raise HTTPException(
                    status_code=404,
                    detail=f"Set with ID '{set_id}' not found. Cannot create workout with non-existent sets."
                )
        
        # Generate a new ID for the workout
        workout_id = str(ObjectId())
        
        # Prepare workout document
        workout_doc = {
            '_id': workout_id,
            'workout_plan': [day_plan.model_dump() for day_plan in request.workout_plan]
        }
        
        # Insert workout into database
        result = workouts_collection.insert_one(workout_doc)
        
        if result.inserted_id:
            logger.info(f"Successfully created workout with ID: {result.inserted_id}")
        else:
            logger.error("Failed to insert workout document")
            raise HTTPException(status_code=500, detail="Failed to create workout")
        
        # Return the created workout data
        return {
            "workout_id": workout_id,
            "workout_plan": [day_plan.model_dump() for day_plan in request.workout_plan],
            "message": f"Successfully created workout with {len(request.workout_plan)} day plan(s)"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workout: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create workout: {str(e)}")


@router.get("/{workout_id}", response_model=Dict[str, Any])
async def get_workout(workout_id: str):
    """
    Get workout information by workout_id.
    
    - **workout_id**: Unique identifier for the workout
    
    Returns the workout data including workout_id and workout_plan.
    """
    logger.info(f"GET /workouts/{workout_id} endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot get workout")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        workouts_collection = db["workouts"]
        
        # Find workout by workout_id
        workout_doc = workouts_collection.find_one({'_id': workout_id})
        
        if not workout_doc:
            logger.warning(f"Workout with workout_id '{workout_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Workout with workout_id '{workout_id}' not found"
            )
        
        # Format response
        workout_data = {
            "workout_id": workout_doc.get('_id', workout_id),
            "workout_plan": workout_doc.get('workout_plan', [])
        }
        
        logger.info(f"Successfully retrieved workout with workout_id: {workout_id}")
        return workout_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving workout with workout_id '{workout_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get workout: {str(e)}")


@router.delete("/{workout_id}", response_model=Dict[str, Any])
async def delete_workout(workout_id: str):
    """
    Delete a workout by workout_id.
    
    - **workout_id**: Unique identifier for the workout
    
    Returns a confirmation message upon successful deletion.
    """
    logger.info(f"DELETE /workouts/{workout_id} endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot delete workout")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        workouts_collection = db["workouts"]
        
        # Check if workout exists
        workout_doc = workouts_collection.find_one({'_id': workout_id})
        if not workout_doc:
            logger.warning(f"Workout with workout_id '{workout_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Workout with workout_id '{workout_id}' not found"
            )
        
        # Delete workout
        result = workouts_collection.delete_one({'_id': workout_id})
        
        if result.deleted_count == 1:
            logger.info(f"Successfully deleted workout with workout_id: {workout_id}")
            return {
                "message": f"Workout with workout_id '{workout_id}' has been successfully deleted",
                "workout_id": workout_id
            }
        else:
            logger.error(f"Failed to delete workout '{workout_id}'")
            raise HTTPException(status_code=500, detail=f"Failed to delete workout with workout_id '{workout_id}'")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workout with workout_id '{workout_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete workout: {str(e)}")
