#!/usr/bin/env python3
"""
Get Started LLM Script for Workouts API

This script helps set up a user with AI-generated workouts by:
1. Creating a user with a UUID (or provided user_id)
2. Fetching available exercises from the exercises collection
3. Using OpenAI to generate a workout plan based on natural language prompt
4. Creating sets for exercises in the generated plan
5. Creating workouts with those sets
6. Associating workouts with the user

Usage:
    export OPENAI_API_KEY="sk-proj-..."
    python get_started_llm.py --prompt "I want a mid-intensity workout for the winter for prep for the next kite surf season"
    python get_started_llm.py --user-id UUID --prompt "Full body strength workout"
"""

import requests
import uuid
import json
import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from openai import OpenAI


class LLMWorkoutSetup:
    def __init__(self, api_base: str = "http://localhost:8000", openai_api_key: Optional[str] = None):
        self.api_base = api_base.rstrip('/')
        self.user_id = None
        self.created_sets = {}
        self.created_workouts = {}
        self.exercises_cache = []  # Cache exercises to avoid multiple API calls
        
        # Initialize OpenAI client
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set or passed as argument")
        self.openai_client = OpenAI(api_key=api_key)
    
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
    
    def get_exercises(self, limit: int = 200, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Fetch available exercises from the API using GET /exercises/ endpoint."""
        # Return cached exercises if available and requested
        if use_cache and self.exercises_cache:
            return self.exercises_cache[:limit]
        
        print("\n🔍 Fetching available exercises from API...")
        
        try:
            response = requests.get(
                f"{self.api_base}/exercises/",
                params={"skip": 0, "limit": limit}
            )
            
            if response.status_code == 200:
                exercises = response.json()
                print(f"✅ Found {len(exercises)} exercise(s) from API")
                self.exercises_cache = exercises  # Cache the results
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
            exercises = self._get_exercises_from_json_fallback()
            self.exercises_cache = exercises  # Cache fallback results too
            return exercises
        except Exception as e:
            print(f"⚠️  Error fetching exercises from API: {e}")
            exercises = self._get_exercises_from_json_fallback()
            self.exercises_cache = exercises  # Cache fallback results too
            return exercises
    
    def _get_exercises_from_json_fallback(self) -> List[Dict[str, Any]]:
        """Fallback method to get exercises from JSON file if API is unavailable."""
        print("\n📁 Trying to load exercises from JSON file as fallback...")
        
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
    
    def generate_workout_plan(self, user_prompt: str, exercises: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Use OpenAI to generate a workout plan based on user prompt and available exercises.
        Returns a structured workout plan dictionary.
        """
        print("\n🤖 Generating workout plan with OpenAI...")
        print(f"📝 User prompt: {user_prompt}")
        
        # Prepare exercise summary for the LLM
        exercise_summaries = []
        for exercise in exercises[:300]:  # Limit to first 300 exercises to avoid token limits
            summary = {
                "id": exercise.get("id", ""),
                "name": exercise.get("name", ""),
                "category": exercise.get("category", ""),
                "equipment": exercise.get("equipment", ""),
                "primaryMuscles": exercise.get("primaryMuscles", []),
                "level": exercise.get("level", ""),
            }
            exercise_summaries.append(summary)
        
        # Create the prompt for OpenAI
        system_prompt = """You are a professional fitness trainer and workout planner. 
Your task is to create a personalized workout plan based on the user's goals and the available exercises.

Available exercises will be provided to you. You must select exercises from this list only (use their exact IDs).

You should create a weekly workout plan that:
1. Matches the user's fitness goals and requirements
2. Distributes exercises across appropriate days of the week
3. Provides appropriate reps, sets, weight, or duration for each exercise
4. Ensures proper recovery between similar muscle groups
5. Progresses appropriately throughout the week

Return your response as a JSON object with this exact structure:
{
    "workout_name": "Descriptive name for the workout plan",
    "workout_plan": [
        {
            "day": "Monday",
            "exercises": [
                {
                    "exercise_id": "exact_exercise_id_from_list",
                    "reps": 15,
                    "weight": null,
                    "duration_sec": null
                },
                {
                    "exercise_id": "another_exercise_id",
                    "reps": 10,
                    "weight": 20.5,
                    "duration_sec": null
                }
            ]
        },
        {
            "day": "Wednesday",
            "exercises": [
                {
                    "exercise_id": "exercise_id",
                    "reps": null,
                    "weight": null,
                    "duration_sec": 60
                }
            ]
        }
    ]
}

Important:
- Use exact exercise IDs from the provided list
- Include only days that have exercises (don't include rest days)
- For repetition-based exercises: set "reps" and leave weight/duration_sec as null
- For time-based exercises: set "duration_sec" and leave reps/weight as null
- For weighted exercises: set both "reps" and "weight", leave duration_sec as null
- Days must be: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, or Sunday
- Create a realistic, progressive workout plan (typically 3-5 days per week)
- Consider the user's goals when selecting exercises and intensity
"""

        user_message = f"""User's fitness goal: {user_prompt}

Available exercises (select from these only):
{json.dumps(exercise_summaries, indent=2)}

Create a personalized workout plan. Return ONLY valid JSON, no additional text."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            print("✅ Received workout plan from OpenAI")
            
            # Parse JSON response
            workout_plan = json.loads(content)
            return workout_plan
        
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response from OpenAI: {e}")
            print(f"Response was: {content[:500]}")
            return None
        except Exception as e:
            print(f"❌ Error calling OpenAI API: {e}")
            return None
    
    def check_exercise_exists(self, exercise_id: str) -> bool:
        """Check if an exercise exists using GET /exercises/{exercise_id} endpoint."""
        try:
            response = requests.get(f"{self.api_base}/exercises/{exercise_id}")
            return response.status_code == 200
        except Exception:
            return False
    
    def create_set(self, exercise_id: str, exercise_name: str, reps: Optional[int] = None, 
                   weight: Optional[float] = None, duration_sec: Optional[int] = None,
                   check_exercise_exists: bool = True) -> Optional[str]:
        """Create a set for an exercise."""
        if not exercise_id:
            print(f"  ❌ Exercise '{exercise_name}' has no ID. Cannot create set.")
            return None
        
        # Verify exercise exists
        if check_exercise_exists:
            if not self.check_exercise_exists(exercise_id):
                print(f"  ❌ Exercise '{exercise_name}' (ID: {exercise_id}) not found in database.")
                return None
        
        # Create set request
        set_name = f"{exercise_name} Set"
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
            return None
    
    def create_workout_from_plan(self, workout_plan_data: Dict[str, Any]) -> Optional[str]:
        """Create a workout from the LLM-generated plan."""
        workout_name = workout_plan_data.get("workout_name", "AI Generated Workout")
        day_plans_raw = workout_plan_data.get("workout_plan", [])
        
        print(f"\n🏋️  Creating workout: {workout_name}")
        
        # First, find exercise names for all exercise IDs (use cached exercises)
        exercises_map = {}
        for exercise in self.get_exercises(limit=500, use_cache=True):
            exercises_map[exercise.get("id")] = exercise
        
        # Create sets and build day plans
        day_plans = []
        all_set_ids = []
        
        for day_plan_raw in day_plans_raw:
            day = day_plan_raw.get("day")
            exercises_raw = day_plan_raw.get("exercises", [])
            
            if not day or not exercises_raw:
                continue
            
            day_set_ids = []
            
            for exercise_data in exercises_raw:
                exercise_id = exercise_data.get("exercise_id")
                if not exercise_id:
                    print(f"  ⚠️  Skipping exercise with no ID in {day}")
                    continue
                
                # Get exercise name
                exercise = exercises_map.get(exercise_id)
                if exercise:
                    exercise_name = exercise.get("name", exercise_id)
                else:
                    exercise_name = exercise_id
                    print(f"  ⚠️  Exercise ID '{exercise_id}' not found in available exercises, using ID as name")
                
                # Extract set parameters
                reps = exercise_data.get("reps")
                weight = exercise_data.get("weight")
                duration_sec = exercise_data.get("duration_sec")
                
                # Check if set already created for this exercise_id
                if exercise_id in self.created_sets:
                    set_id = self.created_sets[exercise_id]
                    print(f"  Reusing existing set for {exercise_name}")
                else:
                    # Create new set
                    set_id = self.create_set(
                        exercise_id=exercise_id,
                        exercise_name=exercise_name,
                        reps=reps,
                        weight=weight,
                        duration_sec=duration_sec
                    )
                
                if set_id:
                    day_set_ids.append(set_id)
            
            if day_set_ids:
                day_plan = {
                    "day": day,
                    "exercises_ids": day_set_ids
                }
                day_plans.append(day_plan)
                all_set_ids.extend(day_set_ids)
                print(f"  {day}: {len(day_set_ids)} set(s)")
        
        if not day_plans:
            print("❌ No valid day plans created. Cannot create workout.")
            return None
        
        # Create workout
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
    
    def associate_workout_with_user(self, workout_id: str) -> bool:
        """Associate a workout with the user."""
        if not self.user_id:
            print("❌ No user ID available")
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
    
    def run(self, user_prompt: str, user_id: Optional[str] = None):
        """Run the complete LLM-powered setup process."""
        print("="*80)
        print("🚀 Workouts API - AI-Powered Get Started Script")
        print("="*80)
        
        # Step 1: Create user
        created_user_id = self.create_user(user_id)
        
        if not created_user_id:
            print("❌ Failed to create user. Exiting.")
            return
        
        # Step 2: Get exercises
        exercises = self.get_exercises(limit=300)
        
        if not exercises:
            print("\n⚠️  No exercises found. Please ensure exercises are uploaded to MongoDB.")
            print("   Run: python upload_exercises_to_mongodb.py")
            return
        
        # Step 3: Generate workout plan with LLM
        workout_plan_data = self.generate_workout_plan(user_prompt, exercises)
        
        if not workout_plan_data:
            print("❌ Failed to generate workout plan. Exiting.")
            return
        
        print(f"\n📋 Generated workout plan: {workout_plan_data.get('workout_name', 'Unnamed')}")
        print(f"   Days: {len(workout_plan_data.get('workout_plan', []))}")
        
        # Step 4: Create workout from plan
        workout_id = self.create_workout_from_plan(workout_plan_data)
        
        # Step 5: Associate with user
        if workout_id:
            self.associate_workout_with_user(workout_id)
        
        # Summary
        print("\n" + "="*80)
        print("📊 Setup Summary")
        print("="*80)
        print(f"User ID: {self.user_id}")
        print(f"User prompt: {user_prompt}")
        print(f"Workout name: {workout_plan_data.get('workout_name', 'N/A')}")
        print(f"Sets created: {len(self.created_sets)}")
        print(f"Workouts created: {len(self.created_workouts)}")
        if workout_id:
            print(f"Workout ID: {workout_id}")
        
        print("\n✅ Setup complete! You can now:")
        print(f"   - Get user info: GET {self.api_base}/users/{self.user_id}")
        print(f"   - Get weekly overview: GET {self.api_base}/users/{self.user_id}/weekly-overview")
        print(f"   - View API docs: {self.api_base}/docs")


def main():
    parser = argparse.ArgumentParser(
        description="AI-Powered Get Started Script for Workouts API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate workout from prompt
  export OPENAI_API_KEY="sk-proj-..."
  python get_started_llm.py --prompt "I want a mid-intensity workout for the winter for prep for the next kite surf season"
  
  # Use specific user ID
  python get_started_llm.py --prompt "Full body strength workout 3 times per week" --user-id 550e8400-e29b-41d4-a716-446655440000
  
  # Custom API base URL
  python get_started_llm.py --prompt "Yoga and stretching routine" --api-base http://localhost:8000
  
  # Custom OpenAI API key
  python get_started_llm.py --prompt "Cardio and endurance training" --openai-key "sk-proj-..."
        """
    )
    parser.add_argument(
        '--prompt',
        type=str,
        required=True,
        help='Natural language description of the desired workout (e.g., "mid-intensity workout for winter prep for kite surfing")'
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
        '--openai-key',
        type=str,
        help='OpenAI API key (defaults to OPENAI_API_KEY environment variable)'
    )
    
    args = parser.parse_args()
    
    setup = LLMWorkoutSetup(api_base=args.api_base, openai_api_key=args.openai_key)
    setup.run(user_prompt=args.prompt, user_id=args.user_id)


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

