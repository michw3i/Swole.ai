from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import httpx
import uuid
import json
import os 
import requests
from enum import Enum

from openai import OpenAi
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', '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'))
# wger API import

from supabase import create_client, Client
supabase_url = os.getenv('SUPABASE_URL', 'https://knslveiqkalonzgmaubq.supabase.co')
supabase_key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtuc2x2ZWlxa2Fsb256Z21hdWJxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA0MjIwMDgsImV4cCI6MjA4NTk5ODAwOH0.Utu6AcBUMGd4xCj4e-3oF_RDGrRNLa03pi1IJ0eP2_M')
supabase: Client = create_client(supabase_url, supabase_key)

# ------------------------ FastAPI ----------------------------
app = FastAPI(
    title="Swole.ai",
    description="Supabase + OpenAI + Wger integration",
    version="3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ Pydantic Models -----------------
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class FitnessLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class WorkoutType(str, Enum):
    CARDIO = "cardio"
    UPPER_BODY= "upper_body"
    LOWER_BODY = "lower_body"
    FULL_BODY = "full_body"
    ARMS = "arms"
    LEGS = "legs"
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    ABS = "abs"
    STRETCHING = "stretching"

class UserProfile(BaseModel):
    name: str
    age: int = Field(ge=13, le=120)
    gender: Gender
    weight_kg: float = Field(gt=0)
    height_cm: float = Field(gt=0)
    fitness_level: FitnessLevel
    goals: List[str]
    medical_conditions: Optional[List[str]]=[]

class WorkoutRequest(BaseModel):
    user_id: str
    workout_type: WorkoutType
    duration_minutes: int = Field(default=30, ge=10, le=120)
    equipment_available: List[str] = []

class WorkoutFeedback(BaseModel):
    workout_id: str
    completed: bool
    difficulty_rating: int = Field(ge=1, le=10)
    enjoyed: bool
    notes: Optional[str] = None

# ------------------ Wger API Integration -----------------
WGER_BASE_URL = "https://wger.de/api/v2"
WORKOUT_CATEGORIES = {
    "cardio": [9],
    "upper_body": [8, 14, 12, 13],
    "lower_body": [9, 11],
    "full_body": [8, 9, 10, 11, 12, 13, 14],
    "arms": [8],
    "legs": [9, 11],
    "chest": [14],
    "back": [12],
    "shoulders": [13],
    "abs": [10],
    "stretching": [9, 10]
}

async def fetch_wger_exercises(workout_type: str, limit: int = 50) -> List[Dict]:
    """Fetch exercises from Wger API"""
    categories = WORKOUT_CATEGORIES.get(workout_type, [8, 9, 10])
    all_exercises = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for category in categories:
            try:
                response = await client.get(
                    f"{WGER_BASE_URL}/exercise/",
                    params = {"language": 2, "category": category, "limit": limit}
                )
                data = response.json()
                all_exercises.extend(data.get("results", []))
            except Exception as e:
                print(f"Wger API error: {e}")
    return all_exercises


async def get_exercise_images(exercise_id: int) -> List[str]:
        """Get image URLs for an exercise"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{WGER_BASE_URL/exerciseimage/}",
                params={"exercise": exercise_id}
            )
            data = response.json()
            return [img.get("image") for img in data.get("results", [])]
        except:
            return []

async def get_exercise_videos(exercise_id: int) -> List[str]:
    """Get video URLs for an exercise"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{WGER_BASE_URL}/exercisevideo/",
                params={"exercise": exercise_id}
            )
            data = response.json()
            return [vid.get("video") for vid in data.get("results", [])]
        except:
            return []

# -------------OpenAI Workout Generation---------------
async def generate_ai_workout(
    user_profile: Dict,
    workout_type: str,
    duration_minutes: int,
    available_exercises: List[Dict]
) -> Dict:
    """Use OpenAI to generate intelligent workout plan"""
    
    # Prepare exercise options
    exercise_list = []
    for ex in available_exercises[:30]:
        exercise_list.append({
            "id": ex.get("id"),
            "name": ex.get("name"),
            "description": ex.get("description", "")[:100],
            "category": ex.get("category", {}).get("name", ""),
            "muscles": [m.get("name") for m in ex.get("muscles", [])],
            "equipment": [e.get("name") for e in ex.get("equipment", [])]
        })
    
    # AI prompt
    prompt = f"""You are an expert fitness trainer. Create a personalized {duration_minutes}-minute workout.
    
USER PROFILE:
- Name: {user_profile['name']}
- Age: {user_profile['age']}
- Fitness Level: {user_profile['fitness_level']}
- Goals: {', '.join(user_profile['goals'])}
- Medical Conditions: {', '.join(user_profile.get('medical_conditions', [])) or 'None'}

WORKOUT TYPE: {workout_type}

AVAILABLE EXERCISES:
{json.dumps(exercise_list, indent=2)}
