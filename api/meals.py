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
    """Update daily nutrition summary"""
    try:
        date_only = meal_date.split('T')[0]  # Get just the date part
        
        # Get existing daily nutrition or create new
        existing = await supabase_service.get_daily_nutrition(user_id, date_only)
        
        if existing:
            # Update existing
            updated_data = {
                'calories_consumed': existing['calories_consumed'] + nutrition_data['calories'],
                'protein_g': existing['protein_g'] + nutrition_data['protein_g'],
                'carbs_g': existing['carbs_g'] + nutrition_data['carbs_g'],
                'fat_g': existing['fat_g'] + nutrition_data['fat_g'],
                'meals_logged': existing['meals_logged'] + 1
            }
            await supabase_service.update_daily_nutrition(existing['id'], updated_data)
        else:
            # Create new
            new_data = {
                'user_id': user_id,
                'date': date_only,
                'calories_consumed': nutrition_data['calories'],
                'protein_g': nutrition_data['protein_g'],
                'carbs_g': nutrition_data['carbs_g'], 
                'fat_g': nutrition_data['fat_g'],
                'meals_logged': 1
            }
            await supabase_service.create_daily_nutrition(new_data)
            
    except Exception as e:
        print(f"❌ Error updating daily nutrition: {e}")