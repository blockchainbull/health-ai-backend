# models/step_schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class StepEntryCreate(BaseModel):
    user_id: str = Field(alias="userId")
    date: str
    steps: int = 0
    goal: int = 10000
    calories_burned: float = Field(default=0.0, alias="caloriesBurned")
    distance_km: float = Field(default=0.0, alias="distanceKm")
    active_minutes: int = Field(default=0, alias="activeMinutes")
    source_type: str = Field(default='manual', alias="sourceType")
    last_synced: Optional[str] = Field(default=None, alias="lastSynced")

    class Config:
        allow_population_by_field_name = True

class StepEntryUpdate(BaseModel):
    steps: Optional[int] = None
    goal: Optional[int] = None
    calories_burned: Optional[float] = Field(default=None, alias="caloriesBurned")
    distance_km: Optional[float] = Field(default=None, alias="distanceKm")
    active_minutes: Optional[int] = Field(default=None, alias="activeMinutes")
    source_type: Optional[str] = Field(default=None, alias="sourceType")
    last_synced: Optional[str] = Field(default=None, alias="lastSynced")

    class Config:
        allow_population_by_field_name = True

class StepEntryResponse(BaseModel):
    id: str
    user_id: str = Field(alias="userId")
    date: str
    steps: int
    goal: int
    calories_burned: float = Field(alias="caloriesBurned")
    distance_km: float = Field(alias="distanceKm")
    active_minutes: int = Field(alias="activeMinutes")
    source_type: str = Field(alias="sourceType")
    last_synced: Optional[str] = Field(alias="lastSynced")
    created_at: Optional[str] = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        allow_population_by_field_name = True