# models/step_schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StepEntryCreate(BaseModel):
    userId: str
    date: str
    steps: int = 0
    goal: int = 10000
    caloriesBurned: float = 0.0
    distanceKm: float = 0.0
    activeMinutes: int = 0
    sourceType: str = 'manual'
    lastSynced: Optional[str] = None

class StepEntryUpdate(BaseModel):
    steps: Optional[int] = None
    goal: Optional[int] = None
    caloriesBurned: Optional[float] = None
    distanceKm: Optional[float] = None
    activeMinutes: Optional[int] = None
    sourceType: Optional[str] = None
    lastSynced: Optional[str] = None

class StepEntryResponse(BaseModel):
    id: str
    userId: str
    date: str
    steps: int
    goal: int
    caloriesBurned: float
    distanceKm: float
    activeMinutes: int
    sourceType: str
    lastSynced: Optional[str]
    createdAt: Optional[str]
    updatedAt: Optional[str]