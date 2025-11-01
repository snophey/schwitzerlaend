from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import os
import logging
import json
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# MongoDB Atlas connection configuration with X509 certificate authentication
CLUSTER_HOST = "cluster0.udio3ct.mongodb.net"
DATABASE_NAME = "schwitzerland"
CERTIFICATE_FILE = "secrets/X509-cert-7850383135344030658.pem"

# Construct MongoDB Atlas connection string with X509 authentication
MONGODB_URI = f"mongodb+srv://{CLUSTER_HOST}/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"

# Global database connection
db = None
client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    logger.info("Starting up FastAPI application...")
    global db, client
    client, db = connect_to_mongodb()
    if db is None:
        logger.error("Failed to connect to MongoDB on startup - raising exception")
        raise Exception("Failed to connect to MongoDB on startup")
    logger.info("Application startup complete. MongoDB connection established.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    if client is not None:
        logger.info("Closing MongoDB connection...")
        client.close()
        logger.info("MongoDB connection closed.")
    logger.info("Application shutdown complete.")

app = FastAPI(
    title="Workouts API",
    description="""
    A comprehensive REST API for managing workout plans, exercises, sets, and users.
    
    ## Features
    
    * **User Management**: Create, retrieve, and delete users
    * **Workout Management**: Create, retrieve, and delete workout plans
    * **Set Management**: Create, retrieve, and delete exercise sets
    * **AI-Powered Generation**: Generate custom workout plans using OpenAI
    * **Weekly Overview**: Get detailed weekly workout schedules for users
    
    ## Collections
    
    The API uses MongoDB with the following collections:
    - **users**: User accounts and their associated workout IDs
    - **workouts**: Workout plans with day-by-day schedules
    - **sets**: Exercise sets with reps, weight, and duration
    - **exercises**: Exercise definitions and details
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Request models
class Exercise(BaseModel):
    """Exercise model for workout generation."""
    type: str = Field(..., description="Type of exercise: 'repetition', 'weighted repetition', 'time', 'distance', or 'skill'", example="repetition")
    reps: Optional[int] = Field(None, description="Number of repetitions (for repetition, weighted repetition, or skill types)", example=10)
    weight: Optional[float] = Field(None, description="Weight in kg (for weighted repetition type)", example=20.5)
    duration_sec: Optional[int] = Field(None, description="Duration in seconds (for time type)", example=60)
    skill: Optional[str] = Field(None, description="Skill description (for skill type)", example="Balance hold")
    description: str = Field(..., description="Detailed description of how to perform the exercise", example="Perform push-ups with proper form, keeping your back straight")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "repetition",
                "reps": 15,
                "description": "Perform 15 push-ups with proper form"
            }
        }

class AddWorkoutRequest(BaseModel):
    """Request model for adding a workout manually."""
    workout_name: str = Field(..., description="Name of the workout", example="Morning Yoga")
    exercises: Optional[Dict[str, Exercise]] = Field(None, description="Dictionary of exercise names mapped to Exercise objects")

    class Config:
        json_schema_extra = {
            "example": {
                "workout_name": "Morning Yoga",
                "exercises": {
                    "Downward Dog": {
                        "type": "time",
                        "duration_sec": 60,
                        "description": "Hold downward dog pose for 60 seconds"
                    }
                }
            }
        }

class GenerateWorkoutRequest(BaseModel):
    """Request model for AI-powered workout generation."""
    prompt: str = Field(..., description="Natural language description of the desired workout", example="I want soft yoga mainly stretching mid efforts")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "I want a full body strength workout with 5 exercises"
            }
        }

class CreateSetRequest(BaseModel):
    """Request model for creating an exercise set."""
    name: str = Field(..., description="Name of the set", example="Push-ups Set 1")
    exercise_id: str = Field(..., description="ID of the exercise this set references", example="push_up_001")
    reps: Optional[int] = Field(None, description="Number of repetitions", example=15)
    weight: Optional[float] = Field(None, description="Weight in kg", example=0.0)
    duration_sec: Optional[int] = Field(None, description="Duration in seconds", example=60)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Push-ups Set 1",
                "exercise_id": "push_up_001",
                "reps": 15,
                "weight": None,
                "duration_sec": None
            }
        }

class CreateExerciseRequest(BaseModel):
    """Request model for creating an exercise."""
    exercise_id: str = Field(..., description="Unique identifier for the exercise", example="3_4_Sit-Up")
    name: str = Field(..., description="Name of the exercise", example="3/4 Sit-Up")
    force: Optional[str] = Field(None, description="Force type: 'pull' or 'push'", example="pull")
    level: Optional[str] = Field(None, description="Difficulty level: 'beginner', 'intermediate', or 'expert'", example="beginner")
    mechanic: Optional[str] = Field(None, description="Mechanic type: 'compound' or 'isolation'", example="compound")
    equipment: Optional[str] = Field(None, description="Equipment required", example="body only")
    primaryMuscles: Optional[List[str]] = Field(None, description="Primary muscles targeted", example=["abdominals"])
    secondaryMuscles: Optional[List[str]] = Field(None, description="Secondary muscles targeted", example=[])
    instructions: Optional[List[str]] = Field(None, description="Step-by-step instructions", example=["Lie down on the floor..."])
    category: Optional[str] = Field(None, description="Exercise category", example="strength")

    class Config:
        json_schema_extra = {
            "example": {
                "exercise_id": "3_4_Sit-Up",
                "name": "3/4 Sit-Up",
                "force": "pull",
                "level": "beginner",
                "mechanic": "compound",
                "equipment": "body only",
                "primaryMuscles": ["abdominals"],
                "secondaryMuscles": [],
                "instructions": ["Lie down on the floor and secure your feet."],
                "category": "strength"
            }
        }

class DayPlan(BaseModel):
    """Day plan model for workout schedules."""
    day: str = Field(..., description="Day of the week", example="Monday")
    exercises_ids: List[str] = Field(..., description="List of set IDs for this day", example=["set_1", "set_2", "set_3"])

    class Config:
        json_schema_extra = {
            "example": {
                "day": "Monday",
                "exercises_ids": ["1", "2", "3"]
            }
        }

class CreateWorkoutRequest(BaseModel):
    """Request model for creating a workout plan."""
    workout_plan: List[DayPlan] = Field(..., description="Array of day plans, each with day and exercises_ids")

    class Config:
        json_schema_extra = {
            "example": {
                "workout_plan": [
                    {
                        "day": "Monday",
                        "exercises_ids": ["1", "2", "3"]
                    },
                    {
                        "day": "Wednesday",
                        "exercises_ids": ["3"]
                    }
                ]
            }
        }

def connect_to_mongodb():
    """Connect to MongoDB using X509 certificate authentication."""
    logger.info(f"Attempting to connect to MongoDB Atlas cluster: {CLUSTER_HOST}")
    logger.info(f"Target database: {DATABASE_NAME}")
    
    try:
        # Check if certificate file exists
        logger.info(f"Checking for certificate file: {CERTIFICATE_FILE}")
        if not os.path.exists(CERTIFICATE_FILE):
            logger.error(f"Certificate file '{CERTIFICATE_FILE}' not found in {os.getcwd()}")
            return None, None
        logger.info(f"Certificate file found: {CERTIFICATE_FILE}")
        
        # Create MongoDB client with X509 certificate authentication
        logger.info("Creating MongoDB client with X509 certificate authentication...")
        client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsCertificateKeyFile=CERTIFICATE_FILE,
            serverSelectionTimeoutMS=10000
        )
        logger.info("MongoDB client created successfully.")
        
        # Test connection
        logger.info("Testing MongoDB connection with ping command...")
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB Atlas using X509 certificate!")
        
        # Get database
        logger.info(f"Accessing database: {DATABASE_NAME}")
        db = client[DATABASE_NAME]
        logger.info(f"Connected to database: {DATABASE_NAME}")
        
        # List available collections
        collections = db.list_collection_names()
        logger.info(f"Found {len(collections)} collection(s) in database: {collections}")
        
        return client, db
    
    except ConnectionFailure as e:
        logger.error(f"Connection failure: {e}")
        return None, None
    except ServerSelectionTimeoutError as e:
        logger.error(f"Server selection timeout: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error occurred connecting to MongoDB: {e}", exc_info=True)
        return None, None

@app.get("/")
async def root():
    """Root endpoint."""
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to the Workouts API",
        "endpoints": [
            "POST /users/{user_id} - Create a new user",
            "GET /users/{user_id} - Get user information by user_id",
            "GET /users/{user_id}/weekly-overview - Get weekly workout overview for a user",
            "POST /workouts/ - Create a new workout consisting of sets",
            "GET /workouts/{workout_id} - Get workout information by workout_id",
            "DELETE /workouts/{workout_id} - Delete a workout by workout_id",
            "POST /sets/ - Create a new set consisting of exercises",
            "GET /sets/{set_id} - Get set information by set_id",
            "DELETE /sets/{set_id} - Delete a set by set_id",
            "POST /exercises/ - Create a new exercise",
            "GET /exercises/ - Get all exercises",
            "GET /exercises/{exercise_id} - Get exercise information by exercise_id",
            "DELETE /exercises/{exercise_id} - Delete an exercise by exercise_id",
            "DELETE /users/{user_id} - Delete a user by user_id",
            "POST /users/{user_id}/workouts/{workout_id} - Add a workout id to the workouts list",
            "DELETE /users/{user_id}/workouts/{workout_id} - Remove a workout id from the workouts list",
        ]
    }

def get_collection_name():
    """Helper function to get the collection name."""
    if db is None:
        return None
    
    collections = db.list_collection_names()
    if not collections:
        return None
    
    # Try to find 'schwitzerland' collection first (based on data structure)
    if "schwitzerland" in collections:
        return "schwitzerland"
    
    # Otherwise use the first collection
    return collections[0]

@app.post("/users/{user_id}", response_model=Dict[str, Any], tags=["Users"])
async def create_user(user_id: str):
    """
    Create a new user.
    
    - **user_id**: Unique identifier for the user
    
    Returns the created user data with associated_workout_ids set to null by default.
    """
    logger.info(f"POST /users/{user_id} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot create user")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for users
        users_collection = db["users"]
        
        # Check if user already exists
        existing_user = users_collection.find_one({'_id': user_id})
        if existing_user:
            logger.warning(f"User with user_id '{user_id}' already exists")
            raise HTTPException(
                status_code=409,
                detail=f"User with user_id '{user_id}' already exists. Cannot create duplicate user."
            )
        
        # Create user document with associated_workout_ids set to empty list
        user_doc = {
            '_id': user_id,
            'associated_workout_ids': []
        }
        
        # Insert user into database
        result = users_collection.insert_one(user_doc)
        
        if result.inserted_id:
            logger.info(f"Successfully created user with user_id: {user_id} (ID: {result.inserted_id})")
        else:
            logger.error("Failed to insert user document")
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # Return the created user data
        return {
            "user_id": user_id,
            "associated_workout_ids": []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user with user_id '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@app.get("/users/{user_id}", response_model=Dict[str, Any], tags=["Users"])
async def get_user(user_id: str):
    """
    Get user information by user_id.
    
    - **user_id**: Unique identifier for the user
    
    Returns the user data including user_id and associated_workout_ids.
    """
    logger.info(f"GET /users/{user_id} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot get user")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for users
        users_collection = db["users"]
        
        # Find user by user_id
        user_doc = users_collection.find_one({'_id': user_id})
        
        if not user_doc:
            logger.warning(f"User with user_id '{user_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"User with user_id '{user_id}' not found"
            )
        
        # Format response (exclude MongoDB _id, use user_id instead)
        user_data = {
            "user_id": user_doc.get('_id', user_id),
            "associated_workout_ids": user_doc.get('associated_workout_ids', [])
        }
        
        logger.info(f"Successfully retrieved user with user_id: {user_id}")
        return user_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user with user_id '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

@app.delete("/users/{user_id}", response_model=Dict[str, Any], tags=["Users"])
async def delete_user(user_id: str):
    """
    Delete a user by user_id.
    
    - **user_id**: Unique identifier for the user
    
    Returns a confirmation message upon successful deletion.
    """
    logger.info(f"DELETE /users/{user_id} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot delete user")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for users
        users_collection = db["users"]
        
        # Check if user exists
        user_doc = users_collection.find_one({'_id': user_id})
        if not user_doc:
            logger.warning(f"User with user_id '{user_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"User with user_id '{user_id}' not found"
            )
        
        # Delete user
        result = users_collection.delete_one({'_id': user_id})
        
        if result.deleted_count == 1:
            logger.info(f"Successfully deleted user with user_id: {user_id}")
            return {
                "message": f"User with user_id '{user_id}' has been successfully deleted",
                "user_id": user_id
            }
        else:
            logger.error(f"Failed to delete user '{user_id}'")
            raise HTTPException(status_code=500, detail=f"Failed to delete user with user_id '{user_id}'")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user with user_id '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

@app.post("/sets/", response_model=Dict[str, Any], tags=["Sets"])
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
    
    if db is None:
        logger.error("Database connection is None - cannot create set")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for sets
        sets_collection = db["sets"]
        
        # Generate a new ID for the set (using ObjectId converted to string)
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

@app.get("/sets/{set_id}", response_model=Dict[str, Any], tags=["Sets"])
async def get_set(set_id: str):
    """
    Get set information by set_id.
    
    - **set_id**: Unique identifier for the set
    
    Returns the set data including name, exercise_id, reps, weight, and duration_sec.
    """
    logger.info(f"GET /sets/{set_id} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot get set")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for sets
        sets_collection = db["sets"]
        
        # Find set by set_id
        set_doc = sets_collection.find_one({'_id': set_id})
        
        if not set_doc:
            logger.warning(f"Set with set_id '{set_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Set with set_id '{set_id}' not found"
            )
        
        # Format response (exclude MongoDB _id, use id instead)
        # Handle both excersise_id (typo) and exercise_id (correct)
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

@app.delete("/sets/{set_id}", response_model=Dict[str, Any], tags=["Sets"])
async def delete_set(set_id: str):
    """
    Delete a set by set_id.
    
    - **set_id**: Unique identifier for the set
    
    Returns a confirmation message upon successful deletion.
    """
    logger.info(f"DELETE /sets/{set_id} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot delete set")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for sets
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

@app.post("/exercises/", response_model=Dict[str, Any], tags=["Exercises"])
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
    
    if db is None:
        logger.error("Database connection is None - cannot create exercise")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for exercises
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

@app.get("/exercises/", response_model=List[Dict[str, Any]], tags=["Exercises"])
async def get_all_exercises(skip: int = 0, limit: int = 100):
    """
    Get all exercises with pagination support.
    
    - **skip**: Number of exercises to skip (for pagination, default: 0)
    - **limit**: Maximum number of exercises to return (default: 100, max: 1000)
    
    Returns a list of exercises.
    """
    logger.info(f"GET /exercises/ endpoint called (skip={skip}, limit={limit})")
    
    if db is None:
        logger.error("Database connection is None - cannot get exercises")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    # Limit the maximum results to prevent performance issues
    limit = min(limit, 1000)
    
    try:
        # Use a collection for exercises
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

@app.get("/exercises/{exercise_id}", response_model=Dict[str, Any], tags=["Exercises"])
async def get_exercise(exercise_id: str):
    """
    Get exercise information by exercise_id.
    
    - **exercise_id**: Unique identifier for the exercise
    
    Returns the exercise data including all fields.
    """
    logger.info(f"GET /exercises/{exercise_id} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot get exercise")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for exercises
        exercises_collection = db["exercises"]
        
        # Find exercise by exercise_id
        exercise_doc = exercises_collection.find_one({'_id': exercise_id})
        
        if not exercise_doc:
            logger.warning(f"Exercise with exercise_id '{exercise_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Exercise with exercise_id '{exercise_id}' not found"
            )
        
        # Format response (exclude MongoDB _id, use id instead)
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

@app.delete("/exercises/{exercise_id}", response_model=Dict[str, Any], tags=["Exercises"])
async def delete_exercise(exercise_id: str):
    """
    Delete an exercise by exercise_id.
    
    - **exercise_id**: Unique identifier for the exercise
    
    Returns a confirmation message upon successful deletion.
    """
    logger.info(f"DELETE /exercises/{exercise_id} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot delete exercise")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for exercises
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

@app.post("/workouts/", response_model=Dict[str, Any], tags=["Workouts"])
async def create_workout(request: CreateWorkoutRequest):
    """
    Create a new workout consisting of sets.
    
    - **workout_plan**: Array of day plans, each containing:
      - **day**: Day of the week (e.g., "Monday", "Tuesday")
      - **exercises_ids**: Array of set IDs for that day
    
    Returns the created workout with a generated ID.
    """
    logger.info(f"POST /workouts/ endpoint called with {len(request.workout_plan)} day plan(s)")
    
    if db is None:
        logger.error("Database connection is None - cannot create workout")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for workouts
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
        
        # Generate a new ID for the workout (using ObjectId converted to string)
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

@app.get("/workouts/{workout_id}", response_model=Dict[str, Any], tags=["Workouts"])
async def get_workout(workout_id: str):
    """
    Get workout information by workout_id.
    
    - **workout_id**: Unique identifier for the workout
    
    Returns the workout data including workout_id and workout_plan.
    """
    logger.info(f"GET /workouts/{workout_id} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot get workout")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for workouts
        workouts_collection = db["workouts"]
        
        # Find workout by workout_id
        workout_doc = workouts_collection.find_one({'_id': workout_id})
        
        if not workout_doc:
            logger.warning(f"Workout with workout_id '{workout_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Workout with workout_id '{workout_id}' not found"
            )
        
        # Format response (exclude MongoDB _id, use workout_id instead)
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

@app.delete("/workouts/{workout_id}", response_model=Dict[str, Any], tags=["Workouts"])
async def delete_workout(workout_id: str):
    """
    Delete a workout by workout_id.
    
    - **workout_id**: Unique identifier for the workout
    
    Returns a confirmation message upon successful deletion.
    """
    logger.info(f"DELETE /workouts/{workout_id} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot delete workout")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use a collection for workouts
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

@app.post("/users/{user_id}/workouts/{workout_id}", response_model=Dict[str, Any], tags=["User Workouts"])
async def add_workout_to_user(user_id: str, workout_id: str):
    """
    Add a workout ID to the user's associated_workout_ids list.
    
    - **user_id**: ID of the user
    - **workout_id**: ID of the workout to associate with the user
    
    Returns the updated user data.
    """
    logger.info(f"POST /users/{user_id}/workouts/{workout_id} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot add workout to user")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use collections
        users_collection = db["users"]
        workouts_collection = db["workouts"]
        
        # Check if user exists
        user_doc = users_collection.find_one({'_id': user_id})
        if not user_doc:
            logger.warning(f"User with user_id '{user_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"User with user_id '{user_id}' not found"
            )
        
        # Check if workout exists
        workout_doc = workouts_collection.find_one({'_id': workout_id})
        if not workout_doc:
            logger.warning(f"Workout with workout_id '{workout_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Workout with workout_id '{workout_id}' not found"
            )
        
        # Get current associated_workout_ids (handle None or empty list)
        current_workout_ids = user_doc.get('associated_workout_ids', [])
        if current_workout_ids is None:
            current_workout_ids = []
        
        # Check if workout_id is already in the list
        if workout_id in current_workout_ids:
            logger.warning(f"Workout '{workout_id}' is already associated with user '{user_id}'")
            raise HTTPException(
                status_code=409,
                detail=f"Workout with workout_id '{workout_id}' is already associated with user '{user_id}'"
            )
        
        # Add workout_id to the list
        updated_workout_ids = current_workout_ids + [workout_id]
        
        # Update user document
        result = users_collection.update_one(
            {'_id': user_id},
            {'$set': {'associated_workout_ids': updated_workout_ids}}
        )
        
        if result.modified_count == 1:
            logger.info(f"Successfully added workout '{workout_id}' to user '{user_id}'")
        elif result.matched_count == 0:
            logger.error(f"User '{user_id}' not found for update")
            raise HTTPException(status_code=404, detail=f"User with user_id '{user_id}' not found")
        else:
            logger.warning(f"Update operation didn't modify user document")
        
        # Return updated user data
        return {
            "user_id": user_id,
            "associated_workout_ids": updated_workout_ids,
            "message": f"Successfully added workout '{workout_id}' to user '{user_id}'"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding workout to user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add workout to user: {str(e)}")

@app.delete("/users/{user_id}/workouts/{workout_id}", response_model=Dict[str, Any], tags=["User Workouts"])
async def remove_workout_from_user(user_id: str, workout_id: str):
    """
    Remove a workout ID from the user's associated_workout_ids list.
    
    - **user_id**: ID of the user
    - **workout_id**: ID of the workout to remove from the user's associated workouts
    
    Returns the updated user data.
    """
    logger.info(f"DELETE /users/{user_id}/workouts/{workout_id} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot remove workout from user")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use collections
        users_collection = db["users"]
        
        # Check if user exists
        user_doc = users_collection.find_one({'_id': user_id})
        if not user_doc:
            logger.warning(f"User with user_id '{user_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"User with user_id '{user_id}' not found"
            )
        
        # Get current associated_workout_ids (handle None or empty list)
        current_workout_ids = user_doc.get('associated_workout_ids', [])
        if current_workout_ids is None:
            current_workout_ids = []
        
        # Check if workout_id is in the list
        if workout_id not in current_workout_ids:
            logger.warning(f"Workout '{workout_id}' is not associated with user '{user_id}'")
            raise HTTPException(
                status_code=404,
                detail=f"Workout with workout_id '{workout_id}' is not associated with user '{user_id}'"
            )
        
        # Remove workout_id from the list
        updated_workout_ids = [wid for wid in current_workout_ids if wid != workout_id]
        
        # Update user document
        result = users_collection.update_one(
            {'_id': user_id},
            {'$set': {'associated_workout_ids': updated_workout_ids}}
        )
        
        if result.modified_count == 1:
            logger.info(f"Successfully removed workout '{workout_id}' from user '{user_id}'")
        elif result.matched_count == 0:
            logger.error(f"User '{user_id}' not found for update")
            raise HTTPException(status_code=404, detail=f"User with user_id '{user_id}' not found")
        else:
            logger.warning(f"Update operation didn't modify user document")
        
        # Return updated user data
        return {
            "user_id": user_id,
            "associated_workout_ids": updated_workout_ids,
            "message": f"Successfully removed workout '{workout_id}' from user '{user_id}'"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing workout from user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to remove workout from user: {str(e)}")


@app.get("/users/{user_id}/weekly-overview", response_model=Dict[str, Any], tags=["User Workouts"])
async def get_weekly_overview(user_id: str):
    """
    Get weekly workout overview for a specific user.
    
    - **user_id**: ID of the user
    
    Returns a weekly overview showing all 7 days (Monday-Sunday) with:
    - Sets scheduled for each day (with reps, weight, duration details)
    - Full exercise information from the exercises collection (if available)
    - Rest days marked when no training is scheduled
    - Summary statistics (training days, rest days, total sets)
    """
    logger.info(f"GET /users/{user_id}/weekly-overview endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot get weekly overview")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get workout plan from workouts collection
        workouts_collection = db["workouts"]
        workout_doc = workouts_collection.find_one({'_id': user_id})
        
        if not workout_doc:
            logger.warning(f"No workout plan found for user_id: {user_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No workout plan found for user_id: {user_id}"
            )
        
        workout_plan = workout_doc.get('workout_plan', [])
        
        if not workout_plan:
            logger.warning(f"Workout plan is empty for user_id: {user_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Workout plan is empty for user_id: {user_id}"
            )
        
        # Get all sets from sets collection
        sets_collection = db["sets"]
        all_sets = {}
        
        # Collect all unique set IDs and exercise IDs from the workout plan
        set_ids = set()
        exercise_ids = set()
        
        for day_plan in workout_plan:
            exercises_ids = day_plan.get('exercises_ids', [])
            # Ensure IDs are strings
            exercises_ids = [str(eid) if not isinstance(eid, str) else eid for eid in exercises_ids]
            set_ids.update(exercises_ids)
        
        # Fetch all sets
        for set_id in set_ids:
            set_doc = sets_collection.find_one({'_id': set_id})
            if set_doc:
                # Convert ObjectId to string if present, and format the document
                formatted_set = {}
                for key, value in set_doc.items():
                    if key != '_id':  # Exclude MongoDB _id from response
                        formatted_set[key] = value
                
                # Collect exercise_id from the set (note: there's a typo "excersise_id" in the data)
                exercise_id = formatted_set.get('excersise_id') or formatted_set.get('exercise_id')
                if exercise_id:
                    exercise_ids.add(exercise_id)
                
                all_sets[set_id] = formatted_set
        
        # Get all exercises from exercises collection
        exercises_collection = db["exercises"]
        all_exercises = {}
        
        # Fetch all exercises
        for exercise_id in exercise_ids:
            exercise_doc = exercises_collection.find_one({'_id': exercise_id})
            if exercise_doc:
                # Format exercise document (exclude MongoDB _id from response, but include it as 'id')
                formatted_exercise = {}
                for key, value in exercise_doc.items():
                    if key == '_id':
                        formatted_exercise['id'] = value
                    else:
                        formatted_exercise[key] = value
                all_exercises[exercise_id] = formatted_exercise
        
        # Define week days in order
        week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Create weekly plan structure with all 7 days
        weekly_plan = []
        day_sets_map = {}
        
        # Map existing days
        for day_plan in workout_plan:
            day = day_plan.get('day', '')
            exercises_ids = day_plan.get('exercises_ids', [])
            # Ensure IDs are strings
            exercises_ids = [str(eid) if not isinstance(eid, str) else eid for eid in exercises_ids]
            day_sets_map[day] = [all_sets.get(str(eid)) for eid in exercises_ids if str(eid) in all_sets]
        
        # Build response with all 7 days
        for day in week_days:
            sets_for_day = day_sets_map.get(day, [])
            
            # Format sets for this day
            formatted_sets = []
            for set_data in sets_for_day:
                if set_data:
                    # Get exercise_id from set (handle typo "excersise_id")
                    exercise_id = set_data.get('excersise_id') or set_data.get('exercise_id')
                    
                    # Get exercise information if it exists
                    exercise_info = None
                    if exercise_id and exercise_id in all_exercises:
                        exercise_info = all_exercises[exercise_id]
                    
                    formatted_set = {
                        "name": set_data.get('name', 'Unknown Exercise'),
                        "reps": set_data.get('reps'),
                        "weight": set_data.get('weight'),
                        "duration_sec": set_data.get('duration_sec'),
                        "exercise_id": exercise_id or 'N/A',
                        "exercise": exercise_info  # Include full exercise details if available
                    }
                    formatted_sets.append(formatted_set)
            
            weekly_plan.append({
                "day": day,
                "day_number": week_days.index(day) + 1,
                "sets": formatted_sets,
                "is_rest_day": len(formatted_sets) == 0
            })
        
        # Calculate summary
        total_sets = sum(len(day_entry['sets']) for day_entry in weekly_plan)
        training_days = sum(1 for day_entry in weekly_plan if not day_entry['is_rest_day'])
        rest_days = 7 - training_days
        
        logger.info(f"Retrieved weekly overview for user_id: {user_id} - {training_days} training days, {total_sets} total sets")
        
        return {
            "user_id": user_id,
            "weekly_plan": weekly_plan,
            "summary": {
                "training_days": training_days,
                "rest_days": rest_days,
                "total_sets": total_sets
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving weekly overview for user_id '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get weekly overview: {str(e)}")
