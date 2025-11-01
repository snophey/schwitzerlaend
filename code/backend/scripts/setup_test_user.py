#!/usr/bin/env python3
"""
Setup script for creating test user "3" with a sample workout plan.

This script ensures user "3" exists and has a workout plan ready for testing
the history tracking system.

Usage:
    python scripts/setup_test_user.py
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
USER_ID = "3"

# Color codes for terminal output
class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    OKCYAN = '\033[96m'


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def create_or_verify_user(user_id: str) -> bool:
    """Create user if doesn't exist, or verify if exists."""
    print_info(f"Checking if user '{user_id}' exists...")
    
    # Try to get user
    try:
        response = requests.get(f"{BASE_URL}/users/{user_id}")
        if response.status_code == 200:
            print_success(f"User '{user_id}' already exists")
            return True
    except Exception:
        pass
    
    # User doesn't exist, create it
    print_info(f"Creating user '{user_id}'...")
    try:
        response = requests.post(f"{BASE_URL}/users/{user_id}")
        response.raise_for_status()
        print_success(f"Created user '{user_id}'")
        return True
    except Exception as e:
        print_error(f"Failed to create user: {str(e)}")
        return False


def get_sample_exercises() -> list:
    """Get some sample exercises from the database."""
    print_info("Fetching available exercises...")
    
    try:
        response = requests.get(f"{BASE_URL}/exercises?limit=20")
        response.raise_for_status()
        exercises = response.json()
        
        if not exercises:
            print_warning("No exercises found in database")
            print_info("Please run exercise import first, or the workout generation may fail")
            return []
        
        print_success(f"Found {len(exercises)} exercises")
        return exercises
    except Exception as e:
        print_error(f"Failed to get exercises: {str(e)}")
        return []


def create_workout_with_ai(user_id: str) -> bool:
    """Generate a workout using AI for the user."""
    print_info(f"Generating AI-powered workout for user '{user_id}'...")
    
    # Simple fitness prompt that should work with basic exercises
    prompt = "I want a 3-day beginner workout plan focusing on bodyweight exercises for full body strength"
    
    try:
        response = requests.post(
            f"{BASE_URL}/users/{user_id}/generate-workout",
            json={"prompt": prompt}
        )
        response.raise_for_status()
        result = response.json()
        
        workout_id = result.get('workout_id')
        workout_name = result.get('workout_name', 'Generated Workout')
        days = result.get('summary', {}).get('days', 0)
        
        print_success(f"Created workout: '{workout_name}'")
        print_success(f"Workout ID: {workout_id}")
        print_success(f"Days in plan: {days}")
        return True
        
    except requests.exceptions.HTTPError as e:
        print_error(f"Failed to generate workout: {e.response.status_code}")
        if e.response.status_code == 400:
            print_warning("This might be due to missing OpenAI API key")
            print_info("Set OPENAI_API_KEY environment variable or provide in request")
        return False
    except Exception as e:
        print_error(f"Failed to generate workout: {str(e)}")
        return False


def verify_user_has_workout(user_id: str) -> bool:
    """Verify user has at least one workout."""
    print_info(f"Verifying user '{user_id}' has workouts...")
    
    try:
        response = requests.get(f"{BASE_URL}/users/{user_id}")
        response.raise_for_status()
        user_data = response.json()
        
        workout_ids = user_data.get('associated_workout_ids', [])
        if workout_ids:
            print_success(f"User has {len(workout_ids)} workout(s)")
            return True
        else:
            print_warning(f"User '{user_id}' has no associated workouts")
            return False
            
    except Exception as e:
        print_error(f"Failed to verify user workouts: {str(e)}")
        return False


def main():
    """Main setup workflow."""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}Setting up test user for history tracking tests{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    print_info(f"Target User ID: {USER_ID}")
    print_info(f"API Base URL: {BASE_URL}\n")
    
    try:
        # Step 1: Create or verify user exists
        if not create_or_verify_user(USER_ID):
            print_error("Failed to create/verify user - aborting")
            return False
        
        # Step 2: Check if user already has workouts
        has_workout = verify_user_has_workout(USER_ID)
        
        if has_workout:
            print_success("\nUser is already set up and ready for testing!")
            print_info("You can now run: python scripts/test_history_workflow.py")
            return True
        
        # Step 3: Get available exercises
        exercises = get_sample_exercises()
        
        # Step 4: Generate a workout plan
        print(f"\n{Colors.BOLD}Generating workout plan...{Colors.ENDC}\n")
        if create_workout_with_ai(USER_ID):
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Setup complete!{Colors.ENDC}")
            print_info("User '3' is now ready for testing")
            print_info("Run: python scripts/test_history_workflow.py")
            return True
        else:
            print_error("\nFailed to generate workout")
            print_warning("You may need to:")
            print_warning("1. Set OPENAI_API_KEY environment variable")
            print_warning("2. Ensure exercises are loaded in the database")
            print_warning("3. Or manually create a workout for user '3'")
            return False
        
    except requests.exceptions.ConnectionError:
        print_error("\nCould not connect to API")
        print_info("Make sure the server is running: python main.py")
        return False
    except Exception as e:
        print_error(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
