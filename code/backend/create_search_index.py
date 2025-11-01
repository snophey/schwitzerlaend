#!/usr/bin/env python3
"""
Create MongoDB Atlas Search index for exercises collection.

This script creates a search index that enables full-text search on:
- name
- instructions
- primaryMuscles
- secondaryMuscles
- equipment
- category
"""

from pymongo import MongoClient
from pymongo.operations import SearchIndexModel
import os
import sys

# Import connection settings from connect.py
from connect import (
    MONGODB_URI,
    DATABASE_NAME,
    CERTIFICATE_FILE,
    CLUSTER_HOST
)

# Collection and index names
COLLECTION_NAME = "exercises"
SEARCH_INDEX_NAME = "exercises_prod"

def create_search_index():
    """Create a MongoDB Atlas Search index for the exercises collection."""
    
    # Check if certificate file exists
    if not os.path.exists(CERTIFICATE_FILE):
        print(f"❌ Error: Certificate file '{CERTIFICATE_FILE}' not found.")
        print(f"   Please ensure the certificate file is in: {os.getcwd()}")
        return False
    
    try:
        # Connect to MongoDB using X509 certificate authentication
        print("🔌 Connecting to MongoDB Atlas...")
        client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsCertificateKeyFile=CERTIFICATE_FILE,
            serverSelectionTimeoutMS=10000
        )
        
        # Test connection
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB Atlas")
        
        # Get database and collection
        database = client[DATABASE_NAME]
        collection = database[COLLECTION_NAME]
        
        print(f"📊 Database: {DATABASE_NAME}")
        print(f"📋 Collection: {COLLECTION_NAME}")
        
        # Check if collection exists and has documents
        doc_count = collection.count_documents({})
        print(f"📈 Documents in collection: {doc_count}")
        
        if doc_count == 0:
            print("⚠️  Warning: Collection is empty. The search index will still be created.")
        
        # Define the MongoDB Search index
        # Based on the fields used in get_started_llm.py:
        # paths_all = ["name","instructions","primaryMuscles","secondaryMuscles","equipment","category"]
        # 
        # Field structure in documents:
        # - name: single string (e.g., "90/90 Hamstring")
        # - instructions: array of strings (multiple steps/lines)
        # - primaryMuscles: array of strings (e.g., ["hamstrings"])
        # - secondaryMuscles: array of strings (e.g., ["calves"])
        # - equipment: single string (e.g., "body only")
        # - category: single string (e.g., "stretching")
        #
        # Note: MongoDB Atlas Search automatically handles arrays when using "string" type
        # - It will index all elements in an array for text search
        # - Multi-value fields work seamlessly with the search queries
        search_index_model = SearchIndexModel(
            definition={
                "mappings": {
                    "dynamic": False,  # Explicit field mapping for better control
                    "fields": {
                        "name": {
                            "type": "string",
                            "analyzer": "lucene.standard",
                            "searchAnalyzer": "lucene.standard"
                        },
                        "instructions": {
                            # Array of strings - automatically indexes all instruction steps
                            # Search will match across all elements in the array
                            "type": "string",
                            "analyzer": "lucene.standard",
                            "searchAnalyzer": "lucene.standard"
                        },
                        "primaryMuscles": {
                            # Array of strings - automatically indexes all muscle names
                            # Supports text search across all values in the array
                            "type": "string",
                            "analyzer": "lucene.standard",
                            "searchAnalyzer": "lucene.standard"
                        },
                        "secondaryMuscles": {
                            # Array of strings - automatically indexes all muscle names
                            # Supports text search across all values in the array
                            "type": "string",
                            "analyzer": "lucene.standard",
                            "searchAnalyzer": "lucene.standard"
                        },
                        "equipment": {
                            # Single string, but could be array - string type handles both
                            "type": "string",
                            "analyzer": "lucene.standard",
                            "searchAnalyzer": "lucene.standard"
                        },
                        "category": {
                            # Single string - full-text searchable
                            "type": "string",
                            "analyzer": "lucene.standard",
                            "searchAnalyzer": "lucene.standard"
                        }
                    }
                }
            },
            name=SEARCH_INDEX_NAME,
        )
        
        # Create the index
        print(f"\n🔨 Creating search index '{SEARCH_INDEX_NAME}'...")
        print("   This may take a few moments...")
        
        result = collection.create_search_index(model=search_index_model)
        print(f"✅ Search index created successfully!")
        print(f"   Index name: {result}")
        
        # Note: The index creation is asynchronous in Atlas
        # It may take a few minutes to fully build
        print(f"\nℹ️  Note: The index is being built asynchronously.")
        print(f"   It may take a few minutes to be ready for use.")
        
        # Wait a moment and then list indexes to show the result
        import time
        print(f"\n📋 Checking search indexes status...")
        time.sleep(2)  # Give it a moment
        
        indexes = list(collection.list_search_indexes())
        if indexes:
            print(f"\n📊 Current search indexes:")
            for idx in indexes:
                print(f"\n  ✅ Name: {idx.get('name', 'N/A')}")
                print(f"     Status: {idx.get('status', 'N/A')}")
                print(f"     Queryable: {idx.get('queryable', 'N/A')}")
                if 'id' in idx:
                    print(f"     ID: {idx['id']}")
                if 'latestDefinition' in idx:
                    defn = idx['latestDefinition']
                    if 'mappings' in defn and 'fields' in defn['mappings']:
                        fields = list(defn['mappings']['fields'].keys())
                        print(f"     Indexed fields: {', '.join(fields)}")
        
        print(f"\n💡 You can check the status in the MongoDB Atlas UI.")
        
        # Close connection
        client.close()
        print("\n🔌 Connection closed.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating search index: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_search_indexes():
    """List all search indexes for the exercises collection."""
    try:
        if not os.path.exists(CERTIFICATE_FILE):
            print(f"❌ Error: Certificate file '{CERTIFICATE_FILE}' not found.")
            return
        
        print("🔌 Connecting to MongoDB Atlas...")
        client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsCertificateKeyFile=CERTIFICATE_FILE,
            serverSelectionTimeoutMS=10000
        )
        
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB Atlas")
        
        database = client[DATABASE_NAME]
        collection = database[COLLECTION_NAME]
        
        print(f"\n📋 Search indexes for collection '{COLLECTION_NAME}':")
        indexes = list(collection.list_search_indexes())
        
        if indexes:
            for idx in indexes:
                print(f"\n  ✅ Name: {idx.get('name', 'N/A')}")
                print(f"     Status: {idx.get('status', 'N/A')}")
                print(f"     Queryable: {idx.get('queryable', 'N/A')}")
                if 'id' in idx:
                    print(f"     ID: {idx['id']}")
                if 'latestDefinition' in idx:
                    defn = idx['latestDefinition']
                    if 'mappings' in defn and 'fields' in defn['mappings']:
                        fields = list(defn['mappings']['fields'].keys())
                        print(f"     Indexed fields: {', '.join(fields)}")
        else:
            print("  (No search indexes found)")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error listing search indexes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create or list MongoDB Atlas Search indexes")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing search indexes instead of creating one"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_search_indexes()
    else:
        success = create_search_index()
        sys.exit(0 if success else 1)

