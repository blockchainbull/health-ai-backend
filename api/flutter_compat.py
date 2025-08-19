# api/flutter_compat.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid

from models.water_schemas import WaterEntryCreate
from services.supabase_service import get_supabase_service
from api.users import hash_password, verify_password
from services.openai_service import get_openai_service
from models.step_schemas import StepEntryCreate
from models.weight_schemas import WeightEntryCreate

router = APIRouter()

# Flutter-compatible models
class HealthUserCreate(BaseModel):
    name: str
    email: str
    password: str
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    activityLevel: Optional[str] = None
    bmi: Optional[float] = None
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    
    # Flutter expects these exact field names
    hasPeriods: Optional[bool] = None
    lastPeriodDate: Optional[str] = None
    cycleLength: Optional[int] = None
    cycleLengthRegular: Optional[bool] = None
    pregnancyStatus: Optional[str] = None
    periodTrackingPreference: Optional[str] = None
    
    primaryGoal: Optional[str] = None
    weightGoal: Optional[str] = None
    targetWeight: Optional[float] = None
    goalTimeline: Optional[str] = None
    
    sleepHours: Optional[float] = 7.0
    bedtime: Optional[str] = None
    wakeupTime: Optional[str] = None
    sleepIssues: Optional[list] = []
    
    dietaryPreferences: Optional[list] = []
    waterIntake: Optional[float] = 2.0
    medicalConditions: Optional[list] = []
    otherMedicalCondition: Optional[str] = None
    
    preferredWorkouts: Optional[list] = []
    workoutFrequency: Optional[int] = 3
    workoutDuration: Optional[int] = 30
    workoutLocation: Optional[str] = None
    availableEquipment: Optional[list] = []
    fitnessLevel: Optional[str] = "Beginner"
    hasTrainer: Optional[bool] = False

class HealthUserResponse(BaseModel):
    success: bool
    userId: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    userProfile: Optional[Dict[str, Any]] = None

class HealthLoginRequest(BaseModel):
    email: str
    password: str

class UnifiedOnboardingRequest(BaseModel):
    basicInfo: Dict[str, Any]
    periodCycle: Optional[Dict[str, Any]] = {}
    primaryGoal: Optional[str] = None
    weightGoal: Optional[Dict[str, Any]] = {}
    sleepInfo: Optional[Dict[str, Any]] = {}
    dietaryPreferences: Optional[Dict[str, Any]] = {}
    workoutPreferences: Optional[Dict[str, Any]] = {}
    exerciseSetup: Optional[Dict[str, Any]] = {}

@router.get("/check")
async def health_check():
    """Health check for mobile app"""
    return {"status": "ok", "message": "Health API is running"}

@router.post("/users", response_model=HealthUserResponse)
async def create_health_user(user_profile: HealthUserCreate):
    """Create user profile for mobile app - Flutter compatible"""
    try:
        print(f"🔍 Flutter user registration: {user_profile.email}")
        
        supabase_service = get_supabase_service()
        
        # Check if user already exists
        existing_user = await supabase_service.get_user_by_email(user_profile.email)
        if existing_user:
            return HealthUserResponse(
                success=False,
                error="Email already exists"
            )
        
        # Convert Flutter model to our backend format
        user_dict = {
            'id': str(uuid.uuid4()),
            'name': user_profile.name,
            'email': user_profile.email,
            'password_hash': hash_password(user_profile.password),
            'gender': user_profile.gender,
            'age': user_profile.age,
            'height': user_profile.height,
            'weight': user_profile.weight,
            'activity_level': user_profile.activityLevel,
            'bmi': user_profile.bmi,
            'bmr': user_profile.bmr,
            'tdee': user_profile.tdee,
            
            # Period tracking
            'has_periods': user_profile.hasPeriods,
            'last_period_date': user_profile.lastPeriodDate,
            'cycle_length': user_profile.cycleLength,
            'cycle_length_regular': user_profile.cycleLengthRegular,
            'pregnancy_status': user_profile.pregnancyStatus,
            'period_tracking_preference': user_profile.periodTrackingPreference,
            
            # Goals
            'primary_goal': user_profile.primaryGoal,
            'weight_goal': user_profile.weightGoal,
            'target_weight': user_profile.targetWeight,
            'goal_timeline': user_profile.goalTimeline,
            
            # Sleep
            'sleep_hours': user_profile.sleepHours,
            'bedtime': user_profile.bedtime,
            'wakeup_time': user_profile.wakeupTime,
            'sleep_issues': user_profile.sleepIssues or [],
            
            # Nutrition
            'dietary_preferences': user_profile.dietaryPreferences or [],
            'water_intake': user_profile.waterIntake,
            'medical_conditions': user_profile.medicalConditions or [],
            'other_medical_condition': user_profile.otherMedicalCondition,
            
            # Exercise
            'preferred_workouts': user_profile.preferredWorkouts or [],
            'workout_frequency': user_profile.workoutFrequency,
            'workout_duration': user_profile.workoutDuration,
            'workout_location': user_profile.workoutLocation,
            'available_equipment': user_profile.availableEquipment or [],
            'fitness_level': user_profile.fitnessLevel,
            'has_trainer': user_profile.hasTrainer,
            
            'preferences': {},
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Create user in Supabase
        created_user = await supabase_service.create_user(user_dict)
        
        return HealthUserResponse(
            success=True,
            userId=created_user['id'],
            message="User registered successfully"
        )
        
    except Exception as e:
        print(f"❌ Error creating Flutter user: {e}")
        return HealthUserResponse(
            success=False,
            error=str(e)
        )

@router.post("/login", response_model=HealthUserResponse)
async def login_health_user(login_data: HealthLoginRequest):
    """Login for mobile app users"""
    try:
        print(f"🔍 Flutter login attempt: {login_data.email}")
        
        supabase_service = get_supabase_service()
        
        # Get user by email
        user = await supabase_service.get_user_by_email(login_data.email)
        if not user:
            return HealthUserResponse(
                success=False,
                error="Invalid credentials"
            )
        
        # Verify password
        if not verify_password(login_data.password, user['password_hash']):
            return HealthUserResponse(
                success=False,
                error="Invalid credentials"
            )
        
        return HealthUserResponse(
            success=True,
            userId=user['id'],
            message="Login successful"
        )
        
    except Exception as e:
        print(f"❌ Error during Flutter login: {e}")
        return HealthUserResponse(
            success=False,
            error=str(e)
        )

@router.post("/onboarding/complete", response_model=HealthUserResponse)
async def complete_flutter_onboarding(onboarding_data: UnifiedOnboardingRequest):
    """Complete onboarding process for Flutter app"""
    try:
        print("🔍 Flutter onboarding data received")
        
        basic_info = onboarding_data.basicInfo
        period_cycle = onboarding_data.periodCycle or {}
        weight_goal = onboarding_data.weightGoal or {}
        sleep_info = onboarding_data.sleepInfo or {}
        dietary_prefs = onboarding_data.dietaryPreferences or {}
        workout_prefs = onboarding_data.workoutPreferences or {}
        exercise_setup = onboarding_data.exerciseSetup or {}
        
        # Convert to HealthUserCreate format
        user_profile = HealthUserCreate(
            name=basic_info.get('name'),
            email=basic_info.get('email'),
            password=basic_info.get('password'),
            gender=basic_info.get('gender'),
            age=basic_info.get('age'),
            height=basic_info.get('height'),
            weight=basic_info.get('weight'),
            activityLevel=basic_info.get('activityLevel'),
            bmi=basic_info.get('bmi'),
            bmr=basic_info.get('bmr'),
            tdee=basic_info.get('tdee'),
            
            # Period data
            hasPeriods=period_cycle.get('hasPeriods'),
            lastPeriodDate=period_cycle.get('lastPeriodDate'),
            cycleLength=period_cycle.get('cycleLength'),
            cycleLengthRegular=period_cycle.get('cycleLengthRegular'),
            pregnancyStatus=period_cycle.get('pregnancyStatus'),
            periodTrackingPreference=period_cycle.get('trackingPreference'),
            
            # Goals
            primaryGoal=onboarding_data.primaryGoal,
            weightGoal=weight_goal.get('weightGoal'),
            targetWeight=weight_goal.get('targetWeight'),
            goalTimeline=weight_goal.get('timeline'),
            
            # Sleep
            sleepHours=sleep_info.get('sleepHours', 7.0),
            bedtime=sleep_info.get('bedtime'),
            wakeupTime=sleep_info.get('wakeupTime'),
            sleepIssues=sleep_info.get('sleepIssues', []),
            
            # Nutrition
            dietaryPreferences=dietary_prefs.get('dietaryPreferences', []),
            waterIntake=dietary_prefs.get('waterIntake', 2.0),
            medicalConditions=dietary_prefs.get('medicalConditions', []),
            otherMedicalCondition=dietary_prefs.get('otherCondition'),
            
            # Exercise
            preferredWorkouts=workout_prefs.get('workoutTypes', []),
            workoutFrequency=workout_prefs.get('frequency', 3),
            workoutDuration=workout_prefs.get('duration', 30),
            workoutLocation=exercise_setup.get('workoutLocation'),
            availableEquipment=exercise_setup.get('equipment', []),
            fitnessLevel=exercise_setup.get('fitnessLevel', 'Beginner'),
            hasTrainer=exercise_setup.get('hasTrainer', False)
        )
        
        # Use the existing create_health_user function
        return await create_health_user(user_profile)
        
    except Exception as e:
        print(f"❌ Error completing Flutter onboarding: {e}")
        return HealthUserResponse(
            success=False,
            error=str(e)
        )

@router.get("/users/{user_id}", response_model=HealthUserResponse)
async def get_health_user_profile(user_id: str):
    """Get user profile for mobile app"""
    try:
        supabase_service = get_supabase_service()
        user = await supabase_service.get_user_by_id(user_id)
        
        if not user:
            return HealthUserResponse(
                success=False,
                error="User not found"
            )
        
        return HealthUserResponse(
            success=True,
            userId=user['id'],
            userProfile=user,
            message="User profile retrieved successfully"
        )
        
    except Exception as e:
        print(f"❌ Error getting Flutter user profile: {e}")
        return HealthUserResponse(
            success=False,
            error=str(e)
        )

@router.post("/auth/login")
async def auth_login(login_data: dict):
    """Login endpoint that matches Flutter's expected path"""
    try:
        email = login_data.get('email')
        password = login_data.get('password')
        
        print(f"🔐 Flutter auth login attempt for: {email}")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        supabase_service = get_supabase_service()
        
        # Get user by email
        user = await supabase_service.get_user_by_email(email)
        if not user:
            print(f"❌ User not found: {email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            print(f"❌ Invalid password for: {email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        print(f"✅ Login successful for: {email}")
        
        return {
            "success": True,
            "user": {
                "id": user['id'],
                "name": user['name'],
                "email": user['email'],
                "age": user.get('age'),
                "gender": user.get('gender'),
                "height": user.get('height'),
                "weight": user.get('weight'),
                "activity_level": user.get('activity_level'),
                "bmi": user.get('bmi'),
                "bmr": user.get('bmr'),
                "tdee": user.get('tdee')
            },
            "message": "Login successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/debug/meals/{user_id}/{date}")
async def debug_meal_data(user_id: str, date: str):
    """Debug endpoint to check raw meal data"""
    try:
        supabase_service = get_supabase_service()
        meals = await supabase_service.get_user_meals_by_date(user_id, date)
        
        print(f"🔍 Raw meal data for {user_id} on {date}:")
        for i, meal in enumerate(meals):
            print(f"  Meal {i+1}: {meal.get('food_item')}")
            print(f"    Raw meal data: {meal}")
            print(f"    fiber_g: {meal.get('fiber_g')} (type: {type(meal.get('fiber_g'))})")
            print(f"    sugar_g: {meal.get('sugar_g')} (type: {type(meal.get('sugar_g'))})")
            print(f"    sodium_mg: {meal.get('sodium_mg')} (type: {type(meal.get('sodium_mg'))})")
        
        return {
            "success": True,
            "raw_meals": meals,
            "count": len(meals)
        }
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/daily-summary/{user_id}")
async def get_daily_summary_flutter(user_id: str, date: str = None):
    """Get daily summary for Flutter app with all nutrition data"""
    try:
        if date:
            target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
        else:
            target_date = datetime.now().date()
        
        print(f"📊 Getting daily summary for user {user_id} on {target_date}")
        
        supabase_service = get_supabase_service()
        meals = await supabase_service.get_user_meals_by_date(user_id, str(target_date))
        
        # Calculate totals including fiber, sugar, sodium
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_fiber = 0
        total_sugar = 0
        total_sodium = 0
        
        # Calculate totals from all meals
        for meal in meals:
            total_calories += float(meal.get('calories', 0))
            total_protein += float(meal.get('protein_g', 0))
            total_carbs += float(meal.get('carbs_g', 0))
            total_fat += float(meal.get('fat_g', 0))
            total_fiber += float(meal.get('fiber_g', 0))
            total_sugar += float(meal.get('sugar_g', 0))
            total_sodium += float(meal.get('sodium_mg', 0))
        
        print(f"📊 Calculated totals - Fiber: {total_fiber}, Sugar: {total_sugar}, Sodium: {total_sodium}")
        
        response_data = {
            "success": True,
            "date": str(target_date),
            "totals": {
                "calories": float(total_calories),
                "protein_g": float(total_protein),
                "carbs_g": float(total_carbs),
                "fat_g": float(total_fat),
                "fiber_g": float(total_fiber),
                "sugar_g": float(total_sugar),
                "sodium_mg": float(total_sodium),
            },
            "meals": {
                "total_calories": float(total_calories),
                "calories_consumed": float(total_calories),
                "total_protein": float(total_protein),
                "protein_g": float(total_protein),
                "total_carbs": float(total_carbs),
                "carbs_g": float(total_carbs),
                "total_fat": float(total_fat),
                "fat_g": float(total_fat),
                "total_fiber": float(total_fiber),
                "fiber_g": float(total_fiber),
                "total_sugar": float(total_sugar),
                "sugar_g": float(total_sugar),
                "total_sodium": float(total_sodium),
                "sodium_mg": float(total_sodium),
                "meals_count": len(meals),
                "total_count": len(meals)
            }
        }
        
        print(f"📊 Returning response: {response_data}")
        return response_data
        
    except Exception as e:
        print(f"❌ Error getting daily summary: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meals/analyze")
async def analyze_meal_flutter(meal_data: dict):
    """Analyze meal for Flutter app"""
    try:
        print(f"🍽️ Flutter meal analysis: {meal_data}")
        
        # Extract data from Flutter format
        user_id = meal_data.get('user_id') or meal_data.get('userId')
        food_item = meal_data.get('food_item') or meal_data.get('foodItem') or meal_data.get('name')
        quantity = meal_data.get('quantity', '1 serving')
        meal_type = meal_data.get('meal_type', 'snack')
        preparation = meal_data.get('preparation', '')
        
        if not user_id or not food_item:
            raise HTTPException(status_code=400, detail="user_id and food_item are required")
        
        print(f"🍽️ Analyzing: {food_item} ({quantity}) for user {user_id}")
        
        # Get services
        supabase_service = get_supabase_service()
        openai_service = get_openai_service()
        
        # Get user context
        user = await supabase_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_context = {
            'weight': user.get('weight', 70),
            'primary_goal': user.get('primary_goal', 'maintain weight'),
            'activity_level': user.get('activity_level', 'moderate'),
            'tdee': user.get('tdee', 2000)
        }
        
        # Analyze with AI
        nutrition_data = await openai_service.analyze_meal(
            food_item=food_item,
            quantity=quantity,
            user_context=user_context
        )
        
        print(f"🔍 AI returned nutrition data: {nutrition_data}")
        print(f"    AI fiber_g: {nutrition_data.get('fiber_g')}")
        print(f"    AI sugar_g: {nutrition_data.get('sugar_g')}")
        print(f"    AI sodium_mg: {nutrition_data.get('sodium_mg')}")
        
        # Prepare meal entry
        meal_entry = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'food_item': food_item,
            'quantity': quantity,
            'preparation': preparation,
            'meal_type': meal_type,
            'calories': nutrition_data['calories'],
            'protein_g': nutrition_data['protein_g'],
            'carbs_g': nutrition_data['carbs_g'],
            'fat_g': nutrition_data['fat_g'],
            'fiber_g': nutrition_data['fiber_g'],
            'sugar_g': nutrition_data['sugar_g'],
            'sodium_mg': nutrition_data['sodium_mg'],
            'nutrition_data': nutrition_data,
            'data_source': 'ai',
            'confidence_score': 0.8,
            'meal_date': datetime.now().isoformat(),
            'logged_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        print(f"🔍 Meal entry to save: {meal_entry}")
        print(f"    Entry fiber_g: {meal_entry['fiber_g']}")
        print(f"    Entry sugar_g: {meal_entry['sugar_g']}")
        print(f"    Entry sodium_mg: {meal_entry['sodium_mg']}")
        
        # Save to database
        saved_meal = await supabase_service.create_meal_entry(meal_entry)
        
        print(f"🔍 Saved meal returned: {saved_meal}")
        print(f"    Saved fiber_g: {saved_meal.get('fiber_g')}")
        print(f"    Saved sugar_g: {saved_meal.get('sugar_g')}")
        print(f"    Saved sodium_mg: {saved_meal.get('sodium_mg')}")
        
        return {
            "success": True,
            "meal": {
                "id": saved_meal['id'],
                "name": saved_meal['food_item'],
                "quantity": saved_meal['quantity'],
                "calories": saved_meal['calories'],
                "protein": saved_meal['protein_g'],
                "carbs": saved_meal['carbs_g'],
                "fat": saved_meal['fat_g'],
                "fiber": saved_meal['fiber_g'],
                "sugar": saved_meal['sugar_g'],
                "sodium": saved_meal['sodium_mg'],
                "healthiness_score": nutrition_data.get('healthiness_score', 7),
                "suggestions": nutrition_data.get('suggestions', ''),
                "nutrition_notes": nutrition_data.get('nutrition_notes', ''),
                "logged_at": saved_meal['logged_at']
            },
            "message": "Meal analyzed and logged successfully"
        }
        
    except Exception as e:
        print(f"❌ Error analyzing Flutter meal: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meals/history/{user_id}")
async def get_meal_history_flutter(user_id: str, limit: int = 50, date: str = None):
    """Get meal history for Flutter app"""
    try:
        print(f"🍽️ Getting meal history for user: {user_id}, limit: {limit}, date: {date}")
        
        supabase_service = get_supabase_service()
        
        if date:
            date_only = date.split('T')[0]
            meals = await supabase_service.get_user_meals_by_date(user_id, date_only)
        else:
            meals = await supabase_service.get_user_meals(user_id, limit=limit)
        
        # Helper function to capitalize meal types
        def capitalize_meal_type(meal_type):
            if not meal_type:
                return "Snack"
            meal_type = str(meal_type).lower()
            if meal_type == "lunch":
                return "Lunch"
            elif meal_type == "breakfast":
                return "Breakfast"
            elif meal_type == "dinner":
                return "Dinner"
            else:
                return "Snack"
        
        # Format meals for Flutter with proper field names
        formatted_meals = []
        for meal in meals:
            formatted_meal = {
                "id": str(meal.get('id', '')),
                "food_item": str(meal.get('food_item', '')),  # This is what Flutter expects!
                "name": str(meal.get('food_item', '')),
                "quantity": str(meal.get('quantity', '')),
                "meal_type": capitalize_meal_type(meal.get('meal_type')),
                "calories": float(meal.get('calories', 0)),
                "protein": float(meal.get('protein_g', 0)),
                "carbs": float(meal.get('carbs_g', 0)),
                "fat": float(meal.get('fat_g', 0)),
                "protein_g": float(meal.get('protein_g', 0)),
                "carbs_g": float(meal.get('carbs_g', 0)),
                "fat_g": float(meal.get('fat_g', 0)),
                "fiber": float(meal.get('fiber_g', 0)),
                "sugar": float(meal.get('sugar_g', 0)),
                "sodium": float(meal.get('sodium_mg', 0)),
                "logged_at": str(meal.get('logged_at', meal.get('meal_date', ''))),
                "meal_date": str(meal.get('meal_date', '')),
                "nutrition_notes": str(meal.get('nutrition_data', {}).get('nutrition_notes', '')),
                "healthiness_score": int(meal.get('nutrition_data', {}).get('healthiness_score', 7)),
                "suggestions": str(meal.get('nutrition_data', {}).get('suggestions', ''))
            }
            formatted_meals.append(formatted_meal)
        
        return {
            "success": True,
            "meals": formatted_meals,
            "total_count": len(formatted_meals)
        }
        
    except Exception as e:
        print(f"❌ Error getting Flutter meal history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# Water logging
@router.post("/water", response_model=dict)
async def save_water_entry(water_data: WaterEntryCreate):
    """Save or update daily water intake"""
    try:
        print(f"💧 Saving water entry: {water_data.glasses_consumed} glasses for user {water_data.user_id}")
        
        supabase_service = get_supabase_service()
        
        # Parse date and convert to date only (not datetime)
        try:
            entry_date = datetime.fromisoformat(water_data.date.replace('Z', '+00:00')).date()
        except ValueError:
            entry_date = datetime.now().date()
        
        # Check if entry exists for this date
        existing_entry = await supabase_service.get_water_entry_by_date(
            water_data.user_id, 
            entry_date
        )
        
        water_entry_data = {
            'user_id': water_data.user_id,
            'date': str(entry_date),  # Convert date to string for Supabase
            'glasses_consumed': water_data.glasses_consumed,
            'total_ml': water_data.total_ml,
            'target_ml': water_data.target_ml,
            'notes': water_data.notes,
            'updated_at': datetime.now().isoformat()
        }
        
        if existing_entry:
            # Update existing entry
            updated_entry = await supabase_service.update_water_entry(
                existing_entry['id'], 
                water_entry_data
            )
            return {"success": True, "id": existing_entry['id'], "entry": updated_entry}
        else:
            # Create new entry
            water_entry_data['id'] = str(uuid.uuid4())
            water_entry_data['created_at'] = datetime.now().isoformat()
            created_entry = await supabase_service.create_water_entry(water_entry_data)
            return {"success": True, "id": created_entry['id'], "entry": created_entry}
            
    except Exception as e:
        print(f"❌ Error saving water entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/water/{user_id}/today")
async def get_today_water(user_id: str):
    """Get today's water intake"""
    try:
        print(f"💧 Getting today's water for user: {user_id}")
        
        supabase_service = get_supabase_service()
        today = datetime.now().date()  # Get today's date
        entry = await supabase_service.get_water_entry_by_date(user_id, today)
        
        return {"success": True, "entry": entry}
        
    except Exception as e:
        print(f"❌ Error getting today's water: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/water/{user_id}")
async def get_water_history(user_id: str, limit: int = 30):
    """Get water intake history for a user"""
    try:
        print(f"💧 Getting water history for user: {user_id}, limit: {limit}")
        
        supabase_service = get_supabase_service()
        entries = await supabase_service.get_water_history(user_id, limit)
        
        # Calculate summary statistics
        total_days = len(entries)
        goal_achieved_days = sum(1 for entry in entries if entry.get('total_ml', 0) >= entry.get('target_ml', 2000))
        avg_daily_intake = sum(entry.get('total_ml', 0) for entry in entries) / max(total_days, 1)
        
        return {
            "success": True, 
            "entries": entries,
            "summary": {
                "total_days": total_days,
                "goal_achieved_days": goal_achieved_days,
                "goal_achievement_rate": (goal_achieved_days / max(total_days, 1)) * 100,
                "average_daily_intake": round(avg_daily_intake, 1)
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting water history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/water/{user_id}/stats")
async def get_water_stats(user_id: str, days: int = 7):
    """Get water intake statistics for the last N days"""
    try:
        print(f"💧 Getting water stats for user: {user_id}, last {days} days")
        
        supabase_service = get_supabase_service()
        entries = await supabase_service.get_water_history(user_id, days)
        
        if not entries:
            return {
                "success": True,
                "stats": {
                    "average_daily": 0,
                    "best_day": 0,
                    "goal_achievement_rate": 0,
                    "total_glasses": 0,
                    "streak_days": 0
                }
            }
        
        # Calculate statistics
        daily_totals = [entry.get('total_ml', 0) for entry in entries]
        goal_achievements = [entry.get('total_ml', 0) >= entry.get('target_ml', 2000) for entry in entries]
        
        stats = {
            "average_daily": round(sum(daily_totals) / len(daily_totals), 1),
            "best_day": max(daily_totals),
            "goal_achievement_rate": round((sum(goal_achievements) / len(goal_achievements)) * 100, 1),
            "total_glasses": sum(entry.get('glasses_consumed', 0) for entry in entries),
            "streak_days": _calculate_water_streak(goal_achievements)
        }
        
        return {"success": True, "stats": stats}
        
    except Exception as e:
        print(f"❌ Error getting water stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_water_streak(achievements: List[bool]) -> int:
    """Calculate current streak of goal achievements"""
    streak = 0
    for achieved in achievements:
        if achieved:
            streak += 1
        else:
            break
    return streak

@router.post("/steps", response_model=dict)
async def save_step_entry(step_data: StepEntryCreate):
    """Save or update daily step entry"""
    try:
        print(f"🚶 Saving step entry: {step_data.steps} steps for user {step_data.userId}")
        
        supabase_service = get_supabase_service()
        
        # Parse date
        try:
            entry_date = datetime.fromisoformat(step_data.date.replace('Z', '+00:00')).date()
        except ValueError:
            entry_date = datetime.now().date()
        
        # Check if entry exists for this date
        existing_entry = await supabase_service.get_step_entry_by_date(
            step_data.userId, 
            entry_date
        )
        
        step_entry_data = {
            'user_id': step_data.userId,
            'date': str(entry_date),
            'steps': step_data.steps,
            'goal': step_data.goal,
            'calories_burned': step_data.caloriesBurned,
            'distance_km': step_data.distanceKm,
            'active_minutes': step_data.activeMinutes,
            'source_type': step_data.sourceType,
            'last_synced': step_data.lastSynced,
            'updated_at': datetime.now().isoformat()
        }
        
        if existing_entry:
            # Update existing entry
            updated_entry = await supabase_service.update_step_entry(
                existing_entry['id'], 
                step_entry_data
            )
            return {"success": True, "id": existing_entry['id'], "entry": updated_entry}
        else:
            # Create new entry
            step_entry_data['id'] = str(uuid.uuid4())
            step_entry_data['created_at'] = datetime.now().isoformat()
            created_entry = await supabase_service.create_step_entry(step_entry_data)
            return {"success": True, "id": created_entry['id'], "entry": created_entry}
            
    except Exception as e:
        print(f"❌ Error saving step entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/steps/{user_id}")
async def get_all_steps(user_id: str, limit: int = 100):
    """Get all step entries for a user"""
    try:
        print(f"🚶 Getting all steps for user: {user_id}, limit: {limit}")
        
        supabase_service = get_supabase_service()
        entries = await supabase_service.get_step_history(user_id, limit)
        
        print(f"🚶 Found {len(entries)} step entries in database")
        
        # Calculate summary statistics
        total_days = len(entries)
        if total_days > 0:
            total_steps = sum(entry.get('steps', 0) for entry in entries)
            goal_achieved_days = sum(1 for entry in entries if entry.get('steps', 0) >= entry.get('goal', 10000))
            avg_daily_steps = total_steps / total_days
            best_day_steps = max(entry.get('steps', 0) for entry in entries)
        else:
            total_steps = avg_daily_steps = best_day_steps = goal_achieved_days = 0
        
        # Log the first entry for debugging
        if entries:
            print(f"🚶 First entry sample: {entries[0]}")
        
        response_data = {
            "success": True,
            "entries": entries,  # Make sure this key exists
            "summary": {
                "total_days": total_days,
                "total_steps": total_steps,
                "goal_achieved_days": goal_achieved_days,
                "goal_achievement_rate": (goal_achieved_days / max(total_days, 1)) * 100,
                "average_daily_steps": round(avg_daily_steps),
                "best_day_steps": best_day_steps
            }
        }
        
        print(f"🚶 Returning response with {len(entries)} entries")
        return response_data
        
    except Exception as e:
        print(f"❌ Error getting all steps: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/steps/{user_id}/today")
async def get_today_steps(user_id: str):
    """Get today's step entry"""
    try:
        print(f"🚶 Getting today's steps for user: {user_id}")
        
        supabase_service = get_supabase_service()
        today = datetime.now().date()
        entry = await supabase_service.get_step_entry_by_date(user_id, today)
        
        return {"success": True, "entry": entry}
        
    except Exception as e:
        print(f"❌ Error getting today's steps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/steps/{user_id}/range")
async def get_steps_in_range(user_id: str, start_date: str, end_date: str):
    """Get step entries within a date range"""
    try:
        print(f"🚶 Getting steps in range for user: {user_id}, {start_date} to {end_date}")
        
        supabase_service = get_supabase_service()
        entries = await supabase_service.get_step_entries_in_range(user_id, start_date, end_date)
        
        return {"success": True, "entries": entries}
        
    except Exception as e:
        print(f"❌ Error getting steps in range: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/steps/{user_id}/{date}")
async def delete_step_entry(user_id: str, date: str):
    """Delete a step entry for a specific date"""
    try:
        print(f"🚶 Deleting step entry for user: {user_id}, date: {date}")
        
        supabase_service = get_supabase_service()
        
        # Parse date
        entry_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
        
        success = await supabase_service.delete_step_entry_by_date(user_id, entry_date)
        
        if success:
            return {"success": True, "message": "Step entry deleted successfully"}
        else:
            return {"success": False, "message": "Step entry not found"}
        
    except Exception as e:
        print(f"❌ Error deleting step entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/steps/{user_id}/stats")
async def get_step_stats(user_id: str, days: int = 7):
    """Get step statistics for the last N days"""
    try:
        print(f"🚶 Getting step stats for user: {user_id}, last {days} days")
        
        supabase_service = get_supabase_service()
        entries = await supabase_service.get_step_history(user_id, days)
        
        if not entries:
            return {
                "success": True,
                "stats": {
                    "average_daily_steps": 0,
                    "best_day_steps": 0,
                    "goal_achievement_rate": 0,
                    "total_steps": 0,
                    "streak_days": 0,
                    "total_distance": 0.0,
                    "total_calories": 0.0
                }
            }
        
        # Calculate statistics
        daily_steps = [entry.get('steps', 0) for entry in entries]
        goal_achievements = [entry.get('steps', 0) >= entry.get('goal', 10000) for entry in entries]
        
        stats = {
            "average_daily_steps": round(sum(daily_steps) / len(daily_steps)),
            "best_day_steps": max(daily_steps),
            "goal_achievement_rate": round((sum(goal_achievements) / len(goal_achievements)) * 100, 1),
            "total_steps": sum(daily_steps),
            "streak_days": _calculate_step_streak(goal_achievements),
            "total_distance": round(sum(entry.get('distance_km', 0) for entry in entries), 2),
            "total_calories": round(sum(entry.get('calories_burned', 0) for entry in entries), 1)
        }
        
        return {"success": True, "stats": stats}
        
    except Exception as e:
        print(f"❌ Error getting step stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_step_streak(achievements: List[bool]) -> int:
    """Calculate current streak of step goal achievements"""
    streak = 0
    for achieved in achievements:
        if achieved:
            streak += 1
        else:
            break
    return streak

@router.post("/weight", response_model=dict)
async def save_weight_entry(weight_data: WeightEntryCreate):
    """Save or update weight entry"""
    try:
        print(f"⚖️ Saving weight entry: {weight_data.weight} kg for user {weight_data.user_id}")
        
        supabase_service = get_supabase_service()
        
        # Parse date
        try:
            entry_date = datetime.fromisoformat(weight_data.date.replace('Z', '+00:00'))
        except ValueError:
            entry_date = datetime.now()
        
        weight_entry_data = {
            'user_id': weight_data.user_id,
            'date': entry_date.isoformat(),
            'weight': weight_data.weight,
            'notes': weight_data.notes,
            'body_fat_percentage': weight_data.body_fat_percentage,
            'muscle_mass_kg': weight_data.muscle_mass_kg,
            'updated_at': datetime.now().isoformat()
        }
        
        # Always create new entry for weight (allow multiple entries per day)
        weight_entry_data['id'] = str(uuid.uuid4())
        weight_entry_data['created_at'] = datetime.now().isoformat()
        created_entry = await supabase_service.create_weight_entry(weight_entry_data)
        
        return {"success": True, "id": created_entry['id'], "entry": created_entry}
            
    except Exception as e:
        print(f"❌ Error saving weight entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weight/{user_id}")
async def get_weight_history(user_id: str, limit: int = 50):
    """Get weight history for a user"""
    try:
        print(f"⚖️ Getting weight history for user: {user_id}, limit: {limit}")
        
        supabase_service = get_supabase_service()
        entries = await supabase_service.get_weight_history(user_id, limit)
        
        print(f"✅ Returning {len(entries)} weight entries")
        
        return {
            "success": True,
            "weights": entries,
            "summary": {
                "total_entries": len(entries)
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting weight history: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weight/{user_id}/latest")
async def get_latest_weight(user_id: str):
    """Get the latest weight entry for a user"""
    try:
        print(f"⚖️ Getting latest weight for user: {user_id}")
        
        supabase_service = get_supabase_service()
        entry = await supabase_service.get_latest_weight(user_id)
        
        return {"success": True, "weight": entry}
        
    except Exception as e:
        print(f"❌ Error getting latest weight: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/weight/{entry_id}")
async def delete_weight_entry(entry_id: str):
    """Delete a weight entry"""
    try:
        print(f"⚖️ Deleting weight entry: {entry_id}")
        
        supabase_service = get_supabase_service()
        success = await supabase_service.delete_weight_entry(entry_id)
        
        if success:
            return {"success": True, "message": "Weight entry deleted successfully"}
        else:
            return {"success": False, "message": "Weight entry not found"}
        
    except Exception as e:
        print(f"❌ Error deleting weight entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weight/{user_id}/stats")
async def get_weight_stats(user_id: str, days: int = 30):
    """Get weight statistics for the last N days"""
    try:
        print(f"⚖️ Getting weight stats for user: {user_id}, last {days} days")
        
        supabase_service = get_supabase_service()
        entries = await supabase_service.get_weight_history(user_id, days)
        
        if not entries:
            return {
                "success": True,
                "stats": {
                    "average_weight": 0,
                    "weight_trend": "stable",
                    "total_change": 0,
                    "weekly_change": 0,
                    "monthly_change": 0
                }
            }
        
        weights = [entry.get('weight', 0) for entry in entries]
        avg_weight = sum(weights) / len(weights)
        
        # Determine trend
        if len(weights) >= 2:
            total_change = weights[0] - weights[-1]
            if total_change > 0.5:
                trend = "gaining"
            elif total_change < -0.5:
                trend = "losing"
            else:
                trend = "stable"
        else:
            total_change = 0
            trend = "stable"
        
        stats = {
            "average_weight": round(avg_weight, 1),
            "weight_trend": trend,
            "total_change": round(total_change, 1),
            "entry_count": len(entries)
        }
        
        return {"success": True, "stats": stats}
        
    except Exception as e:
        print(f"❌ Error getting weight stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))