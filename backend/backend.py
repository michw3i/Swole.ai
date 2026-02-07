from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import httpx
import uuid
import json
import os 
from enum import Enum
import shutil
from pathlib import Path

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

# ============ LLM CONFIGURATION ============
# Switch between providers: 'openai' or 'daedalus'
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'daedalus')

if LLM_PROVIDER == 'daedalus':
    openai_client = OpenAI(
        api_key=os.getenv('DAEDALUS_API_KEY'),
        base_url=os.getenv('DAEDALUS_BASE_URL', 'https://api.daedalus-lab.com/v1')
    )
    CHAT_MODEL = os.getenv('DAEDALUS_MODEL', 'daedalus-chat')
else:
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    CHAT_MODEL = "gpt-4o-mini"

print(f"🤖 Using LLM Provider: {LLM_PROVIDER}, Model: {CHAT_MODEL}")
# ==========================================

from supabase import create_client, Client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)


# ------------------------ FastAPI ----------------------------
app = FastAPI(
    title="Swole.ai",
    description="Supabase + Daedalus Lab + Wger integration",
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
    UPPER_BODY = "upper_body"
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
    medical_conditions: Optional[List[str]] = []

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

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    image: Optional[str] = None


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
                    params={"language": 2, "category": category, "limit": limit}
                )
                if response.status_code == 200:
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
                f"{WGER_BASE_URL}/exerciseimage/",
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


# ------------- AI Workout Generation ---------------
async def generate_ai_workout(
    user_profile: Dict,
    workout_type: str,
    duration_minutes: int,
    available_exercises: List[Dict]
) -> Dict:
    """Use AI to generate intelligent workout plan"""
    
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

INSTRUCTIONS:
1. Select 4-6 appropriate exercises from the list above
2. Order them logically (warm-up → intense → cool-down)
3. Assign sets, reps, and rest periods based on fitness level
4. Provide 3-4 specific coaching cues per exercise
5. Calculate estimated calories burned

Return ONLY valid JSON with this structure:
{{
  "exercises": [
    {{
      "id": <exercise_id>,
      "name": "<exercise_name>",
      "sets": <number>,
      "reps": <number>,
      "rest_seconds": <number>,
      "coaching_cues": ["<cue1>", "<cue2>", "<cue3>"],
      "why_chosen": "<brief reason>"
    }}
  ],
  "estimated_calories": <number>,
  "workout_notes": "<motivational message>"
}}"""

    try:
        response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert personal trainer who creates safe, effective workouts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Remove markdown if present
        if ai_response.startswith("```json"):
            ai_response = ai_response.replace("```json", "").replace("```", "").strip()
        if ai_response.startswith("```"):
            ai_response = ai_response.replace("```", "").strip()
        
        workout_plan = json.loads(ai_response)
        
        # Enrich with images and videos
        for exercise in workout_plan["exercises"]:
            exercise_id = exercise["id"]
            exercise["images"] = await get_exercise_images(exercise_id)
            exercise["videos"] = await get_exercise_videos(exercise_id)
            
            # Get full data
            matching_ex = next((ex for ex in available_exercises if ex.get("id") == exercise_id), None)
            if matching_ex:
                exercise["muscles"] = [m.get("name") for m in matching_ex.get("muscles", [])]
                exercise["equipment"] = [e.get("name") for e in matching_ex.get("equipment", [])]
                exercise["description"] = matching_ex.get("description", "")
        
        return workout_plan
    
    except Exception as e:
        print(f"AI error: {e}")
        # Fallback
        return fallback_workout(available_exercises, duration_minutes, user_profile)


def fallback_workout(exercises: List[Dict], duration: int, profile: Dict) -> Dict:
    """Simple fallback if AI fails"""
    import random
    
    num_exercises = 4 if duration <= 30 else 6
    selected = random.sample(exercises[:20], min(num_exercises, len(exercises)))
    
    sets = 2 if profile['fitness_level'] == 'beginner' else 3
    reps = 10 if profile['fitness_level'] == 'beginner' else 12
    
    return {
        "exercises": [
            {
                "id": ex.get("id"),
                "name": ex.get("name"),
                "sets": sets,
                "reps": reps,
                "rest_seconds": 60,
                "coaching_cues": ["Maintain proper form", "Control breathing", "Start light"],
                "why_chosen": "Selected for balanced workout",
                "images": [],
                "videos": [],
                "muscles": [m.get("name") for m in ex.get("muscles", [])],
                "equipment": [e.get("name") for e in ex.get("equipment", [])]
            }
            for ex in selected
        ],
        "estimated_calories": duration * 5,
        "workout_notes": "Great workout ahead!"
    }


# --------------- API Endpoints --------------------

@app.get("/")
async def root():
    return {
        "message": "AI Fitness Trainer API",
        "version": "3.0",
        "database": "Supabase",
        "ai": LLM_PROVIDER,
        "model": CHAT_MODEL,
        "exercises": "Wger API",
        "docs": "/docs"
    }


@app.post("/api/users", status_code=201)
async def create_user(profile: UserProfile):
    """Create user profile in Supabase"""
    
    user_id = str(uuid.uuid4())
    bmi = profile.weight_kg / ((profile.height_cm / 100) ** 2)
    
    try:
        result = supabase.table('users').insert({
            'user_id': user_id,
            'name': profile.name,
            'age': profile.age,
            'gender': profile.gender.value,
            'weight_kg': profile.weight_kg,
            'height_cm': profile.height_cm,
            'fitness_level': profile.fitness_level.value,
            'goals': profile.goals,
            'medical_conditions': profile.medical_conditions,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        return {
            "user_id": user_id,
            "message": f"Welcome, {profile.name}!",
            "bmi": round(bmi, 1),
            "profile": profile.dict()
        }
    
    except Exception as e:
        print(f"Supabase error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """Get user profile from Supabase"""
    
    try:
        result = supabase.table('users').select('*').eq('user_id', user_id).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = result.data[0]
        return {
            "user_id": user['user_id'],
            "name": user['name'],
            "age": user['age'],
            "gender": user['gender'],
            "weight_kg": user['weight_kg'],
            "height_cm": user['height_cm'],
            "fitness_level": user['fitness_level'],
            "goals": user['goals'],
            "medical_conditions": user['medical_conditions']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Supabase error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/workout-types")
async def get_workout_types():
    """Get available workout types"""
    types = [
        {"value": "cardio", "label": "Cardio", "description": "Heart-pumping cardiovascular exercises"},
        {"value": "upper_body", "label": "Upper Body", "description": "Chest, back, shoulders, and arms"},
        {"value": "lower_body", "label": "Lower Body", "description": "Legs, glutes, and calves"},
        {"value": "full_body", "label": "Full Body", "description": "Complete workout hitting all muscle groups"},
        {"value": "arms", "label": "Arms", "description": "Biceps and triceps focused"},
        {"value": "legs", "label": "Legs", "description": "Quads, hamstrings, and calves"},
        {"value": "chest", "label": "Chest", "description": "Pectoral muscle development"},
        {"value": "back", "label": "Back", "description": "Lat and upper back training"},
        {"value": "shoulders", "label": "Shoulders", "description": "Deltoid strengthening"},
        {"value": "abs", "label": "Abs/Core", "description": "Core strength and stability"},
        {"value": "stretching", "label": "Stretching", "description": "Flexibility and mobility"}
    ]
    return {"workout_types": types}


@app.post("/api/workouts/generate")
async def generate_workout(request: WorkoutRequest):
    """Generate AI-powered workout and save to Supabase"""
    
    try:
        # Get user profile from Supabase
        user_result = supabase.table('users').select('*').eq('user_id', request.user_id).execute()
        
        if not user_result.data or len(user_result.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = user_result.data[0]
        user_profile = {
            "name": user['name'],
            "age": user['age'],
            "gender": user['gender'],
            "weight_kg": user['weight_kg'],
            "height_cm": user['height_cm'],
            "fitness_level": user['fitness_level'],
            "goals": user['goals'],
            "medical_conditions": user.get('medical_conditions', [])
        }
        
        # Fetch exercises from Wger
        available_exercises = await fetch_wger_exercises(request.workout_type.value)
        
        if not available_exercises:
            raise HTTPException(status_code=404, detail="No exercises found")
        
        # Generate workout with AI
        workout_plan = await generate_ai_workout(
            user_profile,
            request.workout_type.value,
            request.duration_minutes,
            available_exercises
        )
        
        # Save to Supabase
        workout_id = str(uuid.uuid4())
        
        supabase.table('workouts').insert({
            'workout_id': workout_id,
            'user_id': request.user_id,
            'workout_type': request.workout_type.value,
            'duration_minutes': request.duration_minutes,
            'exercises': workout_plan['exercises'],
            'estimated_calories': workout_plan['estimated_calories'],
            'workout_notes': workout_plan['workout_notes'],
            'created_at': datetime.now().isoformat(),
            'completed': False
        }).execute()
        
        return {
            "workout_id": workout_id,
            "user_name": user_profile["name"],
            "workout_type": request.workout_type.value,
            "duration_minutes": request.duration_minutes,
            **workout_plan
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating workout: {str(e)}")


@app.get("/api/workouts/{workout_id}")
async def get_workout(workout_id: str):
    """Get workout details from Supabase"""
    
    try:
        result = supabase.table('workouts').select('*').eq('workout_id', workout_id).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Workout not found")
        
        workout = result.data[0]
        return {
            "workout_id": workout['workout_id'],
            "user_id": workout['user_id'],
            "workout_type": workout['workout_type'],
            "duration_minutes": workout['duration_minutes'],
            "exercises": workout['exercises'],
            "estimated_calories": workout['estimated_calories'],
            "workout_notes": workout['workout_notes'],
            "completed": workout['completed'],
            "created_at": workout['created_at']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Supabase error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/workouts/{workout_id}/feedback")
async def submit_feedback(workout_id: str, feedback: WorkoutFeedback):
    """Submit workout feedback to Supabase with AI recommendation"""
    
    try:
        # Update workout in Supabase
        supabase.table('workouts').update({
            'completed': feedback.completed,
            'feedback': {
                'difficulty_rating': feedback.difficulty_rating,
                'enjoyed': feedback.enjoyed,
                'notes': feedback.notes
            }
        }).eq('workout_id', workout_id).execute()
        
        # Generate AI recommendation
        try:
            prompt = f"""Based on this workout feedback, provide a brief (2-3 sentences) motivational recommendation:

Completed: {feedback.completed}
Difficulty (1-10): {feedback.difficulty_rating}
Enjoyed: {feedback.enjoyed}
Notes: {feedback.notes or 'None'}

Be encouraging and specific about adjustments if needed."""

            response = openai_client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.8
            )
            
            recommendation = response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"AI recommendation error: {e}")
            # Fallback
            if feedback.difficulty_rating >= 8:
                recommendation = "That was intense! Next time we'll dial it back for better recovery."
            elif feedback.difficulty_rating <= 3:
                recommendation = "You crushed it! Next workout, we'll increase the challenge."
            else:
                recommendation = "Perfect intensity! Keep up the amazing work!"
        
        return {
            "message": "Feedback recorded!",
            "recommendation": recommendation
        }
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")


@app.get("/api/users/{user_id}/workouts")
async def get_user_workouts(user_id: str, limit: int = 10):
    """Get user's workout history from Supabase"""
    
    try:
        result = supabase.table('workouts')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "user_id": user_id,
            "total_workouts": len(result.data),
            "workouts": result.data
        }
    
    except Exception as e:
        print(f"Supabase error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ----------------------- Chat Endpoint ------------------------

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat with AI fitness trainer"""
    
    try:
        system_prompt = """You are an expert AI fitness trainer. You help users with:
- Workout recommendations and form tips
- Nutrition advice
- Fitness goal setting
- Exercise modifications for injuries
- Motivation and encouragement

Be friendly, encouraging, and provide specific, actionable advice."""

        openai_messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history (last 10 messages to stay within token limits)
        for msg in request.messages[-10:]:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=openai_messages,
            temperature=0.7,
            max_tokens=500
        )
        
        assistant_message = response.choices[0].message.content.strip()
        
        return {
            "content": assistant_message,
            "role": "assistant"
        }
    
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# ----------------------- Health Check ------------------------

@app.get("/api/health")
async def health_check():
    """Check if all services are working"""
    
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "llm_provider": LLM_PROVIDER,
        "llm_model": CHAT_MODEL,
        "services": {}
    }
    
    # Check Supabase
    try:
        supabase.table('users').select('count').limit(1).execute()
        health["services"]["supabase"] = "✅ connected"
    except:
        health["services"]["supabase"] = "❌ error"
        health["status"] = "unhealthy"
    
    # Check LLM API
    if LLM_PROVIDER == 'daedalus':
        api_key = os.getenv('DAEDALUS_API_KEY')
        if api_key:
            health["services"]["llm_api"] = "✅ Daedalus configured"
        else:
            health["services"]["llm_api"] = "⚠️ Daedalus API key not set"
    else:
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            health["services"]["llm_api"] = "✅ OpenAI configured"
        else:
            health["services"]["llm_api"] = "⚠️ OpenAI API key not set"
    
    # Check Wger API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{WGER_BASE_URL}/exercise/", params={"limit": 1})
            if response.status_code == 200:
                health["services"]["wger_api"] = "✅ accessible"
            else:
                health["services"]["wger_api"] = "⚠️ slow response"
    except:
        health["services"]["wger_api"] = "❌ unreachable"
    
    return health


# ------------------------- Image Upload --------------------------

@app.post("/api/upload-image")
async def upload_image(image: UploadFile = File(...)):
    """Upload user image for workout analysis"""
    
    try:
        # Validate file type
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_extension = image.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save the file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        return {
            "message": "Image uploaded successfully",
            "filename": unique_filename,
            "original_filename": image.filename,
            "path": str(file_path),
            "size_bytes": file_path.stat().st_size
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ---------------------------- Run Server ------------------------

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 70)
    print("  🏋️  AI FITNESS TRAINER - Swole.ai")
    print("=" * 70)
    print(f"\n  💾 Database: Supabase (Cloud PostgreSQL)")
    print(f"  🤖 AI Provider: {LLM_PROVIDER}")
    print(f"  📦 Model: {CHAT_MODEL}")
    print(f"  💪 Exercises: Wger API")
    print(f"\n  Server: http://localhost:8000")
    print(f"  Docs: http://localhost:8000/docs")
    print(f"  Health: http://localhost:8000/api/health")
    print("\n" + "=" * 70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)