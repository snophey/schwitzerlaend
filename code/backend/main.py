"""FastAPI application entry point."""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

# Import database connection
from database import connect_to_mongodb, db as database_db, client as database_client
import database

# Import routers
from routers.users import router as users_router
from routers.workouts import router as workouts_router
from routers.sets import router as sets_router
from routers.exercises import router as exercises_router
from routers.history import router as history_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    logger.info("Starting up FastAPI application...")
    client, db = connect_to_mongodb()
    if db is None:
        logger.error("Failed to connect to MongoDB on startup - raising exception")
        raise Exception("Failed to connect to MongoDB on startup")
    
    # Set global database references
    database.db = db
    database.client = client
    
    logger.info("Application startup complete. MongoDB connection established.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    if database.client is not None:
        logger.info("Closing MongoDB connection...")
        database.client.close()
        logger.info("MongoDB connection closed.")
    logger.info("Application shutdown complete.")


# Create FastAPI application
app = FastAPI(
    title="Workouts API",
    description="""
    A comprehensive REST API for managing workout plans, exercises, sets, and users.
    
    ## Features
    
    * **User Management**: Create, retrieve, and delete users
    * **Workout Management**: Create, retrieve, and delete workout plans
    * **Set Management**: Create, retrieve, and delete exercise sets
    * **Exercise Management**: Create, retrieve, and delete exercises
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

# Include routers
app.include_router(users_router)
app.include_router(workouts_router)
app.include_router(sets_router)
app.include_router(exercises_router)
app.include_router(history_router)


@app.get("/")
async def root():
    """Root endpoint."""
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to the Workouts API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "users": "/users",
            "workouts": "/workouts",
            "sets": "/sets",
            "exercises": "/exercises",
            "history": "/history"
        }
    }
