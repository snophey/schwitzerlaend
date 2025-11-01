from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
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
            "GET /workouts - Get all workout names",
            "POST /workouts - Add a new workout manually",
            "POST /workouts/generate - Generate a workout using AI from a prompt",
            "DELETE /workouts/{workout_name} - Delete an entire workout",
            "DELETE /workouts/{workout_name}/exercises/{exercise_name} - Delete an exercise from a workout",
            "GET /workouts/{workout_name}/exercises/count - Get the number of exercises for a workout",
            "GET /workouts/{workout_name}/exercises - Get all exercises for a workout",
            "GET /workouts/{workout_name}/exercises/{exercise_index} - Get a specific exercise by index (1-based)",
            "GET /workouts/dummy - Get a dummy weekly workout plan (7 days)",
            "GET /users/{user_id}/weekly-overview - Get weekly workout overview for a user"
        ]
    }

@app.get("/workouts", response_model=List[str])
async def get_workouts():
    """
    Get all workout names from the database.
    Returns a list of workout names like 'CrossFit', 'WeightLifting', etc.
    """
    logger.info("GET /workouts endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot query workouts")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Try to find a workouts collection or any collection with workout data
        logger.info("Listing all collections in database...")
        collections = db.list_collection_names()
        logger.info(f"Found {len(collections)} collection(s): {collections}")
        
        # Common collection names for workouts
        workout_collections = ['workouts', 'workout', 'exercises', 'training']
        logger.info(f"Searching for workout collections: {workout_collections}")
        
        # Find the workout collection
        collection_name = None
        for col in workout_collections:
            if col in collections:
                collection_name = col
                logger.info(f"Found matching collection: {collection_name}")
                break
        
        # If no specific workout collection found, try the first collection
        if collection_name is None and collections:
            collection_name = collections[0]
            logger.info(f"No specific workout collection found. Using first collection: {collection_name}")
        
        if collection_name is None:
            # If no collections found, return example data
            logger.warning("No collections found in database. Returning example workout data.")
            example_data = ["CrossFit", "WeightLifting", "Running", "Yoga", "Cycling"]
            logger.info(f"Returning {len(example_data)} example workouts")
            return example_data
        
        logger.info(f"Querying collection: {collection_name}")
        collection = db[collection_name]
        
        # Query for all documents (workout names are top-level keys in the document)
        logger.info("Executing query to find workout documents...")
        documents = list(collection.find({}).limit(10))
        logger.info(f"Query returned {len(documents)} document(s)")
        
        workout_names = []
        if documents:
            logger.info("Extracting workout names from document keys...")
            # Extract workout names from top-level document keys
            # The structure is: {workout_name: {exercises...}, workout_name2: {...}, ...}
            for i, doc in enumerate(documents):
                logger.debug(f"Document {i+1} keys: {list(doc.keys())}")
                # Get all keys except '_id' - these are the workout names
                for key in doc.keys():
                    if key != "_id":
                        # Check if the value is a dict (meaning it's a workout with exercises)
                        if isinstance(doc[key], dict):
                            workout_names.append(key)
                            logger.debug(f"Document {i+1}: Found workout '{key}' with {len(doc[key])} exercise(s)")
                        # Also check if it might be a simple field
                        elif key in ["name", "workout_name", "type"]:
                            workout_names.append(doc[key])
                            logger.debug(f"Document {i+1}: Found workout in '{key}' field: {doc[key]}")
            
            # Remove duplicates and sort
            workout_names = sorted(list(set(workout_names)))
            logger.info(f"Extracted {len(workout_names)} unique workout name(s): {workout_names}")
        
        # If no workout names found in database, return example data
        if not workout_names:
            logger.warning("No workout names found in database documents. Returning example data.")
            example_data = ["CrossFit", "WeightLifting", "Running", "Yoga", "Cycling", "Swimming", "Pilates", "HIIT"]
            logger.info(f"Returning {len(example_data)} example workouts")
            return example_data
        
        logger.info(f"Successfully returning {len(workout_names)} workout name(s) from database")
        return workout_names
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying workouts: {e}", exc_info=True)
        logger.warning("Returning example data due to error")
        # Return example data if database query fails
        example_data = ["CrossFit", "WeightLifting", "Running", "Yoga", "Cycling", "Swimming", "Pilates", "HIIT"]
        logger.info(f"Returning {len(example_data)} example workouts")
        return example_data

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

@app.post("/workouts", response_model=Dict[str, Any])
async def add_workout(request: AddWorkoutRequest):
    """
    Add a new workout type to the database.
    
    - **workout_name**: Name of the workout (e.g., "Yoga", "Running")
    - **exercises**: Optional dictionary of exercises for this workout
    
    Example request body:
    ```json
    {
        "workout_name": "Yoga",
        "exercises": {
            "Downward Dog": {
                "type": "time",
                "duration_sec": 60,
                "description": "Hold downward dog pose for 60 seconds"
            },
            "Sun Salutation": {
                "type": "repetition",
                "reps": 5,
                "description": "Complete 5 rounds of sun salutation"
            }
        }
    }
    ```
    """
    logger.info(f"POST /workouts endpoint called with workout_name: '{request.workout_name}'")
    
    if db is None:
        logger.error("Database connection is None - cannot add workout")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        collection_name = get_collection_name()
        if collection_name is None:
            logger.error("No collections found in database")
            raise HTTPException(status_code=500, detail="No collections found in database")
        
        logger.info(f"Using collection: {collection_name}")
        collection = db[collection_name]
        
        # Check if workout already exists in any document
        existing_doc_with_workout = collection.find_one({request.workout_name: {"$exists": True}})
        if existing_doc_with_workout:
            logger.warning(f"Workout '{request.workout_name}' already exists in database")
            raise HTTPException(
                status_code=400,
                detail=f"Workout '{request.workout_name}' already exists"
            )
        
        # Prepare the workout data
        workout_data = {}
        if request.exercises:
            # Convert Pydantic models to dict
            for exercise_name, exercise in request.exercises.items():
                exercise_dict = exercise.model_dump(exclude_none=True)
                workout_data[exercise_name] = exercise_dict
            logger.info(f"Adding workout '{request.workout_name}' with {len(workout_data)} exercise(s)")
        else:
            logger.info(f"Adding workout '{request.workout_name}' with no exercises (empty workout)")
            workout_data = {}
        
        # Get or create a document to update
        # Check if there's an existing document in the collection
        existing_doc = collection.find_one({})
        
        if existing_doc:
            # Update existing document by adding the new workout as a top-level field
            logger.info(f"Updating existing document with new workout '{request.workout_name}'")
            result = collection.update_one(
                {"_id": existing_doc["_id"]},
                {"$set": {request.workout_name: workout_data}}
            )
            if result.modified_count == 1:
                logger.info(f"Successfully added workout '{request.workout_name}' to existing document")
            else:
                logger.warning(f"Update operation didn't modify document. Modified count: {result.modified_count}")
        else:
            # Create a new document with the workout
            logger.info(f"Creating new document with workout '{request.workout_name}'")
            new_doc = {request.workout_name: workout_data}
            result = collection.insert_one(new_doc)
            if result.inserted_id:
                logger.info(f"Successfully created new document with workout '{request.workout_name}' (ID: {result.inserted_id})")
            else:
                logger.error("Failed to insert new document")
                raise HTTPException(status_code=500, detail="Failed to create new workout")
        
        return {
            "message": f"Successfully added workout '{request.workout_name}'",
            "workout_name": request.workout_name,
            "exercises_count": len(workout_data) if request.exercises else 0
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding workout '{request.workout_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add workout: {str(e)}")

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

@app.get("/workouts/{workout_name}/exercises/count", response_model=Dict[str, Any])
async def get_workout_exercise_count(workout_name: str):
    """
    Get the number of exercises for a specific workout.
    
    - **workout_name**: Name of the workout (e.g., "CrossFit", "Yoga")
    
    Returns the count of exercises in the workout.
    """
    logger.info(f"GET /workouts/{workout_name}/exercises/count endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot get exercise count")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        collection_name = get_collection_name()
        if collection_name is None:
            logger.error("No collections found in database")
            raise HTTPException(status_code=500, detail="No collections found in database")
        
        logger.info(f"Using collection: {collection_name}")
        collection = db[collection_name]
        
        # Check if workout exists
        existing_doc = collection.find_one({workout_name: {"$exists": True}})
        if not existing_doc:
            logger.warning(f"Workout '{workout_name}' not found in database")
            raise HTTPException(
                status_code=404,
                detail=f"Workout '{workout_name}' not found"
            )
        
        # Get workout data
        workout_data = existing_doc.get(workout_name, {})
        if not isinstance(workout_data, dict):
            logger.error(f"Workout '{workout_name}' does not contain exercises dictionary")
            raise HTTPException(
                status_code=500,
                detail=f"Workout '{workout_name}' has invalid structure"
            )
        
        exercise_count = len(workout_data)
        logger.info(f"Workout '{workout_name}' has {exercise_count} exercise(s)")
        
        return {
            "workout_name": workout_name,
            "exercise_count": exercise_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exercise count for workout '{workout_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get exercise count: {str(e)}")

@app.get("/workouts/{workout_name}/exercises", response_model=Dict[str, Any])
async def get_workout_exercises(workout_name: str):
    """
    Get all exercises for a specific workout.
    
    - **workout_name**: Name of the workout (e.g., "CrossFit", "Yoga")
    
    Returns all exercises in the workout with their names and details.
    """
    logger.info(f"GET /workouts/{workout_name}/exercises endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot get exercises")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        collection_name = get_collection_name()
        if collection_name is None:
            logger.error("No collections found in database")
            raise HTTPException(status_code=500, detail="No collections found in database")
        
        logger.info(f"Using collection: {collection_name}")
        collection = db[collection_name]
        
        # Check if workout exists
        existing_doc = collection.find_one({workout_name: {"$exists": True}})
        if not existing_doc:
            logger.warning(f"Workout '{workout_name}' not found in database")
            raise HTTPException(
                status_code=404,
                detail=f"Workout '{workout_name}' not found"
            )
        
        # Get workout data
        workout_data = existing_doc.get(workout_name, {})
        if not isinstance(workout_data, dict):
            logger.error(f"Workout '{workout_name}' does not contain exercises dictionary")
            raise HTTPException(
                status_code=500,
                detail=f"Workout '{workout_name}' has invalid structure"
            )
        
        logger.info(f"Found {len(workout_data)} exercise(s) for workout '{workout_name}'")
        
        return {
            "workout_name": workout_name,
            "exercise_count": len(workout_data),
            "exercises": workout_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exercises for workout '{workout_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get exercises: {str(e)}")

@app.get("/workouts/{workout_name}/exercises/{exercise_index}", response_model=Dict[str, Any])
async def get_workout_exercise_by_index(workout_name: str, exercise_index: int):
    """
    Get a specific exercise from a workout by its index (1-based).
    
    - **workout_name**: Name of the workout (e.g., "CrossFit", "Yoga")
    - **exercise_index**: Index of the exercise (1-based, so 1 = first exercise, 2 = second exercise, etc.)
    
    Returns the exercise at the specified index along with its name.
    """
    logger.info(f"GET /workouts/{workout_name}/exercises/{exercise_index} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot get exercise")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Validate index
        if exercise_index < 1:
            logger.warning(f"Invalid exercise index: {exercise_index} (must be >= 1)")
            raise HTTPException(
                status_code=400,
                detail="Exercise index must be >= 1 (1-based indexing)"
            )
        
        collection_name = get_collection_name()
        if collection_name is None:
            logger.error("No collections found in database")
            raise HTTPException(status_code=500, detail="No collections found in database")
        
        logger.info(f"Using collection: {collection_name}")
        collection = db[collection_name]
        
        # Check if workout exists
        existing_doc = collection.find_one({workout_name: {"$exists": True}})
        if not existing_doc:
            logger.warning(f"Workout '{workout_name}' not found in database")
            raise HTTPException(
                status_code=404,
                detail=f"Workout '{workout_name}' not found"
            )
        
        # Get workout data
        workout_data = existing_doc.get(workout_name, {})
        if not isinstance(workout_data, dict):
            logger.error(f"Workout '{workout_name}' does not contain exercises dictionary")
            raise HTTPException(
                status_code=500,
                detail=f"Workout '{workout_name}' has invalid structure"
            )
        
        # Convert to list to maintain order (Python 3.7+ preserves insertion order)
        exercises_list = list(workout_data.items())
        
        if exercise_index > len(exercises_list):
            logger.warning(f"Exercise index {exercise_index} exceeds number of exercises ({len(exercises_list)})")
            raise HTTPException(
                status_code=404,
                detail=f"Exercise index {exercise_index} not found. Workout '{workout_name}' has {len(exercises_list)} exercise(s)"
            )
        
        # Get exercise at index (convert from 1-based to 0-based)
        exercise_name, exercise_data = exercises_list[exercise_index - 1]
        logger.info(f"Found exercise at index {exercise_index}: '{exercise_name}'")
        
        return {
            "workout_name": workout_name,
            "exercise_index": exercise_index,
            "exercise_name": exercise_name,
            "exercise": exercise_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exercise at index {exercise_index} for workout '{workout_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get exercise: {str(e)}")

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

@app.get("/workouts/dummy", response_model=List[Dict[str, Any]])
async def get_dummy_workout_plan():
    """
    Get a dummy weekly workout plan with 7 entries (one for each weekday).
    
    Each day can either:
    - Be empty (no training): exercises will be an empty list
    - Contain a list of exercises: exercises will be a list of exercise JSON objects
    
    Returns a list of 7 entries representing Monday through Sunday.
    """
    logger.info("GET /workout-plan/dummy endpoint called")
    
    try:
        # Create a dummy workout plan for 7 days
        workout_plan = [
            {
                "day": "Monday",
                "day_number": 1,
                "exercises": [
                    {
                        "name": "Push-ups",
                        "type": "repetition",
                        "reps": 15,
                        "description": "Perform 15 push-ups with proper form"
                    },
                    {
                        "name": "Pull-ups",
                        "type": "repetition",
                        "reps": 10,
                        "description": "Complete 10 pull-ups or assisted pull-ups"
                    },
                    {
                        "name": "Plank",
                        "type": "time",
                        "duration_sec": 60,
                        "description": "Hold plank position for 60 seconds"
                    },
                    {
                        "name": "Bench Press",
                        "type": "weighted repetition",
                        "reps": 8,
                        "weight": 75.0,
                        "description": "Perform 8 reps of bench press with 75kg load"
                    }
                ]
            },
            {
                "day": "Tuesday",
                "day_number": 2,
                "exercises": [
                    {
                        "name": "Cool Down Stretch",
                        "type": "time",
                        "duration_sec": 300,
                        "description": "Stretch for 5 minutes after running"
                    },
                    {
                        "name": "Kickflip",
                        "type": "skill",
                        "reps": 20,
                        "description": "Just dooo it !!"
                    }
                ]
            },
            {
                "day": "Wednesday",
                "day_number": 3,
                "exercises": [
                    {
                        "name": "Squats",
                        "type": "repetition",
                        "reps": 20,
                        "description": "Perform 20 bodyweight squats"
                    },
                    {
                        "name": "Lunges",
                        "type": "repetition",
                        "reps": 12,
                        "description": "Do 12 lunges on each leg"
                    },
                    {
                        "name": "Leg Raises",
                        "type": "repetition",
                        "reps": 15,
                        "description": "Complete 15 leg raises"
                    }
                ]
            },
            {
                "day": "Thursday",
                "day_number": 4,
                "exercises": []  # Rest day / No training
            },
            {
                "day": "Friday",
                "day_number": 5,
                "exercises": [
                    {
                        "name": "Bench Press",
                        "type": "weighted repetition",
                        "reps": 10,
                        "weight": 80.0,
                        "description": "Perform 10 reps of bench press with 80kg"
                    },
                    {
                        "name": "Deadlift",
                        "type": "weighted repetition",
                        "reps": 8,
                        "weight": 100.0,
                        "description": "Complete 8 reps of deadlift with 100kg"
                    },
                    {
                        "name": "Barbell Rows",
                        "type": "weighted repetition",
                        "reps": 12,
                        "weight": 60.0,
                        "description": "Do 12 reps of barbell rows with 60kg"
                    }
                ]
            },
            {
                "day": "Saturday",
                "day_number": 6,
                "exercises": [
                    {
                        "name": "Yoga Flow",
                        "type": "time",
                        "duration_sec": 1800,
                        "description": "Complete a 30-minute yoga flow session"
                    },
                    {
                        "name": "Meditation",
                        "type": "time",
                        "duration_sec": 600,
                        "description": "Meditate for 10 minutes"
                    }
                ]
            },
            {
                "day": "Sunday",
                "day_number": 7,
                "exercises": []  # Rest day / No training
            }
        ]
        
        logger.info(f"Returning dummy workout plan with {len(workout_plan)} days")
        return workout_plan
    
    except Exception as e:
        logger.error(f"Error generating dummy workout plan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate dummy workout plan: {str(e)}")

@app.delete("/workouts/{workout_name}", response_model=Dict[str, Any])
async def delete_workout(workout_name: str):
    """
    Delete an entire workout from the database.
    
    - **workout_name**: Name of the workout to delete (e.g., "CrossFit", "Yoga")
    """
    logger.info(f"DELETE /workouts/{workout_name} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot delete workout")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        collection_name = get_collection_name()
        if collection_name is None:
            logger.error("No collections found in database")
            raise HTTPException(status_code=500, detail="No collections found in database")
        
        logger.info(f"Using collection: {collection_name}")
        collection = db[collection_name]
        
        # Check if workout exists
        existing_doc = collection.find_one({workout_name: {"$exists": True}})
        if not existing_doc:
            logger.warning(f"Workout '{workout_name}' not found in database")
            raise HTTPException(
                status_code=404,
                detail=f"Workout '{workout_name}' not found"
            )
        
        logger.info(f"Deleting workout '{workout_name}' from document")
        
        # Remove the workout field from the document
        result = collection.update_one(
            {"_id": existing_doc["_id"]},
            {"$unset": {workout_name: ""}}
        )
        
        if result.modified_count == 1:
            logger.info(f"Successfully deleted workout '{workout_name}'")
        else:
            logger.warning(f"Delete operation didn't modify document. Modified count: {result.modified_count}")
            # Workout might not exist even though find_one returned a doc
            raise HTTPException(
                status_code=404,
                detail=f"Workout '{workout_name}' not found in document"
            )
        
        return {
            "message": f"Successfully deleted workout '{workout_name}'",
            "workout_name": workout_name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workout '{workout_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete workout: {str(e)}")

@app.delete("/workouts/{workout_name}/exercises/{exercise_name}", response_model=Dict[str, Any])
async def delete_exercise(workout_name: str, exercise_name: str):
    """
    Delete a specific exercise from a workout.
    
    - **workout_name**: Name of the workout (e.g., "CrossFit", "Yoga")
    - **exercise_name**: Name of the exercise to delete (e.g., "Pull-ups", "Downward Dog")
    """
    logger.info(f"DELETE /workouts/{workout_name}/exercises/{exercise_name} endpoint called")
    
    if db is None:
        logger.error("Database connection is None - cannot delete exercise")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        collection_name = get_collection_name()
        if collection_name is None:
            logger.error("No collections found in database")
            raise HTTPException(status_code=500, detail="No collections found in database")
        
        logger.info(f"Using collection: {collection_name}")
        collection = db[collection_name]
        
        # Check if workout exists
        existing_doc = collection.find_one({workout_name: {"$exists": True}})
        if not existing_doc:
            logger.warning(f"Workout '{workout_name}' not found in database")
            raise HTTPException(
                status_code=404,
                detail=f"Workout '{workout_name}' not found"
            )
        
        # Check if exercise exists in the workout
        workout_data = existing_doc.get(workout_name, {})
        if not isinstance(workout_data, dict):
            logger.error(f"Workout '{workout_name}' does not contain exercises dictionary")
            raise HTTPException(
                status_code=500,
                detail=f"Workout '{workout_name}' has invalid structure"
            )
        
        if exercise_name not in workout_data:
            logger.warning(f"Exercise '{exercise_name}' not found in workout '{workout_name}'")
            raise HTTPException(
                status_code=404,
                detail=f"Exercise '{exercise_name}' not found in workout '{workout_name}'"
            )
        
        logger.info(f"Deleting exercise '{exercise_name}' from workout '{workout_name}'")
        
        # Remove the exercise from the workout using dot notation
        result = collection.update_one(
            {"_id": existing_doc["_id"]},
            {"$unset": {f"{workout_name}.{exercise_name}": ""}}
        )
        
        if result.modified_count == 1:
            logger.info(f"Successfully deleted exercise '{exercise_name}' from workout '{workout_name}'")
        else:
            logger.warning(f"Delete operation didn't modify document. Modified count: {result.modified_count}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete exercise '{exercise_name}' from workout '{workout_name}'"
            )
        
        return {
            "message": f"Successfully deleted exercise '{exercise_name}' from workout '{workout_name}'",
            "workout_name": workout_name,
            "exercise_name": exercise_name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting exercise '{exercise_name}' from workout '{workout_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete exercise: {str(e)}")

