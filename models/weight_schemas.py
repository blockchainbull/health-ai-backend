# models/weight_schemas.py
from pydantic import BaseModel
from typing import Optional

class WeightEntryCreate(BaseModel):
    user_id: str
    date: str
    weight: float
    notes: Optional[str] = None
    body_fat_percentage: Optional[float] = None
    muscle_mass_kg: Optional[float] = None

class WeightEntryUpdate(BaseModel):
    weight: Optional[float] = None
    notes: Optional[str] = None
    body_fat_percentage: Optional[float] = None
    muscle_mass_kg: Optional[float] = None

class WeightEntryResponse(BaseModel):
    id: str
    user_id: str
    date: str
    weight: float
    notes: Optional[str]
    body_fat_percentage: Optional[float]
    muscle_mass_kg: Optional[float]
    created_at: Optional[str]
    updated_at: Optional[str]