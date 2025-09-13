# api/meals.py
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
import uuid

from models.meal_schemas import (
    MealAnalysisRequest, 
    MealEntryResponse, 
    MealHistoryResponse
)
from services.supabase_service import get_supabase_service
from services.meal_analysis_service import get_meal_analysis_service
from services.meal_parser_service import get_meal_parser_service

router = APIRouter()

@router.post("/analyze", response_model=MealEntryResponse)
async def analyze_meal(request: MealAnalysisRequest):
    """Analyze meal using smart parser for multi-food support"""
    try:
        print(f"🍽️ Analyzing meal for user {request.user_id}: {request.food_item}")
        
        # Get services
        supabase_service = get_supabase_service()
        parser_service = get_meal_parser_service()  # NEW
        
        # Get user context
        user = await supabase_service.get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_context = {
            'weight': user.get('weight', 70),
            'primary_goal': user.get('primary_goal', 'maintain weight'),
            'activity_level': user.get('activity_level', 'moderate'),
            'tdee': user.get('tdee', 2000)
        }
        
        # Use parser for intelligent multi-food handling
        nutrition_data = await parser_service.parse_and_analyze_meal(
            meal_input=request.food_item,
            default_quantity=request.quantity,
            user_context=user_context,
            meal_type=request.meal_type
        )
        
        # Store components if it's a multi-food meal
        if nutrition_data.get('components'):
            print(f"✅ Analyzed {len(nutrition_data['components'])} food items")
        
        # Prepare meal entry data
        meal_entry = {
            'id': str(uuid.uuid4()),
            'user_id': request.user_id,
            'food_item': request.food_item,
            'quantity': request.quantity,
            'preparation': request.preparation,
            'meal_type': request.meal_type,
            'calories': nutrition_data['calories'],
            'protein_g': nutrition_data['protein_g'],
            'carbs_g': nutrition_data['carbs_g'],
            'fat_g': nutrition_data['fat_g'],
            'fiber_g': nutrition_data['fiber_g'],
            'sugar_g': nutrition_data['sugar_g'],
            'sodium_mg': nutrition_data['sodium_mg'],
            'nutrition_data': nutrition_data,
            'data_source': nutrition_data.get('data_source', 'ai'),
            'confidence_score': nutrition_data.get('confidence_score', 0.8),
            'meal_date': request.meal_date or datetime.now().isoformat(),
            'logged_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save to database
        saved_meal = await supabase_service.create_meal_entry(meal_entry)
        
        # Update daily nutrition
        await update_daily_nutrition(
            supabase_service, 
            request.user_id, 
            meal_entry['meal_date'],
            nutrition_data
        )
        
        # Return response
        return MealEntryResponse(
            id=saved_meal['id'],
            user_id=saved_meal['user_id'],
            food_item=saved_meal['food_item'],
            quantity=saved_meal['quantity'],
            meal_type=saved_meal['meal_type'],
            calories=saved_meal['calories'],
            protein_g=saved_meal['protein_g'],
            carbs_g=saved_meal['carbs_g'],
            fat_g=saved_meal['fat_g'],
            fiber_g=saved_meal['fiber_g'],
            sugar_g=saved_meal['sugar_g'],
            sodium_mg=saved_meal['sodium_mg'],
            nutrition_notes=nutrition_data.get('nutrition_notes'),
            healthiness_score=nutrition_data.get('healthiness_score'),
            suggestions=nutrition_data.get('suggestions'),
            meal_date=saved_meal['meal_date'],
            logged_at=saved_meal['logged_at'],
            data_source=saved_meal.get('data_source', 'ai')  # Include source in response
        )
        
    except Exception as e:
        print(f"❌ Error analyzing meal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/history", response_model=MealHistoryResponse)
async def get_meal_history(user_id: str, limit: int = 20, date_from: Optional[str] = None):
    """Get user's meal history"""
    try:
        supabase_service = get_supabase_service()
        
        # Get meals from database
        meals = await supabase_service.get_user_meals(user_id, limit=limit, date_from=date_from)
        
        meal_responses = [
            MealEntryResponse(
                id=meal['id'],
                user_id=meal['user_id'],
                food_item=meal['food_item'],
                quantity=meal['quantity'],
                meal_type=meal['meal_type'],
                calories=meal['calories'],
                protein_g=meal['protein_g'],
                carbs_g=meal['carbs_g'],
                fat_g=meal['fat_g'],
                fiber_g=meal['fiber_g'],
                sugar_g=meal['sugar_g'],
                sodium_mg=meal['sodium_mg'],
                nutrition_notes=meal.get('nutrition_data', {}).get('nutrition_notes'),
                healthiness_score=meal.get('nutrition_data', {}).get('healthiness_score'),
                suggestions=meal.get('nutrition_data', {}).get('suggestions'),
                meal_date=meal['meal_date'],
                logged_at=meal['logged_at']
            )
            for meal in meals
        ]
        
        return MealHistoryResponse(
            meals=meal_responses,
            total_count=len(meal_responses),
            date_range=date_from
        )
        
    except Exception as e:
        print(f"❌ Error getting meal history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def meals_health_check():
    """Health check for meals API"""
    return {
        "status": "Meals API is healthy",
        "features": ["ai_meal_analysis", "meal_history", "nutrition_tracking"],
        "timestamp": datetime.now()
    }

async def update_daily_nutrition(supabase_service, user_id: str, meal_date: str, nutrition_data: dict):
    """Update daily nutrition summary in daily_nutrition table"""
    try:
        # Extract just the date part (YYYY-MM-DD)
        date_only = meal_date.split('T')[0]
        
        # Get existing daily nutrition
        existing = await supabase_service.get_daily_nutrition(user_id, date_only)
        
        if existing:
            # Update existing entry
            updated_data = {
                'calories_consumed': int(float(existing.get('calories_consumed', 0)) + float(nutrition_data.get('calories', 0))),
                'protein_g': round(float(existing.get('protein_g', 0)) + float(nutrition_data.get('protein_g', 0)), 1),
                'carbs_g': round(float(existing.get('carbs_g', 0)) + float(nutrition_data.get('carbs_g', 0)), 1),
                'fat_g': round(float(existing.get('fat_g', 0)) + float(nutrition_data.get('fat_g', 0)), 1),
                'fiber_g': round(float(existing.get('fiber_g', 0)) + float(nutrition_data.get('fiber_g', 0)), 1),
                'sugar_g': round(float(existing.get('sugar_g', 0)) + float(nutrition_data.get('sugar_g', 0)), 1),
                'sodium_mg': int(float(existing.get('sodium_mg', 0)) + float(nutrition_data.get('sodium_mg', 0))),
                'meals_logged': int(existing.get('meals_logged', 0)) + 1,
                'updated_at': datetime.now().isoformat()
            }
            await supabase_service.update_daily_nutrition(existing['id'], updated_data)
            print(f"✅ Updated daily nutrition for {user_id} on {date_only}")
        else:
            # Create new entry
            new_data = {
                'user_id': user_id,
                'date': date_only,
                'calories_consumed': int(float(nutrition_data.get('calories', 0))),
                'protein_g': round(float(nutrition_data.get('protein_g', 0)), 1),
                'carbs_g': round(float(nutrition_data.get('carbs_g', 0)), 1),
                'fat_g': round(float(nutrition_data.get('fat_g', 0)), 1),
                'fiber_g': round(float(nutrition_data.get('fiber_g', 0)), 1),
                'sugar_g': round(float(nutrition_data.get('sugar_g', 0)), 1),
                'sodium_mg': int(float(nutrition_data.get('sodium_mg', 0))),
                'meals_logged': 1,
                'calorie_goal': 2000,  # Default or calculate based on user profile
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            await supabase_service.create_daily_nutrition(new_data)
            print(f"✅ Created daily nutrition for {user_id} on {date_only}")
            
    except Exception as e:
        print(f"❌ Error updating daily nutrition: {e}")
        # Don't fail the entire meal logging if daily nutrition update fails
        import traceback
        traceback.print_exc()

def calculate_calorie_goal(user_profile: dict) -> int:
    """Calculate daily calorie goal based on user's TDEE and weight goal"""
    
    tdee = user_profile.get('tdee', 2000)
    weight_goal = user_profile.get('weight_goal', 'maintain_weight').lower()
    
    # Normalize the goal (handle different formats)
    if 'lose' in weight_goal:
        weight_goal = 'lose_weight'
    elif 'gain' in weight_goal:
        weight_goal = 'gain_weight'
    else:
        weight_goal = 'maintain_weight'
    
    # Calculate based on goal
    if weight_goal == 'lose_weight':
        # Moderate deficit: 15-20% below TDEE
        calorie_goal = int(tdee * 0.82)  # 18% deficit
        
    elif weight_goal == 'gain_weight':
        # Moderate surplus: 10-15% above TDEE  
        calorie_goal = int(tdee * 1.12)  # 12% surplus
        
    else:  # maintain_weight
        # Maintenance: equal to TDEE
        calorie_goal = int(tdee)
    
    # Safety bounds (never go too extreme)
    min_calories = 1200 if user_profile.get('gender', '').lower() == 'female' else 1500
    max_calories = min(4000, int(tdee * 1.5))
    
    return max(min_calories, min(calorie_goal, max_calories))