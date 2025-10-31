from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os

# MongoDB Atlas connection configuration with X509 certificate authentication
CLUSTER_HOST = "cluster0.udio3ct.mongodb.net"
DATABASE_NAME = "schwitzerland"
CERTIFICATE_FILE = "secrets/X509-cert-7850383135344030658.pem"  # Path to your X509 certificate file

# Construct MongoDB Atlas connection string with X509 authentication
# authSource=$external (URL encoded as %24external) for X509 certificate authentication
MONGODB_URI = f"mongodb+srv://{CLUSTER_HOST}/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"

def connect_to_mongodb():
    """Connect to MongoDB using X509 certificate authentication."""
    try:
        # Check if certificate file exists
        if not os.path.exists(CERTIFICATE_FILE):
            print(f"Error: Certificate file '{CERTIFICATE_FILE}' not found.")
            print(f"Please ensure the certificate file is in the current directory: {os.getcwd()}")
            return None, None
        
        # Create MongoDB client with X509 certificate authentication
        client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsCertificateKeyFile=CERTIFICATE_FILE,
            serverSelectionTimeoutMS=10000
        )
        
        # Test connection
        client.admin.command('ping')
        print(f"Successfully connected to MongoDB Atlas using X509 certificate!")
        
        # Get database
        db = client[DATABASE_NAME]
        print(f"Connected to database: {DATABASE_NAME}")
        
        return client, db
    
    except FileNotFoundError:
        print(f"Error: Certificate file '{CERTIFICATE_FILE}' not found.")
        return None, None
    except ConnectionFailure:
        print("Failed to connect to MongoDB. Please check your certificate and connection settings.")
        return None, None
    except ServerSelectionTimeoutError:
        print("Server selection timeout. Please check your MongoDB connection settings.")
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def list_collections(db):
    """List all collections in the database."""
    if db is not None:
        collections = db.list_collection_names()
        print(f"\nCollections in database '{DATABASE_NAME}':")
        for collection_name in collections:
            print(f"  - {collection_name}")
        return collections
    return []

def query_collection(db, collection_name, query=None, limit=10):
    """Query documents from a collection."""
    if db is None:
        print("Database connection not available.")
        return []
    
    try:
        collection = db[collection_name]
        
        # If no query specified, use empty query to get all documents
        if query is None:
            query = {}
        
        # Execute query with limit
        documents = list(collection.find(query).limit(limit))
        
        print(f"\nFound {len(documents)} document(s) in collection '{collection_name}':")
        for doc in documents:
            print(doc)
        
        return documents
    
    except Exception as e:
        print(f"Error querying collection '{collection_name}': {e}")
        return []

def main():
    # Connect to MongoDB
    client, db = connect_to_mongodb()
    
    if db is None:
        return
    
    # List all collections
    collections = list_collections(db)
    
    # Example: Query from a collection
    # Replace 'your_collection_name' with the actual collection name you want to query
    if collections:
        # Query the first collection found
        query_collection(db, collections[0])
    else:
        print(f"\nNo collections found in database '{DATABASE_NAME}'.")
        print("Example: Query a collection named 'users'")
        # Uncomment the line below and replace 'users' with your collection name
        # query_collection(db, 'users')
    
    # Example: Query with a specific filter
    # query_collection(db, 'your_collection_name', query={"field": "value"})
    
    # Close connection
    if client:
        client.close()
        print("\nConnection closed.")

if __name__ == "__main__":
    main()

