"""Pydantic models for request and response validation."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Exercise(BaseModel):
    """Exercise model for workout generation."""
    type: str = Field(..., description="Type of exercise: 'repetition', 'weighted repetition', 'time', 'distance', or 'skill'", example="repetition")
    reps: Optional[int] = Field(None, description="Number of repetitions (for repetition, weighted repetition, or skill types)", example=10)
    weight: Optional[float] = Field(None, description="Weight in kg (for weighted repetition type)", example=20.5)
    duration_sec: Optional[int] = Field(None, description="Duration in seconds (for time type)", example=60)
    skill: Optional[str] = Field(None, description="Skill description (for skill type)", example="Balance hold")
    description: str = Field(..., description="Detailed description of how to perform the exercise", example="Perform push-ups with proper form, keeping your back straight")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "repetition",
                "reps": 15,
                "description": "Perform 15 push-ups with proper form"
            }
        }


class AddWorkoutRequest(BaseModel):
    """Request model for adding a workout manually."""
    workout_name: str = Field(..., description="Name of the workout", example="Morning Yoga")
    exercises: Optional[Dict[str, Exercise]] = Field(None, description="Dictionary of exercise names mapped to Exercise objects")

    class Config:
        json_schema_extra = {
            "example": {
                "workout_name": "Morning Yoga",
                "exercises": {
                    "Downward Dog": {
                        "type": "time",
                        "duration_sec": 60,
                        "description": "Hold downward dog pose for 60 seconds"
                    }
                }
            }
        }


class GenerateWorkoutRequest(BaseModel):
    """Request model for AI-powered workout generation."""
    prompt: str = Field(..., description="Natural language description of the desired workout", example="I want soft yoga mainly stretching mid efforts")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key (if not provided, uses OPENAI_API_KEY env variable)")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "I want a full body strength workout with 5 exercises"
            }
        }


class CreateSetRequest(BaseModel):
    """Request model for creating an exercise set."""
    name: str = Field(..., description="Name of the set", example="Push-ups Set 1")
    exercise_id: str = Field(..., description="ID of the exercise this set references", example="push_up_001")
    reps: Optional[int] = Field(None, description="Number of repetitions", example=15)
    weight: Optional[float] = Field(None, description="Weight in kg", example=0.0)
    duration_sec: Optional[int] = Field(None, description="Duration in seconds", example=60)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Push-ups Set 1",
                "exercise_id": "push_up_001",
                "reps": 15,
                "weight": None,
                "duration_sec": None
            }
        }


class CreateExerciseRequest(BaseModel):
    """Request model for creating an exercise."""
    exercise_id: str = Field(..., description="Unique identifier for the exercise", example="3_4_Sit-Up")
    name: str = Field(..., description="Name of the exercise", example="3/4 Sit-Up")
    force: Optional[str] = Field(None, description="Force type: 'pull' or 'push'", example="pull")
    level: Optional[str] = Field(None, description="Difficulty level: 'beginner', 'intermediate', or 'expert'", example="beginner")
    mechanic: Optional[str] = Field(None, description="Mechanic type: 'compound' or 'isolation'", example="compound")
    equipment: Optional[str] = Field(None, description="Equipment required", example="body only")
    primaryMuscles: Optional[List[str]] = Field(None, description="Primary muscles targeted", example=["abdominals"])
    secondaryMuscles: Optional[List[str]] = Field(None, description="Secondary muscles targeted", example=[])
    instructions: Optional[List[str]] = Field(None, description="Step-by-step instructions", example=["Lie down on the floor..."])
    category: Optional[str] = Field(None, description="Exercise category", example="strength")

    class Config:
        json_schema_extra = {
            "example": {
                "exercise_id": "3_4_Sit-Up",
                "name": "3/4 Sit-Up",
                "force": "pull",
                "level": "beginner",
                "mechanic": "compound",
                "equipment": "body only",
                "primaryMuscles": ["abdominals"],
                "secondaryMuscles": [],
                "instructions": ["Lie down on the floor and secure your feet."],
                "category": "strength"
            }
        }


class DayPlan(BaseModel):
    """Day plan model for workout schedules."""
    day: str = Field(..., description="Day of the week", example="Monday")
    exercises_ids: List[str] = Field(..., description="List of set IDs for this day", example=["set_1", "set_2", "set_3"])

    class Config:
        json_schema_extra = {
            "example": {
                "day": "Monday",
                "exercises_ids": ["1", "2", "3"]
            }
        }


class CreateWorkoutRequest(BaseModel):
    """Request model for creating a workout plan."""
    workout_plan: List[DayPlan] = Field(..., description="Array of day plans, each with day and exercises_ids")

    class Config:
        json_schema_extra = {
            "example": {
                "workout_plan": [
                    {
                        "day": "Monday",
                        "exercises_ids": ["1", "2", "3"]
                    },
                    {
                        "day": "Wednesday",
                        "exercises_ids": ["3"]
                    }
                ]
            }
        }
