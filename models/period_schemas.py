# models/period_schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class PeriodEntryCreate(BaseModel):
    user_id: str
    start_date: str
    end_date: Optional[str] = None
    flow_intensity: str = 'Medium'
    symptoms: Optional[List[str]] = []
    mood: Optional[str] = None
    notes: Optional[str] = None

class PeriodEntryResponse(BaseModel):
    id: str
    user_id: str
    start_date: str
    end_date: Optional[str]
    flow_intensity: str
    symptoms: List[str]
    mood: Optional[str]
    notes: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]