# models/exercise_schemas.py
from pydantic import BaseModel
from typing import Optional

class ExerciseLogCreate(BaseModel):
    user_id: str
    exercise_name: str
    exercise_type: str
    duration_minutes: int
    calories_burned: Optional[float] = None
    distance_km: Optional[float] = None
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    intensity: str = 'moderate'
    notes: Optional[str] = None
    exercise_date: Optional[str] = None

class ExerciseLogResponse(BaseModel):
    id: str
    user_id: str
    exercise_name: str
    exercise_type: str
    duration_minutes: int
    calories_burned: Optional[float]
    distance_km: Optional[float]
    sets: Optional[int]
    reps: Optional[int]
    weight_kg: Optional[float]
    intensity: str
    notes: Optional[str]
    exercise_date: str
    created_at: Optional[str]
    updated_at: Optional[str]