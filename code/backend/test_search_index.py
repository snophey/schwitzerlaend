#!/usr/bin/env python3
"""
Test MongoDB Atlas Search index with various queries.

Usage:
  python test_search_index.py "hamstring stretch"
  python test_search_index.py --name "90/90"
  python test_search_index.py --equipment "body only"
  python test_search_index.py --category "stretching"
  python test_search_index.py --muscle "hamstrings"
  python test_search_index.py --all  # Run all test queries
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
import sys
import json
import argparse

# Import connection settings from connect.py
from connect import (
    MONGODB_URI,
    DATABASE_NAME,
    CERTIFICATE_FILE,
)

# Collection and index names
COLLECTION_NAME = "exercises"
SEARCH_INDEX_NAME = "exercises_prod"

# Fields that can be searched
SEARCH_PATHS = ["name", "instructions", "primaryMuscles", "secondaryMuscles", "equipment", "category"]


def connect_to_mongodb():
    """Connect to MongoDB using X509 certificate authentication."""
    try:
        if not os.path.exists(CERTIFICATE_FILE):
            print(f"❌ Error: Certificate file '{CERTIFICATE_FILE}' not found.")
            return None, None, None

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

        return client, database, collection

    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def check_index_status(collection):
    """Check if the search index is ready."""
    try:
        indexes = list(collection.list_search_indexes())
        for idx in indexes:
            if idx.get('name') == SEARCH_INDEX_NAME:
                status = idx.get('status', 'UNKNOWN')
                queryable = idx.get('queryable', False)
                print(f"\n📊 Search index '{SEARCH_INDEX_NAME}':")
                print(f"   Status: {status}")
                print(f"   Queryable: {queryable}")
                return queryable
        print(f"⚠️  Search index '{SEARCH_INDEX_NAME}' not found")
        return False
    except Exception as e:
        print(f"⚠️  Could not check index status: {e}")
        return True  # Assume it's ready if we can't check


def search_all_fields(collection, query_text, limit=10):
    """Search across all fields."""
    pipeline = [
        {
            "$search": {
                "index": SEARCH_INDEX_NAME,
                "text": {
                    "query": query_text,
                    "path": SEARCH_PATHS,
                    "fuzzy": {"maxEdits": 2, "prefixLength": 2}
                }
            }
        },
        {
            "$project": {
                "_id": 1,
                "name": 1,
                "category": 1,
                "equipment": 1,
                "primaryMuscles": 1,
                "score": {"$meta": "searchScore"}
            }
        },
        {"$sort": {"score": -1}},
        {"$limit": limit}
    ]
    return list(collection.aggregate(pipeline))


def search_by_field(collection, query_text, field, limit=10):
    """Search in a specific field."""
    pipeline = [
        {
            "$search": {
                "index": SEARCH_INDEX_NAME,
                "text": {
                    "query": query_text,
                    "path": field
                }
            }
        },
        {
            "$project": {
                "_id": 1,
                "name": 1,
                field: 1,
                "score": {"$meta": "searchScore"}
            }
        },
        {"$sort": {"score": -1}},
        {"$limit": limit}
    ]
    return list(collection.aggregate(pipeline))


def search_with_filters(collection, query_text, filters=None, limit=10):
    """Search with filters (equipment, category, muscles, etc.)."""
    must = []
    filter_clauses = []

    if query_text:
        must.append({
            "text": {
                "query": query_text,
                "path": SEARCH_PATHS,
                "fuzzy": {"maxEdits": 2, "prefixLength": 2}
            }
        })

    if filters:
        for field, values in filters.items():
            if values:
                filter_clauses.append({
                    "text": {
                        "query": values,
                        "path": field
                    }
                })

    compound = {}
    if must:
        compound["must"] = must
    if filter_clauses:
        compound["filter"] = filter_clauses

    if not compound:
        compound = {"must": [{"text": {"query": "", "path": SEARCH_PATHS}}]}

    pipeline = [
        {
            "$search": {
                "index": SEARCH_INDEX_NAME,
                "compound": compound
            }
        },
        {
            "$project": {
                "_id": 1,
                "name": 1,
                "category": 1,
                "equipment": 1,
                "primaryMuscles": 1,
                "secondaryMuscles": 1,
                "score": {"$meta": "searchScore"}
            }
        },
        {"$sort": {"score": -1}},
        {"$limit": limit}
    ]
    return list(collection.aggregate(pipeline))


def display_results(results, title="Search Results"):
    """Display search results in a readable format."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")
    
    if not results:
        print("❌ No results found")
        return

    print(f"📊 Found {len(results)} result(s):\n")
    
    for i, doc in enumerate(results, 1):
        print(f"{i}. {doc.get('name', 'Unknown')} (ID: {doc.get('_id', 'N/A')})")
        print(f"   Score: {doc.get('score', 0):.4f}")
        
        if 'category' in doc:
            print(f"   Category: {doc['category']}")
        if 'equipment' in doc:
            print(f"   Equipment: {doc['equipment']}")
        if 'primaryMuscles' in doc:
            muscles = doc['primaryMuscles']
            if isinstance(muscles, list):
                print(f"   Primary Muscles: {', '.join(muscles)}")
            else:
                print(f"   Primary Muscles: {muscles}")
        if 'secondaryMuscles' in doc:
            muscles = doc['secondaryMuscles']
            if isinstance(muscles, list):
                print(f"   Secondary Muscles: {', '.join(muscles)}")
            else:
                print(f"   Secondary Muscles: {muscles}")
        print()


def run_all_tests(collection):
    """Run a suite of test queries."""
    print("\n" + "="*60)
    print("🧪 Running All Test Queries")
    print("="*60)

    tests = [
        ("Search: 'hamstring'", lambda: search_all_fields(collection, "hamstring", limit=5)),
        ("Search: 'push up'", lambda: search_all_fields(collection, "push up", limit=5)),
        ("Search by name: '90'", lambda: search_by_field(collection, "90", "name", limit=5)),
        ("Search by equipment: 'body only'", lambda: search_by_field(collection, "body only", "equipment", limit=5)),
        ("Search by category: 'stretching'", lambda: search_by_field(collection, "stretching", "category", limit=5)),
        ("Search with filter: equipment='body only'", 
         lambda: search_with_filters(collection, "", {"equipment": "body only"}, limit=5)),
        ("Search: 'triceps' + filter category='strength'", 
         lambda: search_with_filters(collection, "triceps", {"category": "strength"}, limit=5)),
    ]

    for test_name, test_func in tests:
        try:
            results = test_func()
            display_results(results, test_name)
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed: {e}")
            import traceback
            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Test MongoDB Atlas Search index")
    parser.add_argument("query", nargs="?", help="Text to search for (across all fields)")
    parser.add_argument("--name", type=str, help="Search in name field only")
    parser.add_argument("--equipment", type=str, help="Search in equipment field only")
    parser.add_argument("--category", type=str, help="Search in category field only")
    parser.add_argument("--muscle", type=str, help="Search for primary/secondary muscles")
    parser.add_argument("--filter-equipment", type=str, help="Filter by equipment")
    parser.add_argument("--filter-category", type=str, help="Filter by category")
    parser.add_argument("--all", action="store_true", help="Run all test queries")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    client, database, collection = connect_to_mongodb()
    if collection is None:
        sys.exit(1)

    # Check index status
    if not check_index_status(collection):
        print("\n⚠️  Warning: Index may not be ready yet. Queries might fail.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            client.close()
            sys.exit(0)

    try:
        results = None

        if args.all:
            run_all_tests(collection)
        elif args.name:
            results = search_by_field(collection, args.name, "name", limit=args.limit)
            display_results(results, f"Search by name: '{args.name}'")
        elif args.equipment:
            results = search_by_field(collection, args.equipment, "equipment", limit=args.limit)
            display_results(results, f"Search by equipment: '{args.equipment}'")
        elif args.category:
            results = search_by_field(collection, args.category, "category", limit=args.limit)
            display_results(results, f"Search by category: '{args.category}'")
        elif args.muscle:
            # Search in both primary and secondary muscles
            filters = {"primaryMuscles": args.muscle}
            results = search_with_filters(collection, "", filters, limit=args.limit)
            display_results(results, f"Search by muscle: '{args.muscle}'")
        elif args.query or args.filter_equipment or args.filter_category:
            filters = {}
            if args.filter_equipment:
                filters["equipment"] = args.filter_equipment
            if args.filter_category:
                filters["category"] = args.filter_category
            query_text = args.query or ""
            results = search_with_filters(collection, query_text, filters, limit=args.limit)
            title = f"Search: '{query_text}'"
            if filters:
                title += f" with filters: {filters}"
            display_results(results, title)
        else:
            parser.print_help()
            print("\n❌ Please provide a query or use --all to run tests")

        if args.json and results:
            print("\n📄 JSON Output:")
            print(json.dumps(results, indent=2, default=str))

    except Exception as e:
        print(f"\n❌ Error during search: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if client:
            client.close()
            print("\n🔌 Connection closed.")


if __name__ == "__main__":
    main()

