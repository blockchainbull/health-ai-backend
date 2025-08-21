# models/supplement_schemas.py
from pydantic import BaseModel
from typing import Optional, List

class SupplementPreferenceCreate(BaseModel):
    user_id: str
    supplements: List[dict]

class SupplementLogCreate(BaseModel):
    user_id: str
    supplement_name: str
    date: str
    taken: bool = False
    dosage: Optional[str] = None
    time_taken: Optional[str] = None
    notes: Optional[str] = None

class SupplementPreferenceResponse(BaseModel):
    id: str
    user_id: str
    supplement_name: str
    dosage: Optional[str]
    frequency: str
    preferred_time: str
    notes: Optional[str]
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]

class SupplementLogResponse(BaseModel):
    id: str
    user_id: str
    supplement_name: str
    date: str
    taken: bool
    dosage: Optional[str]
    time_taken: Optional[str]
    notes: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]