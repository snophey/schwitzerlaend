"""User-related API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from models import GenerateWorkoutRequest
from database import get_database
from bson import ObjectId
import os
import json
from openai import OpenAI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/{user_id}", response_model=Dict[str, Any])
async def create_user(user_id: str):
    """
    Create a new user.
    
    - **user_id**: Unique identifier for the user
    
    Returns the created user data with associated_workout_ids set to null by default.
    """
    logger.info(f"POST /users/{user_id} endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot create user")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        users_collection = db["users"]
        
        # Check if user already exists
        existing_user = users_collection.find_one({'_id': user_id})
        if existing_user:
            logger.warning(f"User with user_id '{user_id}' already exists")
            raise HTTPException(
                status_code=409,
                detail=f"User with user_id '{user_id}' already exists. Cannot create duplicate user."
            )
        
        # Create user document
        user_doc = {
            '_id': user_id,
            'associated_workout_ids': []
        }
        
        result = users_collection.insert_one(user_doc)
        
        if result.inserted_id:
            logger.info(f"Successfully created user with user_id: {user_id} (ID: {result.inserted_id})")
        else:
            logger.error("Failed to insert user document")
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        return {
            "user_id": user_id,
            "associated_workout_ids": []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user with user_id '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_user(user_id: str):
    """
    Get user information by user_id.
    
    - **user_id**: Unique identifier for the user
    
    Returns the user data including user_id and associated_workout_ids.
    """
    logger.info(f"GET /users/{user_id} endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot get user")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        users_collection = db["users"]
        user_doc = users_collection.find_one({'_id': user_id})
        
        if not user_doc:
            logger.warning(f"User with user_id '{user_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"User with user_id '{user_id}' not found"
            )
        
        user_data = {
            "user_id": user_doc.get('_id', user_id),
            "associated_workout_ids": user_doc.get('associated_workout_ids', [])
        }
        
        logger.info(f"Successfully retrieved user with user_id: {user_id}")
        return user_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user with user_id '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.delete("/{user_id}", response_model=Dict[str, Any])
async def delete_user(user_id: str):
    """
    Delete a user by user_id.
    
    - **user_id**: Unique identifier for the user
    
    Returns a confirmation message upon successful deletion.
    """
    logger.info(f"DELETE /users/{user_id} endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot delete user")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        users_collection = db["users"]
        
        user_doc = users_collection.find_one({'_id': user_id})
        if not user_doc:
            logger.warning(f"User with user_id '{user_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"User with user_id '{user_id}' not found"
            )
        
        result = users_collection.delete_one({'_id': user_id})
        
        if result.deleted_count == 1:
            logger.info(f"Successfully deleted user with user_id: {user_id}")
            return {
                "message": f"User with user_id '{user_id}' has been successfully deleted",
                "user_id": user_id
            }
        else:
            logger.error(f"Failed to delete user '{user_id}'")
            raise HTTPException(status_code=500, detail=f"Failed to delete user with user_id '{user_id}'")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user with user_id '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


@router.post("/{user_id}/workouts/{workout_id}", response_model=Dict[str, Any], tags=["User Workouts"])
async def add_workout_to_user(user_id: str, workout_id: str):
    """
    Add a workout ID to the user's associated_workout_ids list.
    
    - **user_id**: ID of the user
    - **workout_id**: ID of the workout to associate with the user
    
    Returns the updated user data.
    """
    logger.info(f"POST /users/{user_id}/workouts/{workout_id} endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot add workout to user")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        users_collection = db["users"]
        workouts_collection = db["workouts"]
        
        user_doc = users_collection.find_one({'_id': user_id})
        if not user_doc:
            logger.warning(f"User with user_id '{user_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"User with user_id '{user_id}' not found"
            )
        
        workout_doc = workouts_collection.find_one({'_id': workout_id})
        if not workout_doc:
            logger.warning(f"Workout with workout_id '{workout_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Workout with workout_id '{workout_id}' not found"
            )
        
        current_workout_ids = user_doc.get('associated_workout_ids', [])
        if current_workout_ids is None:
            current_workout_ids = []
        
        if workout_id in current_workout_ids:
            logger.warning(f"Workout '{workout_id}' is already associated with user '{user_id}'")
            raise HTTPException(
                status_code=409,
                detail=f"Workout with workout_id '{workout_id}' is already associated with user '{user_id}'"
            )
        
        updated_workout_ids = current_workout_ids + [workout_id]
        
        result = users_collection.update_one(
            {'_id': user_id},
            {'$set': {'associated_workout_ids': updated_workout_ids}}
        )
        
        if result.modified_count == 1:
            logger.info(f"Successfully added workout '{workout_id}' to user '{user_id}'")
        elif result.matched_count == 0:
            logger.error(f"User '{user_id}' not found for update")
            raise HTTPException(status_code=404, detail=f"User with user_id '{user_id}' not found")
        else:
            logger.warning(f"Update operation didn't modify user document")
        
        return {
            "user_id": user_id,
            "associated_workout_ids": updated_workout_ids,
            "message": f"Successfully added workout '{workout_id}' to user '{user_id}'"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding workout to user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add workout to user: {str(e)}")


@router.delete("/{user_id}/workouts/{workout_id}", response_model=Dict[str, Any], tags=["User Workouts"])
async def remove_workout_from_user(user_id: str, workout_id: str):
    """
    Remove a workout ID from the user's associated_workout_ids list.
    
    - **user_id**: ID of the user
    - **workout_id**: ID of the workout to remove from the user's associated workouts
    
    Returns the updated user data.
    """
    logger.info(f"DELETE /users/{user_id}/workouts/{workout_id} endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot remove workout from user")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        users_collection = db["users"]
        
        user_doc = users_collection.find_one({'_id': user_id})
        if not user_doc:
            logger.warning(f"User with user_id '{user_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"User with user_id '{user_id}' not found"
            )
        
        current_workout_ids = user_doc.get('associated_workout_ids', [])
        if current_workout_ids is None:
            current_workout_ids = []
        
        if workout_id not in current_workout_ids:
            logger.warning(f"Workout '{workout_id}' is not associated with user '{user_id}'")
            raise HTTPException(
                status_code=404,
                detail=f"Workout with workout_id '{workout_id}' is not associated with user '{user_id}'"
            )
        
        updated_workout_ids = [wid for wid in current_workout_ids if wid != workout_id]
        
        result = users_collection.update_one(
            {'_id': user_id},
            {'$set': {'associated_workout_ids': updated_workout_ids}}
        )
        
        if result.modified_count == 1:
            logger.info(f"Successfully removed workout '{workout_id}' from user '{user_id}'")
        elif result.matched_count == 0:
            logger.error(f"User '{user_id}' not found for update")
            raise HTTPException(status_code=404, detail=f"User with user_id '{user_id}' not found")
        else:
            logger.warning(f"Update operation didn't modify user document")
        
        return {
            "user_id": user_id,
            "associated_workout_ids": updated_workout_ids,
            "message": f"Successfully removed workout '{workout_id}' from user '{user_id}'"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing workout from user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to remove workout from user: {str(e)}")


@router.get("/{user_id}/weekly-overview", response_model=Dict[str, Any], tags=["User Workouts"])
async def get_weekly_overview(user_id: str):
    """
    Get weekly workout overview for a specific user.
    
    - **user_id**: ID of the user
    
    Returns a weekly overview showing all 7 days (Monday-Sunday) for each associated workout.
    """
    logger.info(f"GET /users/{user_id}/weekly-overview endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot get weekly overview")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        users_collection = db["users"]
        user_doc = users_collection.find_one({'_id': user_id})
        
        if not user_doc:
            logger.warning(f"User with user_id '{user_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"User with user_id '{user_id}' not found"
            )
        
        associated_workout_ids = user_doc.get('associated_workout_ids', [])
        
        if not associated_workout_ids:
            logger.warning(f"No associated workouts found for user_id: {user_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No associated workouts found for user_id: {user_id}"
            )
        
        workouts_collection = db["workouts"]
        
        def build_weekly_plan_for_workout(workout_plan):
            """Build weekly plan structure from a workout plan."""
            sets_collection = db["sets"]
            all_sets = {}
            
            set_ids = set()
            exercise_ids = set()
            
            for day_plan in workout_plan:
                exercises_ids = day_plan.get('exercises_ids', [])
                exercises_ids = [str(eid) if not isinstance(eid, str) else eid for eid in exercises_ids]
                set_ids.update(exercises_ids)
            
            for set_id in set_ids:
                set_doc = sets_collection.find_one({'_id': set_id})
                if set_doc:
                    formatted_set = {}
                    for key, value in set_doc.items():
                        if key != '_id':
                            formatted_set[key] = value
                    
                    exercise_id = formatted_set.get('excersise_id') or formatted_set.get('exercise_id')
                    if exercise_id:
                        exercise_ids.add(exercise_id)
                    
                    all_sets[set_id] = formatted_set
            
            exercises_collection = db["exercises"]
            all_exercises = {}
            
            for exercise_id in exercise_ids:
                exercise_doc = exercises_collection.find_one({'_id': exercise_id})
                if exercise_doc:
                    formatted_exercise = {}
                    for key, value in exercise_doc.items():
                        if key == '_id':
                            formatted_exercise['id'] = value
                        else:
                            formatted_exercise[key] = value
                    all_exercises[exercise_id] = formatted_exercise
            
            week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            weekly_plan = []
            day_sets_map = {}
            
            for day_plan in workout_plan:
                day = day_plan.get('day', '')
                exercises_ids = day_plan.get('exercises_ids', [])
                exercises_ids = [str(eid) if not isinstance(eid, str) else eid for eid in exercises_ids]
                day_sets_map[day] = [all_sets.get(str(eid)) for eid in exercises_ids if str(eid) in all_sets]
            
            for day in week_days:
                sets_for_day = day_sets_map.get(day, [])
                
                formatted_sets = []
                for set_data in sets_for_day:
                    if set_data:
                        exercise_id = set_data.get('excersise_id') or set_data.get('exercise_id')
                        
                        exercise_info = None
                        if exercise_id and exercise_id in all_exercises:
                            exercise_info = all_exercises[exercise_id]
                        
                        formatted_set = {
                            "name": set_data.get('name', 'Unknown Exercise'),
                            "reps": set_data.get('reps'),
                            "weight": set_data.get('weight'),
                            "duration_sec": set_data.get('duration_sec'),
                            "exercise_id": exercise_id or 'N/A',
                            "exercise": exercise_info
                        }
                        formatted_sets.append(formatted_set)
                
                weekly_plan.append({
                    "day": day,
                    "day_number": week_days.index(day) + 1,
                    "sets": formatted_sets,
                    "is_rest_day": len(formatted_sets) == 0
                })
            
            total_sets = sum(len(day_entry['sets']) for day_entry in weekly_plan)
            training_days = sum(1 for day_entry in weekly_plan if not day_entry['is_rest_day'])
            rest_days = 7 - training_days
            
            return {
                "weekly_plan": weekly_plan,
                "summary": {
                    "training_days": training_days,
                    "rest_days": rest_days,
                    "total_sets": total_sets
                }
            }
        
        workouts_data = []
        
        for workout_id in associated_workout_ids:
            workout_doc = workouts_collection.find_one({'_id': workout_id})
            
            if not workout_doc:
                logger.warning(f"Workout with workout_id '{workout_id}' not found - skipping")
                workouts_data.append({
                    "workout_id": workout_id,
                    "error": f"Workout not found"
                })
                continue
            
            workout_plan = workout_doc.get('workout_plan', [])
            
            if not workout_plan:
                logger.warning(f"Workout plan is empty for workout_id: {workout_id}")
                workouts_data.append({
                    "workout_id": workout_id,
                    "error": "Workout plan is empty"
                })
                continue
            
            weekly_data = build_weekly_plan_for_workout(workout_plan)
            
            workouts_data.append({
                "workout_id": workout_id,
                **weekly_data
            })
        
        total_training_days = sum(w.get('summary', {}).get('training_days', 0) for w in workouts_data if 'summary' in w)
        total_rest_days = sum(w.get('summary', {}).get('rest_days', 0) for w in workouts_data if 'summary' in w)
        total_sets = sum(w.get('summary', {}).get('total_sets', 0) for w in workouts_data if 'summary' in w)
        
        logger.info(f"Retrieved weekly overview for user_id: {user_id} - {len(associated_workout_ids)} workout(s)")
        
        return {
            "user_id": user_id,
            "associated_workout_ids": associated_workout_ids,
            "workouts": workouts_data,
            "overall_summary": {
                "total_workouts": len(associated_workout_ids),
                "total_training_days": total_training_days,
                "total_rest_days": total_rest_days,
                "total_sets": total_sets
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving weekly overview for user_id '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get weekly overview: {str(e)}")


@router.post("/{user_id}/generate-workout", response_model=Dict[str, Any], tags=["User Workouts"])
async def generate_workout_for_user(user_id: str, request: GenerateWorkoutRequest):
    """
    Generate an AI-powered workout plan for an existing user.
    
    - **user_id**: ID of the user (must already exist)
    - **prompt**: Natural language description of the desired workout
    - **openai_api_key**: (Optional) OpenAI API key
    
    Returns the created workout with workout_id and summary.
    """
    logger.info(f"POST /users/{user_id}/generate-workout endpoint called")
    
    db = get_database()
    if db is None:
        logger.error("Database connection is None - cannot generate workout")
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        users_collection = db["users"]
        user_doc = users_collection.find_one({'_id': user_id})
        
        if not user_doc:
            logger.warning(f"User with user_id '{user_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"User with user_id '{user_id}' not found. Please create the user first."
            )
        
        api_key = request.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not provided")
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key must be provided either in request or as OPENAI_API_KEY environment variable"
            )
        
        openai_client = OpenAI(api_key=api_key)
        
        exercises_collection = db["exercises"]
        logger.info("Fetching exercises from database...")
        exercise_docs = list(exercises_collection.find().limit(300))
        
        if not exercise_docs:
            logger.warning("No exercises found in database")
            raise HTTPException(
                status_code=404,
                detail="No exercises found in database. Please upload exercises first."
            )
        
        exercise_summaries = []
        exercises_map = {}
        for exercise_doc in exercise_docs:
            exercise_id = exercise_doc.get('_id', '')
            exercise_summary = {
                "id": str(exercise_id),
                "name": exercise_doc.get("name", ""),
                "category": exercise_doc.get("category", ""),
                "equipment": exercise_doc.get("equipment", ""),
                "primaryMuscles": exercise_doc.get("primaryMuscles", []),
                "level": exercise_doc.get("level", ""),
            }
            exercise_summaries.append(exercise_summary)
            exercises_map[str(exercise_id)] = exercise_doc
        
        logger.info(f"Prepared {len(exercise_summaries)} exercises for LLM")
        
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
"""

        user_message = f"""User's fitness goal: {request.prompt}

Available exercises (select from these only):
{json.dumps(exercise_summaries, indent=2)}

Create a personalized workout plan. Return ONLY valid JSON, no additional text."""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            logger.info("Successfully received workout plan from OpenAI")
            
            workout_plan_data = json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from OpenAI: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to parse workout plan from OpenAI: {str(e)}")
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to generate workout plan with OpenAI: {str(e)}")
        
        workout_name = workout_plan_data.get("workout_name", "AI Generated Workout")
        day_plans_raw = workout_plan_data.get("workout_plan", [])
        
        logger.info(f"Processing workout plan: {workout_name} with {len(day_plans_raw)} days")
        
        sets_collection = db["sets"]
        workouts_collection = db["workouts"]
        day_plans = []
        created_sets = {}
        created_set_ids = []
        
        for day_plan_raw in day_plans_raw:
            day = day_plan_raw.get("day")
            exercises_raw = day_plan_raw.get("exercises", [])
            
            if not day or not exercises_raw:
                continue
            
            day_set_ids = []
            
            for exercise_data in exercises_raw:
                exercise_id = exercise_data.get("exercise_id")
                if not exercise_id:
                    logger.warning(f"Skipping exercise with no ID in {day}")
                    continue
                
                exercise = exercises_map.get(str(exercise_id))
                if exercise:
                    exercise_name = exercise.get("name", exercise_id)
                else:
                    exercise_doc = exercises_collection.find_one({'_id': exercise_id})
                    if not exercise_doc:
                        logger.warning(f"Exercise ID '{exercise_id}' not found in database - skipping")
                        continue
                    exercise_name = exercise_doc.get("name", exercise_id)
                
                reps = exercise_data.get("reps")
                weight = exercise_data.get("weight")
                duration_sec = exercise_data.get("duration_sec")
                
                if exercise_id in created_sets:
                    set_id = created_sets[exercise_id]
                    logger.info(f"Reusing existing set {set_id} for {exercise_name}")
                else:
                    set_id = str(ObjectId())
                    set_name = f"{exercise_name} Set"
                    
                    set_doc = {
                        '_id': set_id,
                        'name': set_name,
                        'excersise_id': exercise_id,
                        'exercise_id': exercise_id,
                    }
                    
                    if reps is not None:
                        set_doc['reps'] = reps
                    if weight is not None:
                        set_doc['weight'] = weight
                    if duration_sec is not None:
                        set_doc['duration_sec'] = duration_sec
                    
                    sets_collection.insert_one(set_doc)
                    created_sets[exercise_id] = set_id
                    logger.info(f"Created set {set_id} for {exercise_name}")
                
                day_set_ids.append(set_id)
            
            if day_set_ids:
                day_plan = {
                    "day": day,
                    "exercises_ids": day_set_ids
                }
                day_plans.append(day_plan)
                created_set_ids.extend(day_set_ids)
                logger.info(f"  {day}: {len(day_set_ids)} set(s)")
        
        if not day_plans:
            logger.error("No valid day plans created from workout plan")
            raise HTTPException(status_code=500, detail="Failed to create workout: No valid day plans generated")
        
        workout_id = str(ObjectId())
        workout_doc = {
            '_id': workout_id,
            'workout_plan': day_plans
        }
        
        workouts_collection.insert_one(workout_doc)
        logger.info(f"Created workout {workout_id} ({workout_name})")
        
        current_workout_ids = user_doc.get('associated_workout_ids', [])
        if current_workout_ids is None:
            current_workout_ids = []
        
        if workout_id not in current_workout_ids:
            updated_workout_ids = current_workout_ids + [workout_id]
            users_collection.update_one(
                {'_id': user_id},
                {'$set': {'associated_workout_ids': updated_workout_ids}}
            )
            logger.info(f"Associated workout {workout_id} with user {user_id}")
        
        logger.info(f"Successfully generated workout for user_id: {user_id} - workout_id: {workout_id}")
        
        return {
            "user_id": user_id,
            "workout_id": workout_id,
            "workout_name": workout_name,
            "workout_plan": day_plans,
            "summary": {
                "sets_created": len(created_sets),
                "days": len(day_plans),
                "total_sets": len(created_set_ids)
            },
            "message": f"Successfully generated workout '{workout_name}' and associated it with user"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating workout for user_id '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate workout: {str(e)}")
