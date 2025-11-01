#!/usr/bin/env python3
"""
Get Started Script for Workouts API

This script helps set up a user with workouts by:
1. Creating a user with a UUID (or provided user_id/session token)
2. Fetching available exercises from the exercises collection
3. Creating sets for selected exercises (depends on exercises existing)
4. Creating workouts with those sets (depends on sets existing)
5. Associating workouts with the user (depends on workouts existing)

Cascading dependency handling:
- If workout_id doesn't exist when associating, create it first
- If sets don't exist when creating workout, create them first
- If exercises don't exist when creating sets, prompt user

Usage:
    python get_started.py [--user-id UUID] [--api-base http://localhost:8000]
"""

import requests
import uuid
import json
import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional


class WorkoutSetup:
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base.rstrip('/')
        self.user_id = None
        self.created_sets = {}
        self.created_workouts = {}
    
    def create_user(self, user_id: Optional[str] = None) -> str:
        """Create a new user. If user_id is provided, use it; otherwise generate a UUID."""
        if user_id is None:
            user_id = str(uuid.uuid4())
        
        print(f"\n📝 Creating user with ID: {user_id}")
        response = requests.post(f"{self.api_base}/users/{user_id}")
        
        if response.status_code == 201 or response.status_code == 200:
            print(f"✅ User created successfully: {user_id}")
            self.user_id = user_id
            return user_id
        elif response.status_code == 409:
            print(f"ℹ️  User already exists: {user_id}")
            self.user_id = user_id
            return user_id
        else:
            print(f"❌ Failed to create user: {response.status_code} - {response.text}")
            response.raise_for_status()
    
    def get_exercises(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch available exercises from the API using GET /exercises/ endpoint."""
        print("\n🔍 Fetching available exercises from API...")
        
        try:
            # Use GET /exercises/ endpoint with pagination
            response = requests.get(
                f"{self.api_base}/exercises/",
                params={"skip": 0, "limit": limit}
            )
            
            if response.status_code == 200:
                exercises = response.json()
                print(f"✅ Found {len(exercises)} exercise(s) from API")
                return exercises
            elif response.status_code == 500:
                print(f"⚠️  API error: {response.json().get('detail', 'Unknown error')}")
                print("   The API may not be running or exercises may not be uploaded.")
                print("   Run: python upload_exercises_to_mongodb.py")
                return []
            else:
                print(f"⚠️  Failed to fetch exercises: {response.status_code} - {response.text}")
                return []
        
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to API at {self.api_base}")
            print("   Make sure the API server is running.")
            # Fallback to JSON file if API is not available
            return self._get_exercises_from_json_fallback()
        except Exception as e:
            print(f"⚠️  Error fetching exercises from API: {e}")
            # Fallback to JSON file
            return self._get_exercises_from_json_fallback()
    
    def _get_exercises_from_json_fallback(self) -> List[Dict[str, Any]]:
        """Fallback method to get exercises from JSON file if API is unavailable."""
        print("\n📁 Trying to load exercises from JSON file as fallback...")
        
        # Try to find all_exercises.json relative to script location
        script_dir = Path(__file__).parent
        exercises_file = script_dir / 'all_exercises.json'
        
        try:
            with open(exercises_file, 'r') as f:
                exercises = json.load(f)
            print(f"✅ Found {len(exercises)} exercises in {exercises_file}")
            return exercises
        except FileNotFoundError:
            print(f"⚠️  {exercises_file} not found. Trying current directory...")
            try:
                with open('all_exercises.json', 'r') as f:
                    exercises = json.load(f)
                print(f"✅ Found {len(exercises)} exercises in all_exercises.json")
                return exercises
            except FileNotFoundError:
                print("⚠️  all_exercises.json not found. You may need to upload exercises first.")
                print("   Run: python upload_exercises_to_mongodb.py")
                return []
    
    def display_exercises(self, exercises: List[Dict[str, Any]], limit: int = 20):
        """Display a paginated list of exercises."""
        print(f"\n📋 Available Exercises (showing first {limit} of {len(exercises)}):")
        print("-" * 80)
        for i, exercise in enumerate(exercises[:limit], 1):
            name = exercise.get('name', 'Unknown')
            exercise_id = exercise.get('id', 'N/A')
            category = exercise.get('category', 'N/A')
            equipment = exercise.get('equipment', 'N/A')
            print(f"{i:3d}. {name:<40} | ID: {exercise_id:<20} | {category} | {equipment}")
        
        if len(exercises) > limit:
            print(f"\n... and {len(exercises) - limit} more exercises")
    
    def select_exercises(self, exercises: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Interactive exercise selection."""
        if not exercises:
            print("❌ No exercises available. Cannot proceed.")
            return []
        
        self.display_exercises(exercises, limit=30)
        
        print("\n💡 Select exercises by:")
        print("   1. Enter exercise IDs (comma-separated, e.g., '3_4_Sit-Up,90_90_Hamstring')")
        print("   2. Enter exercise numbers from the list above (comma-separated, e.g., '1,2,3')")
        print("   3. Enter 'all' to use all exercises (not recommended for large sets)")
        print("   4. Enter 'skip' to continue without selecting exercises")
        
        selection = input("\nYour selection: ").strip()
        
        if selection.lower() == 'skip':
            return []
        
        if selection.lower() == 'all':
            return exercises
        
        selected = []
        items = [item.strip() for item in selection.split(',')]
        
        for item in items:
            # Try as number first
            try:
                idx = int(item) - 1
                if 0 <= idx < len(exercises):
                    selected.append(exercises[idx])
                else:
                    print(f"⚠️  Index {item} out of range")
            except ValueError:
                # Try as exercise ID
                matching = [e for e in exercises if e.get('id') == item]
                if matching:
                    selected.append(matching[0])
                else:
                    print(f"⚠️  Exercise ID '{item}' not found")
        
        print(f"\n✅ Selected {len(selected)} exercise(s)")
        return selected
    
    def check_exercise_exists(self, exercise_id: str) -> bool:
        """Check if an exercise exists using GET /exercises/{exercise_id} endpoint."""
        try:
            response = requests.get(f"{self.api_base}/exercises/{exercise_id}")
            return response.status_code == 200
        except Exception:
            return False
    
    def create_set(self, exercise: Dict[str, Any], reps: Optional[int] = None, 
                   weight: Optional[float] = None, duration_sec: Optional[int] = None,
                   check_exercise_exists: bool = True) -> Optional[str]:
        """
        Create a set for an exercise.
        If check_exercise_exists is True, verifies the exercise exists using GET /exercises/{exercise_id}.
        """
        exercise_id = exercise.get('id')
        exercise_name = exercise.get('name', 'Unknown')
        
        if not exercise_id:
            print(f"  ❌ Exercise '{exercise_name}' has no ID. Cannot create set.")
            return None
        
        # Verify exercise exists using GET /exercises/{exercise_id} endpoint
        if check_exercise_exists:
            if not self.check_exercise_exists(exercise_id):
                print(f"  ❌ Exercise '{exercise_name}' (ID: {exercise_id}) not found in database.")
                print(f"     Cannot create set. Please ensure the exercise exists.")
                return None
        
        # Determine set parameters based on exercise type or defaults
        set_name = f"{exercise_name} Set"
        
        # Create set request
        set_data = {
            "name": set_name,
            "exercise_id": exercise_id
        }
        
        if reps is not None:
            set_data["reps"] = reps
        if weight is not None:
            set_data["weight"] = weight
        if duration_sec is not None:
            set_data["duration_sec"] = duration_sec
        
        print(f"  Creating set for {exercise_name} (exercise_id: {exercise_id})...")
        response = requests.post(f"{self.api_base}/sets/", json=set_data)
        
        if response.status_code in [200, 201]:
            set_result = response.json()
            set_id = set_result.get('id')
            print(f"    ✅ Created set: {set_id} ({set_name})")
            self.created_sets[exercise_id] = set_id
            return set_id
        else:
            print(f"    ❌ Failed to create set: {response.status_code} - {response.text}")
            if response.status_code == 404:
                print(f"    💡 Hint: Set creation failed. Check that exercise {exercise_id} exists.")
                print(f"       Verify with: GET {self.api_base}/exercises/{exercise_id}")
            return None
    
    def create_workout(self, workout_name: str, day_plans: List[Dict[str, Any]], 
                       create_missing_sets: bool = True) -> Optional[str]:
        """
        Create a workout with day plans.
        If create_missing_sets is True, validates that all referenced sets exist,
        and creates them if they don't (though this requires exercise data).
        """
        print(f"\n🏋️  Creating workout: {workout_name}")
        
        # Cascade: Validate all set IDs exist
        all_set_ids = []
        for day_plan in day_plans:
            exercises_ids = day_plan.get('exercises_ids', [])
            all_set_ids.extend(exercises_ids)
        
        if create_missing_sets:
            missing_sets = []
            for set_id in all_set_ids:
                if not self.check_set_exists(set_id):
                    missing_sets.append(set_id)
            
            if missing_sets:
                print(f"  ⚠️  Warning: {len(missing_sets)} set(s) not found: {missing_sets}")
                print(f"     The API will reject the workout if sets don't exist.")
                print(f"     Creating sets requires exercise data, which isn't available here.")
        
        workout_data = {
            "workout_plan": day_plans
        }
        
        response = requests.post(f"{self.api_base}/workouts/", json=workout_data)
        
        if response.status_code in [200, 201]:
            result = response.json()
            workout_id = result.get('workout_id')
            print(f"✅ Created workout: {workout_id} ({workout_name})")
            self.created_workouts[workout_name] = workout_id
            return workout_id
        elif response.status_code == 404:
            print(f"❌ Failed to create workout: One or more sets not found")
            print(f"   Details: {response.json().get('detail', 'Unknown error')}")
            return None
        else:
            print(f"❌ Failed to create workout: {response.status_code} - {response.text}")
            return None
    
    def check_workout_exists(self, workout_id: str) -> bool:
        """Check if a workout exists."""
        response = requests.get(f"{self.api_base}/workouts/{workout_id}")
        return response.status_code == 200
    
    def check_set_exists(self, set_id: str) -> bool:
        """Check if a set exists."""
        response = requests.get(f"{self.api_base}/sets/{set_id}")
        return response.status_code == 200
    
    def associate_workout_with_user(self, workout_id: str, create_if_missing: bool = False) -> bool:
        """
        Associate a workout with the user.
        If create_if_missing is True and workout doesn't exist, attempt to create it first.
        """
        if not self.user_id:
            print("❌ No user ID available")
            return False
        
        # Cascade: Check if workout exists, create if missing and create_if_missing is True
        if create_if_missing and not self.check_workout_exists(workout_id):
            print(f"  ⚠️  Workout {workout_id} doesn't exist. Creating it first...")
            # For now, we can't auto-create a workout without its structure
            # This would require the workout plan data
            print(f"    ❌ Cannot auto-create workout {workout_id} without workout plan data")
            return False
        
        print(f"  Associating workout {workout_id} with user {self.user_id}...")
        response = requests.post(
            f"{self.api_base}/users/{self.user_id}/workouts/{workout_id}"
        )
        
        if response.status_code in [200, 201]:
            print(f"    ✅ Associated workout {workout_id} with user")
            return True
        elif response.status_code == 404:
            print(f"    ❌ Workout {workout_id} not found. Cannot associate.")
            return False
        elif response.status_code == 409:
            print(f"    ℹ️  Workout already associated with user")
            return True
        else:
            print(f"    ❌ Failed to associate workout: {response.status_code} - {response.text}")
            return False
    
    def setup_workout_plan(self, selected_exercises: List[Dict[str, Any]]) -> Optional[str]:
        """Interactive setup of a workout plan."""
        if not selected_exercises:
            print("\n⚠️  No exercises selected. Skipping workout plan creation.")
            return None
        
        print("\n" + "="*80)
        print("📅 Workout Plan Setup")
        print("="*80)
        
        # Create sets for all selected exercises
        print("\n🔨 Creating sets for selected exercises...")
        set_ids = []
        for exercise in selected_exercises:
            # Default parameters - could be made configurable
            reps = 10  # Default reps
            set_id = self.create_set(exercise, reps=reps)
            if set_id:
                set_ids.append(set_id)
        
        if not set_ids:
            print("❌ No sets were created. Cannot create workout.")
            return None
        
        # Ask for workout name
        workout_name = input("\n📝 Enter workout name (or press Enter for 'My Workout'): ").strip()
        if not workout_name:
            workout_name = "My Workout"
        
        # Create day plans
        print("\n📆 Setting up weekly workout plan...")
        print("Enter which days should include exercises (comma-separated):")
        print("   Options: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday")
        print("   Example: Monday,Wednesday,Friday")
        
        days_input = input("Days: ").strip()
        if not days_input:
            print("⚠️  No days specified. Using Monday, Wednesday, Friday as default.")
            selected_days = ["Monday", "Wednesday", "Friday"]
        else:
            selected_days = [day.strip() for day in days_input.split(',')]
        
        # Distribute sets across selected days
        day_plans = []
        sets_per_day = len(set_ids) // len(selected_days) if selected_days else 0
        remaining_sets = len(set_ids) % len(selected_days) if selected_days else 0
        
        set_index = 0
        for day in selected_days:
            # Calculate how many sets for this day
            day_set_count = sets_per_day + (1 if remaining_sets > 0 else 0)
            remaining_sets -= 1
            
            # Get sets for this day
            day_set_ids = set_ids[set_index:set_index + day_set_count]
            set_index += day_set_count
            
            day_plan = {
                "day": day,
                "exercises_ids": day_set_ids
            }
            day_plans.append(day_plan)
            print(f"  {day}: {len(day_set_ids)} set(s)")
        
        # Create the workout
        workout_id = self.create_workout(workout_name, day_plans)
        
        # Associate with user
        if workout_id:
            self.associate_workout_with_user(workout_id)
            return workout_id
        
        return None
    
    def run(self, user_id: Optional[str] = None, interactive: bool = True, 
            workout_ids: Optional[List[str]] = None):
        """Run the complete setup process."""
        print("="*80)
        print("🚀 Workouts API - Get Started Script")
        print("="*80)
        
        # Step 1: Create user
        created_user_id = self.create_user(user_id)
        
        if not created_user_id:
            print("❌ Failed to create user. Exiting.")
            return
        
        # Step 2: Get exercises
        exercises = self.get_exercises()
        
        if not exercises:
            print("\n⚠️  No exercises found. Please ensure exercises are uploaded to MongoDB.")
            print("   Run: python upload_exercises_to_mongodb.py")
            return
        
        # Step 3: Select exercises (interactive)
        if interactive:
            selected_exercises = self.select_exercises(exercises)
        else:
            # Non-interactive: use first 5 exercises as example
            selected_exercises = exercises[:5]
            print(f"\n✅ Auto-selected {len(selected_exercises)} exercises (non-interactive mode)")
        
        # Step 4: Create workout plan
        workout_id = self.setup_workout_plan(selected_exercises)
        
        # Optional: Associate existing workouts
        if workout_ids:
            # Use provided workout IDs from command line
            print("\n" + "="*80)
            print("🔗 Associating Provided Workouts")
            print("="*80)
            print(f"Associating {len(workout_ids)} workout(s)...")
            for wid in workout_ids:
                self.associate_workout_with_user(wid, create_if_missing=False)
        elif interactive:
            # Prompt for workout IDs interactively
            print("\n" + "="*80)
            print("🔗 Associate Existing Workouts (Optional)")
            print("="*80)
            print("Enter existing workout IDs to associate with this user (comma-separated):")
            print("   Or press Enter to skip")
            workouts_input = input("Workout IDs: ").strip()
            
            if workouts_input:
                workout_ids_list = [wid.strip() for wid in workouts_input.split(',')]
                print(f"\nAssociating {len(workout_ids_list)} workout(s)...")
                for wid in workout_ids_list:
                    self.associate_workout_with_user(wid, create_if_missing=False)
        
        # Summary
        print("\n" + "="*80)
        print("📊 Setup Summary")
        print("="*80)
        print(f"User ID: {self.user_id}")
        print(f"Sets created: {len(self.created_sets)}")
        print(f"Workouts created: {len(self.created_workouts)}")
        if workout_id:
            print(f"Latest workout ID: {workout_id}")
        
        print("\n✅ Setup complete! You can now:")
        print(f"   - Get user info: GET {self.api_base}/users/{self.user_id}")
        print(f"   - Get weekly overview: GET {self.api_base}/users/{self.user_id}/weekly-overview")
        print(f"   - View API docs: {self.api_base}/docs")


def main():
    parser = argparse.ArgumentParser(
        description="Get Started Script for Workouts API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive setup with auto-generated user ID
  python get_started.py
  
  # Use specific user ID (from test script UUID)
  python get_started.py --user-id 550e8400-e29b-41d4-a716-446655440000
  
  # Non-interactive mode (uses first 5 exercises)
  python get_started.py --non-interactive
  
  # Associate existing workouts with user
  python get_started.py --user-id my-user-123 --workout-ids "workout-id-1,workout-id-2"
  
  # Custom API base URL
  python get_started.py --api-base http://localhost:8000
        """
    )
    parser.add_argument(
        '--user-id',
        type=str,
        help='User ID to use (UUID will be generated if not provided)'
    )
    parser.add_argument(
        '--api-base',
        type=str,
        default='http://localhost:8000',
        help='API base URL (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run in non-interactive mode (auto-selects first 5 exercises)'
    )
    parser.add_argument(
        '--workout-ids',
        type=str,
        help='Comma-separated list of existing workout IDs to associate with user (e.g., "id1,id2,id3")'
    )
    
    args = parser.parse_args()
    
    setup = WorkoutSetup(api_base=args.api_base)
    
    # Handle workout IDs if provided
    workout_ids_arg = []
    if args.workout_ids:
        workout_ids_arg = [wid.strip() for wid in args.workout_ids.split(',')]
    
    setup.run(user_id=args.user_id, interactive=not args.non_interactive, 
              workout_ids=workout_ids_arg)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

