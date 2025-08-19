# models/water_schemas.py
from pydantic import BaseModel
from typing import Optional

class WaterEntryCreate(BaseModel):
    user_id: str
    date: str
    glasses_consumed: int = 0
    total_ml: float = 0.0
    target_ml: float = 2000.0
    notes: Optional[str] = None

class WaterEntryUpdate(BaseModel):
    glasses_consumed: Optional[int] = None
    total_ml: Optional[float] = None
    target_ml: Optional[float] = None
    notes: Optional[str] = None

class WaterEntryResponse(BaseModel):
    id: str
    user_id: str
    date: str
    glasses_consumed: int
    total_ml: float
    target_ml: float
    notes: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]