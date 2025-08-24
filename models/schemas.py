# models/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    activity_level: Optional[str] = None

class UserCreate(BaseModel):
    """For user registration"""
    name: str
    email: EmailStr
    password: str
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    activity_level: Optional[str] = None
    bmi: Optional[float] = None
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    
    # Period tracking
    has_periods: Optional[bool] = None
    last_period_date: Optional[str] = None
    cycle_length: Optional[int] = None
    period_length: Optional[int] = 5
    cycle_length_regular: Optional[bool] = None
    pregnancy_status: Optional[str] = None
    period_tracking_preference: Optional[str] = None
    
    # Goals
    primary_goal: Optional[str] = None
    fitness_goal: Optional[str] = None
    weight_goal: Optional[str] = None
    target_weight: Optional[float] = None
    goal_timeline: Optional[str] = None
    
    # Sleep
    sleep_hours: Optional[float] = 7.0
    bedtime: Optional[str] = None
    wakeup_time: Optional[str] = None
    sleep_issues: Optional[List[str]] = []
    
    daily_step_goal: Optional[int] = 10000

    # Nutrition
    dietary_preferences: Optional[List[str]] = []
    water_intake: Optional[float] = 2.0
    medical_conditions: Optional[List[str]] = []
    other_medical_condition: Optional[str] = None
    
    # Exercise
    preferred_workouts: Optional[List[str]] = []
    workout_frequency: Optional[int] = 3
    workout_duration: Optional[int] = 30
    workout_location: Optional[str] = None
    available_equipment: Optional[List[str]] = []
    fitness_level: Optional[str] = "Beginner"
    has_trainer: Optional[bool] = False

class UserUpdate(BaseModel):
    """For user profile updates"""
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    activity_level: Optional[str] = None
    bmi: Optional[float] = None
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    
    # Period tracking
    has_periods: Optional[bool] = None
    last_period_date: Optional[str] = None
    cycle_length: Optional[int] = None
    period_length: Optional[int] = None
    cycle_length_regular: Optional[bool] = None
    pregnancy_status: Optional[str] = None
    period_tracking_preference: Optional[str] = None
    
    # Goals
    primary_goal: Optional[str] = None
    fitness_goal: Optional[str] = None
    weight_goal: Optional[str] = None
    target_weight: Optional[float] = None
    goal_timeline: Optional[str] = None
    
    # Sleep
    sleep_hours: Optional[float] = None
    bedtime: Optional[str] = None
    wakeup_time: Optional[str] = None
    sleep_issues: Optional[List[str]] = None
    
    # Step goal - NEW
    daily_step_goal: Optional[int] = None

    # Nutrition
    dietary_preferences: Optional[List[str]] = None
    water_intake: Optional[float] = None
    medical_conditions: Optional[List[str]] = None
    other_medical_condition: Optional[str] = None
    
    # Exercise
    preferred_workouts: Optional[List[str]] = None
    workout_frequency: Optional[int] = None
    workout_duration: Optional[int] = None
    workout_location: Optional[str] = None
    available_equipment: Optional[List[str]] = None
    fitness_level: Optional[str] = None
    has_trainer: Optional[bool] = None

class UserResponse(BaseModel):
    """For API responses"""
    id: str
    name: str
    email: str
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    activity_level: Optional[str] = None
    daily_step_goal: Optional[int] = None
    bmi: Optional[float] = None
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    primary_goal: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserLoginResponse(BaseModel):
    success: bool
    user: Optional[UserResponse] = None
    message: Optional[str] = None
    error: Optional[str] = None