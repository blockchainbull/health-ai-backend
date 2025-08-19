# models/sleep_schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SleepEntryCreate(BaseModel):
    user_id: str
    date: str
    bedtime: Optional[str] = None
    wake_time: Optional[str] = None
    total_hours: float = 0.0
    quality_score: float = 0.0
    deep_sleep_hours: float = 0.0
    sleep_issues: Optional[List[str]] = []
    notes: Optional[str] = None

class SleepEntryUpdate(BaseModel):
    bedtime: Optional[str] = None
    wake_time: Optional[str] = None
    total_hours: Optional[float] = None
    quality_score: Optional[float] = None
    deep_sleep_hours: Optional[float] = None
    sleep_issues: Optional[List[str]] = None
    notes: Optional[str] = None

class SleepEntryResponse(BaseModel):
    id: str
    user_id: str
    date: str
    bedtime: Optional[str]
    wake_time: Optional[str]
    total_hours: float
    quality_score: float
    deep_sleep_hours: float
    sleep_issues: List[str]
    notes: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]