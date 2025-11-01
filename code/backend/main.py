from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
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
    description="API for retrieving workout information",
    lifespan=lifespan
)

# Request models
class Exercise(BaseModel):
    type: str  # 'repetition', 'weighted repetition', 'time', 'distance', 'skill'
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration_sec: Optional[int] = None
    # distance_m: Optional[int] = None
    skill: Optional[str] = None
    description: str

class AddWorkoutRequest(BaseModel):
    workout_name: str
    exercises: Optional[Dict[str, Exercise]] = None  # Optional: exercise_name -> Exercise

class GenerateWorkoutRequest(BaseModel):
    prompt: str

class CreateSetRequest(BaseModel):
    name: str
    exercise_id: str  # Note: using exercise_id (will also accept excersise_id typo from existing data)
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration_sec: Optional[int] = None

class DayPlan(BaseModel):
    day: str  # e.g., "Monday", "Tuesday", etc.
    exercises_ids: List[str]  # List of set IDs

class CreateWorkoutRequest(BaseModel):
    workout_plan: List[DayPlan]  # Array of day plans, each with day and exercises_ids

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
            "POST /workouts/generate - Generate a workout using AI from a prompt",
            "POST /users/{user_id} - Create a new user",
            "GET /users/{user_id} - Get user information by user_id",
            "GET /users/{user_id}/weekly-overview - Get weekly workout overview for a user",
            "POST /workouts/ - Create a new workout consisting of sets",
            "GET /workouts/{workout_id} - Get workout information by workout_id",
            "POST /sets/ - Create a new set consisting of exercises",
            "GET /sets/{set_id} - Get set information by set_id",
            "POST /users/{user_id}/workouts/{workout_id} - Add a workout id to the workouts list",
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

@app.post("/users/{user_id}", response_model=Dict[str, Any])
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

@app.get("/users/{user_id}", response_model=Dict[str, Any])
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

@app.post("/sets/", response_model=Dict[str, Any])
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

@app.get("/sets/{set_id}", response_model=Dict[str, Any])
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

@app.post("/workouts/", response_model=Dict[str, Any])
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

@app.get("/workouts/{workout_id}", response_model=Dict[str, Any])
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

@app.post("/users/{user_id}/workouts/{workout_id}", response_model=Dict[str, Any])
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

@app.post("/workouts/generate", response_model=Dict[str, Any])
async def generate_workout(request: GenerateWorkoutRequest):
    """
    Generate a workout using OpenAI based on a natural language prompt.
    
    - **prompt**: A natural language description of the workout you want (e.g., "I want soft yoga mainly stretching mid efforts")
    
    The AI will generate a workout with exercises in JSON format and add it to the database.
    """
    logger.info(f"POST /workouts/generate endpoint called with prompt: '{request.prompt}'")
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )
    
    try:
        # Initialize OpenAI client
        openai_client = OpenAI(api_key=openai_api_key)
        logger.info("OpenAI client initialized")
        
        # Create system prompt that specifies the JSON format
        system_prompt = """You are a fitness expert. Generate a workout plan in JSON format ONLY.

The response must be valid JSON with this EXACT structure where the workout name is the top-level key:
{
  "Workout Name": {
    "Exercise Name 1": {
      "type": "repetition" | "weighted repetition" | "time" | "distance" | "skill",
      "description": "Detailed description of how to perform the exercise",
      "reps": <number> (only if type is "repetition", "weighted repetition", or "skill"),
      "weight": <number> (only if type is "weighted repetition"),
      "duration_sec": <number> (only if type is "time"),
      "distance_m": <number> (only if type is "distance"),
      "skill": <string> (only if type is "skill")
    },
    "Exercise Name 2": {
      "type": "time",
      "duration_sec": 60,
      "description": "Hold the pose for 60 seconds"
    }
  }
}

IMPORTANT:
- The workout name MUST be the top-level key (not inside a "workout_name" field)
- Each exercise name is a key under the workout
- Return ONLY the JSON object, no other text before or after
- Include 3-6 exercises per workout
- Make exercise descriptions detailed and helpful
- Choose appropriate exercise types based on the workout description
- Ensure all required fields match the exercise type
- Use proper JSON formatting

Example:
{
  "Gentle Yoga": {
    "Downward Dog": {
      "type": "time",
      "duration_sec": 60,
      "description": "Hold downward dog pose for 60 seconds, focusing on stretching the hamstrings and shoulders."
    },
    "Child's Pose": {
      "type": "time",
      "duration_sec": 90,
      "description": "Rest in child's pose for 90 seconds, breathing deeply and relaxing."
    }
  }
}"""

        logger.info("Calling OpenAI API to generate workout...")
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency, can change to "gpt-4" for better results
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a workout based on this request: {request.prompt}"}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}  # Force JSON response
        )
        
        # Extract JSON from response
        generated_text = response.choices[0].message.content
        logger.info(f"OpenAI generated response: {generated_text[:200]}...")  # Log first 200 chars
        
        # Parse JSON
        try:
            workout_json = json.loads(generated_text)
            logger.info("Successfully parsed JSON from OpenAI response")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}")
            logger.error(f"Response text: {generated_text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse JSON from OpenAI response: {str(e)}"
            )
        
        # Extract workout name and exercises from the format: {"Workout Name": {"Exercise": {...}}}
        # The workout name is the top-level key
        if len(workout_json) == 0:
            logger.error("Generated JSON is empty")
            raise HTTPException(status_code=500, detail="Generated JSON is empty")
        
        if len(workout_json) > 1:
            logger.warning(f"Generated JSON has multiple top-level keys: {list(workout_json.keys())}. Using the first one.")
        
        # Get the first (and should be only) top-level key as workout name
        workout_name = list(workout_json.keys())[0]
        exercises_dict = workout_json[workout_name]
        
        if not isinstance(exercises_dict, dict):
            logger.error(f"Workout '{workout_name}' value is not a dictionary of exercises")
            raise HTTPException(
                status_code=500,
                detail=f"Invalid structure: workout '{workout_name}' should contain a dictionary of exercises"
            )
        
        logger.info(f"Generated workout '{workout_name}' with {len(exercises_dict)} exercise(s)")
        
        # Convert to AddWorkoutRequest format
        exercises = {}
        for exercise_name, exercise_data in exercises_dict.items():
            try:
                # Validate exercise structure
                exercise = Exercise(**exercise_data)
                exercises[exercise_name] = exercise
            except Exception as e:
                logger.warning(f"Failed to validate exercise '{exercise_name}': {e}")
                # Try to create a minimal valid exercise
                exercises[exercise_name] = Exercise(
                    type=exercise_data.get("type", "repetition"),
                    description=exercise_data.get("description", "Exercise description"),
                    reps=exercise_data.get("reps"),
                    weight=exercise_data.get("weight"),
                    duration_sec=exercise_data.get("duration_sec"),
                    distance_m=exercise_data.get("distance_m"),
                    skill=exercise_data.get("skill")
                )
        
        # Create AddWorkoutRequest
        add_request = AddWorkoutRequest(
            workout_name=workout_name,
            exercises=exercises if exercises else None
        )
        
        # Add to database using existing logic
        logger.info(f"Adding generated workout '{workout_name}' to database...")
        
        if db is None:
            logger.error("Database connection is None - cannot add workout")
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        collection_name = get_collection_name()
        if collection_name is None:
            logger.error("No collections found in database")
            raise HTTPException(status_code=500, detail="No collections found in database")
        
        logger.info(f"Using collection: {collection_name}")
        collection = db[collection_name]
        
        # Check if workout already exists
        existing_doc_with_workout = collection.find_one({workout_name: {"$exists": True}})
        if existing_doc_with_workout:
            logger.warning(f"Workout '{workout_name}' already exists in database")
            raise HTTPException(
                status_code=400,
                detail=f"Workout '{workout_name}' already exists"
            )
        
        # Prepare workout data
        workout_data = {}
        if add_request.exercises:
            for exercise_name, exercise in add_request.exercises.items():
                exercise_dict = exercise.model_dump(exclude_none=True)
                workout_data[exercise_name] = exercise_dict
        
        # Get or create document
        existing_doc = collection.find_one({})
        
        if existing_doc:
            logger.info(f"Updating existing document with new workout '{workout_name}'")
            result = collection.update_one(
                {"_id": existing_doc["_id"]},
                {"$set": {workout_name: workout_data}}
            )
            if result.modified_count == 1:
                logger.info(f"Successfully added workout '{workout_name}' to existing document")
            else:
                logger.warning(f"Update operation didn't modify document. Modified count: {result.modified_count}")
        else:
            logger.info(f"Creating new document with workout '{workout_name}'")
            new_doc = {workout_name: workout_data}
            result = collection.insert_one(new_doc)
            if result.inserted_id:
                logger.info(f"Successfully created new document with workout '{workout_name}' (ID: {result.inserted_id})")
            else:
                logger.error("Failed to insert new document")
                raise HTTPException(status_code=500, detail="Failed to create new workout")
        
        return {
            "message": f"Successfully generated and added workout '{workout_name}'",
            "workout_name": workout_name,
            "exercises_count": len(workout_data),
            "generated_exercises": list(workout_data.keys())
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating workout: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate workout: {str(e)}")

@app.get("/users/{user_id}/weekly-overview", response_model=Dict[str, Any])
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
