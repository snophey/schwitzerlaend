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
    type: str  # 'repetition', 'weighted repetition', 'time', 'distance'
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration_sec: Optional[int] = None
    distance_m: Optional[int] = None
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
            "DELETE /workouts/{workout_name}/exercises/{exercise_name} - Delete an exercise from a workout"
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
      "type": "repetition" | "weighted repetition" | "time" | "distance",
      "description": "Detailed description of how to perform the exercise",
      "reps": <number> (only if type is "repetition" or "weighted repetition"),
      "weight": <number> (only if type is "weighted repetition"),
      "duration_sec": <number> (only if type is "time"),
      "distance_m": <number> (only if type is "distance")
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
                    distance_m=exercise_data.get("distance_m")
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

