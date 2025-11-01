"""Exercise-related API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from models import CreateExerciseRequest
from database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exercises", tags=["Exercises"])


@router.post("/", response_model=Dict[str, Any])
async def create_exercise(request: CreateExerciseRequest):
    """
    Create a new exercise.
    
    - **exercise_id**: Unique identifier for the exercise
    - **name**: Name of the exercise
    - **force**: Force type (optional)
    - **level**: Difficulty level (optional)
    - **mechanic**: Mechanic type (optional)
    - **equipment**: Equipment required (optional)
    - **primaryMuscles**: Primary muscles targeted (optional)
    - **secondaryMuscles**: Secondary muscles targeted (optional)
    - **instructions**: Step-by-step instructions (optional)
    - **category**: Exercise category (optional)
    
    Returns the created exercise with its ID.
    """
    logger.info(f"POST /exercises/ endpoint called with exercise_id: '{request.exercise_id}'")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot create exercise")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        exercises_collection = db["exercises"]
        
        # Check if exercise already exists
        existing_exercise = exercises_collection.find_one({'_id': request.exercise_id})
        if existing_exercise:
            logger.warning(f"Exercise with exercise_id '{request.exercise_id}' already exists")
            raise HTTPException(
                status_code=409,
                detail=f"Exercise with exercise_id '{request.exercise_id}' already exists. Cannot create duplicate exercise."
            )
        
        # Create exercise document
        exercise_doc = {
            '_id': request.exercise_id,
            'name': request.name
        }
        
        # Add optional fields if provided
        if request.force is not None:
            exercise_doc['force'] = request.force
        if request.level is not None:
            exercise_doc['level'] = request.level
        if request.mechanic is not None:
            exercise_doc['mechanic'] = request.mechanic
        if request.equipment is not None:
            exercise_doc['equipment'] = request.equipment
        if request.primaryMuscles is not None:
            exercise_doc['primaryMuscles'] = request.primaryMuscles
        if request.secondaryMuscles is not None:
            exercise_doc['secondaryMuscles'] = request.secondaryMuscles
        if request.instructions is not None:
            exercise_doc['instructions'] = request.instructions
        if request.category is not None:
            exercise_doc['category'] = request.category
        
        # Insert exercise into database
        result = exercises_collection.insert_one(exercise_doc)
        
        if result.inserted_id:
            logger.info(f"Successfully created exercise with ID: {result.inserted_id}")
        else:
            logger.error("Failed to insert exercise document")
            raise HTTPException(status_code=500, detail="Failed to create exercise")
        
        # Return the created exercise data
        return {
            "id": request.exercise_id,
            "name": request.name,
            "force": request.force,
            "level": request.level,
            "mechanic": request.mechanic,
            "equipment": request.equipment,
            "primaryMuscles": request.primaryMuscles,
            "secondaryMuscles": request.secondaryMuscles,
            "instructions": request.instructions,
            "category": request.category
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating exercise: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create exercise: {str(e)}")


@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_exercises(skip: int = 0, limit: int = 100):
    """
    Get all exercises with pagination support.
    
    - **skip**: Number of exercises to skip (for pagination, default: 0)
    - **limit**: Maximum number of exercises to return (default: 100, max: 1000)
    
    Returns a list of exercises.
    """
    logger.info(f"GET /exercises/ endpoint called (skip={skip}, limit={limit})")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot get exercises")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    # Limit the maximum results to prevent performance issues
    limit = min(limit, 1000)
    
    try:
        exercises_collection = db["exercises"]
        
        # Get total count
        total_count = exercises_collection.count_documents({})
        
        # Fetch exercises with pagination
        exercises = list(exercises_collection.find().skip(skip).limit(limit))
        
        # Format response
        exercises_list = []
        for exercise_doc in exercises:
            exercise_data = {}
            for key, value in exercise_doc.items():
                if key == '_id':
                    exercise_data['id'] = value
                else:
                    exercise_data[key] = value
            exercises_list.append(exercise_data)
        
        logger.info(f"Successfully retrieved {len(exercises_list)} exercise(s) (total: {total_count})")
        
        return exercises_list
    
    except Exception as e:
        logger.error(f"Error retrieving exercises: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get exercises: {str(e)}")


@router.get("/{exercise_id}", response_model=Dict[str, Any])
async def get_exercise(exercise_id: str):
    """
    Get exercise information by exercise_id.
    
    - **exercise_id**: Unique identifier for the exercise
    
    Returns the exercise data including all fields.
    """
    logger.info(f"GET /exercises/{exercise_id} endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot get exercise")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        exercises_collection = db["exercises"]
        
        # Find exercise by exercise_id
        exercise_doc = exercises_collection.find_one({'_id': exercise_id})
        
        if not exercise_doc:
            logger.warning(f"Exercise with exercise_id '{exercise_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Exercise with exercise_id '{exercise_id}' not found"
            )
        
        # Format response
        exercise_data = {}
        for key, value in exercise_doc.items():
            if key == '_id':
                exercise_data['id'] = value
            else:
                exercise_data[key] = value
        
        logger.info(f"Successfully retrieved exercise with exercise_id: {exercise_id}")
        return exercise_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving exercise with exercise_id '{exercise_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get exercise: {str(e)}")


@router.delete("/{exercise_id}", response_model=Dict[str, Any])
async def delete_exercise(exercise_id: str):
    """
    Delete an exercise by exercise_id.
    
    - **exercise_id**: Unique identifier for the exercise
    
    Returns a confirmation message upon successful deletion.
    """
    logger.info(f"DELETE /exercises/{exercise_id} endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot delete exercise")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        exercises_collection = db["exercises"]
        
        # Check if exercise exists
        exercise_doc = exercises_collection.find_one({'_id': exercise_id})
        if not exercise_doc:
            logger.warning(f"Exercise with exercise_id '{exercise_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Exercise with exercise_id '{exercise_id}' not found"
            )
        
        # Check if exercise is referenced by any sets
        sets_collection = db["sets"]
        sets_using_exercise = sets_collection.count_documents({
            '$or': [
                {'exercise_id': exercise_id},
                {'excersise_id': exercise_id}  # Also check typo version
            ]
        })
        
        if sets_using_exercise > 0:
            logger.warning(f"Cannot delete exercise '{exercise_id}': it is referenced by {sets_using_exercise} set(s)")
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete exercise with exercise_id '{exercise_id}': it is referenced by {sets_using_exercise} set(s). Please delete or update the sets first."
            )
        
        # Delete exercise
        result = exercises_collection.delete_one({'_id': exercise_id})
        
        if result.deleted_count == 1:
            logger.info(f"Successfully deleted exercise with exercise_id: {exercise_id}")
            return {
                "message": f"Exercise with exercise_id '{exercise_id}' has been successfully deleted",
                "exercise_id": exercise_id
            }
        else:
            logger.error(f"Failed to delete exercise '{exercise_id}'")
            raise HTTPException(status_code=500, detail=f"Failed to delete exercise with exercise_id '{exercise_id}'")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting exercise with exercise_id '{exercise_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete exercise: {str(e)}")
