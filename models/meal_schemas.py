# models/meal_schemas.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class MealAnalysisRequest(BaseModel):
    user_id: str
    food_item: str
    quantity: str
    preparation: Optional[str] = ""
    meal_type: Optional[str] = "snack"  # breakfast, lunch, dinner, snack
    meal_date: Optional[str] = None  # ISO format

class MealEntryResponse(BaseModel):
    id: str
    user_id: str
    food_item: str
    quantity: str
    meal_type: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float
    sodium_mg: float
    nutrition_notes: Optional[str] = None
    healthiness_score: Optional[int] = None
    suggestions: Optional[str] = None
    meal_date: str
    logged_at: str

class MealHistoryResponse(BaseModel):
    meals: list[MealEntryResponse]
    total_count: int
    date_range: Optional[str] = None

class DailyNutritionResponse(BaseModel):
    date: str
    calories_consumed: float
    protein_g: float
    carbs_g: float
    fat_g: float
    water_liters: float
    meals_logged: int
    meals: list[MealEntryResponse]