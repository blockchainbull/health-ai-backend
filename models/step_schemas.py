# models/step_schemas.py
from pydantic import BaseModel
from typing import Optional

class StepEntryCreate(BaseModel):
    userid: str  # Changed from userId
    date: str
    steps: int = 0
    goal: int = 10000
    calories_burned: float = 0.0  # Changed from caloriesBurned
    distance_km: float = 0.0      # Changed from distanceKm
    active_minutes: int = 0       # Changed from activeMinutes
    source_type: str = 'manual'   # Changed from sourceType
    last_synced: Optional[str] = None  # Changed from lastSynced

class StepEntryUpdate(BaseModel):
    steps: Optional[int] = None
    goal: Optional[int] = None
    calories_burned: Optional[float] = None  # Changed from caloriesBurned
    distance_km: Optional[float] = None      # Changed from distanceKm
    active_minutes: Optional[int] = None     # Changed from activeMinutes
    source_type: Optional[str] = None        # Changed from sourceType
    last_synced: Optional[str] = None        # Changed from lastSynced

class StepEntryResponse(BaseModel):
    id: str
    userid: str  # Changed from userId
    date: str
    steps: int
    goal: int
    calories_burned: float  # Changed from caloriesBurned
    distance_km: float      # Changed from distanceKm
    active_minutes: int     # Changed from activeMinutes
    source_type: str        # Changed from sourceType
    last_synced: Optional[str]  # Changed from lastSynced
    created_at: Optional[str]   # Changed from createdAt
    updated_at: Optional[str]   # Changed from updatedAt