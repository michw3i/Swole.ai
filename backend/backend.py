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
supabase_key = os.getenv('SUPABASE_KEY', 'sb_publishable_WkRofQE-nSe1W5dWKTO2Ng_NFNCwgEY')
supabase: Client = create_client(supabase_url, supabase_key)

# FastAPI

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

# Pydantic Models
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

class UserProfile