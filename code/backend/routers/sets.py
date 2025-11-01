"""Set-related API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from models import CreateSetRequest
from database import get_database
from bson import ObjectId

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sets", tags=["Sets"])


@router.post("/", response_model=Dict[str, Any])
async def create_set(request: CreateSetRequest):
    """
    Create a new set consisting of exercises.
    
    - **name**: Name of the set
    - **exercise_id**: ID of the exercise this set references
    - **reps**: Number of repetitions (optional)
    - **weight**: Weight in kg (optional)
    - **duration_sec**: Duration in seconds (optional)
    
    Returns the created set with a generated ID.
    """
    logger.info(f"POST /sets/ endpoint called with name: '{request.name}'")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot create set")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        sets_collection = db["sets"]
        
        # Generate a new ID for the set
        set_id = str(ObjectId())
        
        # Create set document
        set_doc = {
            '_id': set_id,
            'name': request.name,
            'excersise_id': request.exercise_id,  # Note: using typo to match existing data structure
            'exercise_id': request.exercise_id,   # Also add correct spelling for future use
        }
        
        # Add optional fields if provided
        if request.reps is not None:
            set_doc['reps'] = request.reps
        if request.weight is not None:
            set_doc['weight'] = request.weight
        if request.duration_sec is not None:
            set_doc['duration_sec'] = request.duration_sec
        
        # Insert set into database
        result = sets_collection.insert_one(set_doc)
        
        if result.inserted_id:
            logger.info(f"Successfully created set with ID: {result.inserted_id}")
        else:
            logger.error("Failed to insert set document")
            raise HTTPException(status_code=500, detail="Failed to create set")
        
        # Return the created set data
        return {
            "id": set_id,
            "name": request.name,
            "exercise_id": request.exercise_id,
            "reps": request.reps,
            "weight": request.weight,
            "duration_sec": request.duration_sec
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating set: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create set: {str(e)}")


@router.get("/{set_id}", response_model=Dict[str, Any])
async def get_set(set_id: str):
    """
    Get set information by set_id.
    
    - **set_id**: Unique identifier for the set
    
    Returns the set data including name, exercise_id, reps, weight, and duration_sec.
    """
    logger.info(f"GET /sets/{set_id} endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot get set")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        sets_collection = db["sets"]
        
        # Find set by set_id
        set_doc = sets_collection.find_one({'_id': set_id})
        
        if not set_doc:
            logger.warning(f"Set with set_id '{set_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Set with set_id '{set_id}' not found"
            )
        
        # Format response (handle both excersise_id (typo) and exercise_id (correct))
        exercise_id = set_doc.get('exercise_id') or set_doc.get('excersise_id')
        
        set_data = {
            "id": set_doc.get('_id', set_id),
            "name": set_doc.get('name'),
            "exercise_id": exercise_id,
            "reps": set_doc.get('reps'),
            "weight": set_doc.get('weight'),
            "duration_sec": set_doc.get('duration_sec')
        }
        
        logger.info(f"Successfully retrieved set with set_id: {set_id}")
        return set_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving set with set_id '{set_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get set: {str(e)}")


@router.delete("/{set_id}", response_model=Dict[str, Any])
async def delete_set(set_id: str):
    """
    Delete a set by set_id.
    
    - **set_id**: Unique identifier for the set
    
    Returns a confirmation message upon successful deletion.
    """
    logger.info(f"DELETE /sets/{set_id} endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot delete set")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        sets_collection = db["sets"]
        
        # Check if set exists
        set_doc = sets_collection.find_one({'_id': set_id})
        if not set_doc:
            logger.warning(f"Set with set_id '{set_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Set with set_id '{set_id}' not found"
            )
        
        # Delete set
        result = sets_collection.delete_one({'_id': set_id})
        
        if result.deleted_count == 1:
            logger.info(f"Successfully deleted set with set_id: {set_id}")
            return {
                "message": f"Set with set_id '{set_id}' has been successfully deleted",
                "set_id": set_id
            }
        else:
            logger.error(f"Failed to delete set '{set_id}'")
            raise HTTPException(status_code=500, detail=f"Failed to delete set with set_id '{set_id}'")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting set with set_id '{set_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete set: {str(e)}")
