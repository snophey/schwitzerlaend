"""Database connection configuration and utilities."""
import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# MongoDB configuration from environment variables
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "schwitzerland")
USE_LOCAL_MONGODB = os.getenv("USE_LOCAL_MONGODB", "true").lower() == "true"
CERTIFICATE_FILE = os.getenv("CERTIFICATE_FILE", "secrets/X509-cert-7850383135344030658.pem")

# Global database connection
db = None
client = None


def connect_to_mongodb():
    """Connect to MongoDB (local or Atlas with X509 certificate authentication)."""
    logger.info(f"Attempting to connect to MongoDB: {MONGODB_URI}")
    logger.info(f"Target database: {DATABASE_NAME}")
    logger.info(f"Using local MongoDB: {USE_LOCAL_MONGODB}")
    
    try:
        if USE_LOCAL_MONGODB:
            # Local MongoDB connection (no authentication)
            logger.info("Creating MongoDB client for local MongoDB...")
            client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=10000
            )
            logger.info("MongoDB client created successfully.")
        else:
            # MongoDB Atlas connection with X509 certificate authentication
            logger.info(f"Checking for certificate file: {CERTIFICATE_FILE}")
            if not os.path.exists(CERTIFICATE_FILE):
                logger.error(f"Certificate file '{CERTIFICATE_FILE}' not found in {os.getcwd()}")
                return None, None
            logger.info(f"Certificate file found: {CERTIFICATE_FILE}")
            
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
        logger.info("Successfully connected to MongoDB!")
        
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
        logger.error(f"Please check if MongoDB is running and accessible at {MONGODB_URI}")
        if USE_LOCAL_MONGODB:
            logger.error("For local development, make sure MongoDB is running on localhost:27017")
            logger.error("You can start it with: docker compose -f docker-compose.dev.yml up -d")
        return None, None
    except ServerSelectionTimeoutError as e:
        logger.error(f"Server selection timeout: {e}")
        logger.error(f"Could not reach MongoDB at {MONGODB_URI}")
        logger.error("Please check:")
        logger.error("1. Is MongoDB running?")
        logger.error("2. Is the connection string correct?")
        if USE_LOCAL_MONGODB:
            logger.error("3. For local dev, use: mongodb://localhost:27017/")
            logger.error("4. Start MongoDB: docker compose -f docker-compose.dev.yml up -d")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error occurred connecting to MongoDB: {e}", exc_info=True)
        logger.error(f"Connection string used: {MONGODB_URI}")
        logger.error(f"Local MongoDB mode: {USE_LOCAL_MONGODB}")
        return None, None


def get_database():
    """Get the database instance."""
    return db
