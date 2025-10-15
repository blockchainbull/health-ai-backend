# api/meals.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timedelta
import uuid

from models.meal_schemas import (
    MealAnalysisRequest, 
    MealEntryResponse, 
    MealHistoryResponse
)
from services.supabase_service import get_supabase_service
from services.meal_analysis_service import get_meal_analysis_service
from services.chat_context_manager import get_context_manager
from utils.timezone_utils import get_timezone_offset, get_user_date, get_user_today, get_user_now

router = APIRouter()

@router.post("/analyze", response_model=MealEntryResponse)
async def analyze_meal(request: MealAnalysisRequest, tz_offset: int = Depends(get_timezone_offset)):
    """Analyze meal using smart parser with CACHING"""
    try:
        print(f"🍽️ Analyzing meal for user {request.user_id}: {request.food_item}")
        print(f"📅 Received meal_date (UTC): {request.meal_date}")
        
        # Parse the UTC datetime - NO CONVERSION, just parse it
        if request.meal_date:
            try:
                # Parse as UTC, keep as UTC
                meal_datetime_utc = datetime.fromisoformat(request.meal_date.replace('Z', '+00:00'))
                # Extract date for daily nutrition (convert to user's date for grouping)
                user_date = (meal_datetime_utc + timedelta(minutes=tz_offset)).date()
                
                print(f"✅ Storing UTC time: {meal_datetime_utc}")
                print(f"📅 User's date for grouping: {user_date}")
            except Exception as e:
                print(f"⚠️ Error parsing meal_date: {e}, using current UTC time")
                meal_datetime_utc = datetime.utcnow()
                user_date = (meal_datetime_utc + timedelta(minutes=tz_offset)).date()
        else:
            # No meal_date provided, use current UTC time
            meal_datetime_utc = datetime.utcnow()
            user_date = (meal_datetime_utc + timedelta(minutes=tz_offset)).date()
            print(f"📅 No meal_date provided, using current UTC: {meal_datetime_utc}")

        # Get services
        supabase_service = get_supabase_service()
        analysis_service = get_meal_analysis_service()
        context_manager = get_context_manager()
        
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
        
        nutrition_data = await analysis_service.analyze_meal_with_cache(
            food_item=request.food_item,
            quantity=request.quantity,
            user_context=user_context,
            user_id=request.user_id, 
            preparation=request.preparation
        )
        
        # Store components if it's a multi-food meal
        if nutrition_data.get('components'):
            print(f"✅ Analyzed {len(nutrition_data['components'])} food items")

        if not nutrition_data.get('data_source'):
            print(f"⚠️ WARNING: No data_source set for meal analysis!")
            nutrition_data['data_source'] = 'unknown'
        
        # Prepare meal entry data - store UTC time as-is
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
            'data_source': nutrition_data.get('data_source'),
            'search_hash': nutrition_data.get('search_hash'),
            'is_cached_source': nutrition_data.get('data_source') == 'cached',
            'confidence_score': nutrition_data.get('confidence_score', 0.8),
            'meal_date': user_date.isoformat(),  # User's date for grouping
            'logged_at': meal_datetime_utc.isoformat() + 'Z',  # Store UTC with Z marker
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        print(f"💾 Saving meal with logged_at (UTC): {meal_entry['logged_at']}")
        print(f"💾 Meal date for grouping: {meal_entry['meal_date']}")
        
        # Save to database
        saved_meal = await supabase_service.create_meal_entry(meal_entry)
        
        print(f"✅ Meal saved in UTC!")
        
        # Update chat context with the new meal
        await context_manager.update_context_activity(
            request.user_id,
            'meal',
            saved_meal,
            user_date
        )
        
        # Update daily nutrition
        await update_daily_nutrition(
            supabase_service, 
            request.user_id, 
            user_date.isoformat(),
            nutrition_data,
            tz_offset
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
            data_source=saved_meal.get('data_source', 'ai')
        )
        
    except Exception as e:
        print(f"❌ Error analyzing meal: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/log", response_model=dict)
async def log_meal(meal_entry: dict):
    """Log a meal entry directly (for manual entries)"""
    try:
        supabase_service = get_supabase_service()
        context_manager = get_context_manager()
        
        # Add IDs and timestamps
        meal_entry['id'] = str(uuid.uuid4())
        meal_entry['logged_at'] = datetime.now().isoformat()
        meal_entry['updated_at'] = datetime.now().isoformat()
        
        # Save to database
        created_entry = await supabase_service.create_meal_entry(meal_entry)
        
        # Update chat context
        meal_date = datetime.fromisoformat(meal_entry.get('meal_date', datetime.now().isoformat())).date()
        await context_manager.update_context_activity(
            meal_entry['user_id'],
            'meal',
            created_entry,
            meal_date
        )
        
        # Update daily nutrition
        await update_daily_nutrition(
            supabase_service,
            meal_entry['user_id'],
            meal_date.isoformat(),
            created_entry
        )
        
        return {"success": True, "meal": created_entry}
        
    except Exception as e:
        print(f"❌ Error logging meal: {e}")
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
    
@router.delete("/{meal_id}")
async def delete_meal(meal_id: str):
    """Delete a meal entry and update context"""
    try:
        print(f"🍽️ Deleting meal: {meal_id}")
        
        supabase_service = get_supabase_service()
        context_manager = get_context_manager()
        
        # Get meal details before deletion
        meal = await supabase_service.get_meal_by_id(meal_id)
        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found")
        
        # Delete from database
        success = await supabase_service.delete_meal(meal_id)
        
        if success:
            # Update context - remove this specific meal
            meal_date = datetime.fromisoformat(meal['meal_date']).date()
            await context_manager.remove_from_context(
                meal['user_id'],
                'meal',
                meal_id,
                meal_date
            )
            
            # Also update daily nutrition totals
            await recalculate_daily_nutrition(
                supabase_service,
                meal['user_id'],
                meal_date.isoformat()
            )
            
            return {"success": True, "message": "Meal deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete meal")
            
    except Exception as e:
        print(f"❌ Error deleting meal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function to recalculate daily nutrition after deletion
async def recalculate_daily_nutrition(supabase_service, user_id: str, date: str):
    """Recalculate daily nutrition totals after a meal deletion"""
    try:
        # Get all meals for the day
        meals = await supabase_service.get_user_meals_by_date(user_id, date)
        
        # Calculate new totals
        totals = {
            'total_calories': sum(m.get('calories', 0) for m in meals),
            'total_protein': sum(m.get('protein_g', 0) for m in meals),
            'total_carbs': sum(m.get('carbs_g', 0) for m in meals),
            'total_fat': sum(m.get('fat_g', 0) for m in meals),
            'total_fiber': sum(m.get('fiber_g', 0) for m in meals),
            'total_sugar': sum(m.get('sugar_g', 0) for m in meals),
            'total_sodium': sum(m.get('sodium_mg', 0) for m in meals),
        }
        
        # Update daily nutrition table
        await supabase_service.update_daily_nutrition(user_id, date, totals)
        
    except Exception as e:
        print(f"Error recalculating daily nutrition: {e}")

@router.get("/")
async def meals_health_check():
    """Health check for meals API"""
    return {
        "status": "Meals API is healthy",
        "features": ["ai_meal_analysis", "meal_history", "nutrition_tracking"],
        "timestamp": datetime.now()
    }

async def update_daily_nutrition(supabase_service, user_id: str, meal_date: str, nutrition_data: dict, timezone_offset: int = 0):
    """Update daily nutrition summary in daily_nutrition table"""
    try:
        from utils.timezone_utils import get_user_date, get_user_now
        
        # Extract date in user's timezone
        if 'T' in meal_date:
            # It's a datetime string - convert to user's local date
            date_only = str(get_user_date(meal_date, timezone_offset))
        else:
            # Already a date string
            date_only = meal_date
        
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
                'updated_at': get_user_now(timezone_offset).isoformat()
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
                'created_at': get_user_now(timezone_offset).isoformat(),
                'updated_at': get_user_now(timezone_offset).isoformat()
            }
            await supabase_service.create_daily_nutrition(new_data)
            print(f"✅ Created daily nutrition for {user_id} on {date_only}")
            
    except Exception as e:
        print(f"❌ Error updating daily nutrition: {e}")
        import traceback
        traceback.print_exc()

@router.post("/presets/create")
async def create_meal_preset(preset_data: dict):
    """Create a meal preset from logged meals"""
    try:
        supabase_service = get_supabase_service()
        
        preset = {
            'id': str(uuid.uuid4()),
            'user_id': preset_data['user_id'],
            'preset_name': preset_data['preset_name'],
            'description': preset_data.get('description'),
            'food_items': preset_data['food_items'],  # Array of items
            'meal_type': preset_data.get('meal_type'),
            'total_calories': preset_data['total_calories'],
            'total_protein_g': preset_data['total_protein_g'],
            'total_carbs_g': preset_data['total_carbs_g'],
            'total_fat_g': preset_data['total_fat_g'],
            'total_fiber_g': preset_data.get('total_fiber_g', 0),
            'total_sugar_g': preset_data.get('total_sugar_g', 0),
            'total_sodium_mg': preset_data.get('total_sodium_mg', 0),
            'is_favorite': preset_data.get('is_favorite', False),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        created = await supabase_service.create_meal_preset(preset)
        return {"success": True, "preset": created}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presets/{user_id}")
async def get_meal_presets(user_id: str):
    """Get all meal presets for a user"""
    try:
        supabase_service = get_supabase_service()
        presets = await supabase_service.get_user_meal_presets(user_id)
        return {"success": True, "presets": presets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/presets/{preset_id}/use")
async def use_meal_preset(preset_id: str, data: dict, tz_offset: int = Depends(get_timezone_offset)):
    """Log meals from a preset"""
    try:
        supabase_service = get_supabase_service()
        context_manager = get_context_manager()
        
        print(f"🍽️ Using preset: {preset_id}")
        print(f"📅 Received meal_date (UTC): {data.get('meal_date')}")
        print(f"🌍 Timezone offset: {tz_offset} minutes")
        
        # Get the preset
        response = supabase_service.client.table('meal_presets')\
            .select('*')\
            .eq('id', preset_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Preset not found")
        
        preset = response.data[0]
        
        # Parse the UTC datetime - keep as UTC
        if data.get('meal_date'):
            try:
                # Parse as UTC, keep as UTC
                meal_datetime_utc = datetime.fromisoformat(data['meal_date'].replace('Z', '+00:00'))
                # Extract date for daily nutrition (convert to user's date for grouping)
                user_date = (meal_datetime_utc + timedelta(minutes=tz_offset)).date()
                
                print(f"✅ Storing UTC time: {meal_datetime_utc}")
                print(f"📅 User's date for grouping: {user_date}")
            except Exception as e:
                print(f"⚠️ Error parsing meal_date: {e}, using current UTC time")
                meal_datetime_utc = datetime.utcnow()
                user_date = (meal_datetime_utc + timedelta(minutes=tz_offset)).date()
        else:
            # No meal_date provided, use current UTC time
            meal_datetime_utc = datetime.utcnow()
            user_date = (meal_datetime_utc + timedelta(minutes=tz_offset)).date()
        
        # Create meal entry from preset
        meal_entry = {
            'id': str(uuid.uuid4()),
            'user_id': preset['user_id'],
            'food_item': preset['preset_name'],
            'quantity': '1 serving',
            'meal_type': data.get('meal_type', preset.get('meal_type', 'snack')),
            'calories': preset['total_calories'],
            'protein_g': preset['total_protein_g'],
            'carbs_g': preset['total_carbs_g'],
            'fat_g': preset['total_fat_g'],
            'fiber_g': preset.get('total_fiber_g', 0),
            'sugar_g': preset.get('total_sugar_g', 0),
            'sodium_mg': preset.get('total_sodium_mg', 0),
            'nutrition_data': {
                'from_preset': True,
                'preset_id': preset_id,
                'food_items': preset['food_items']
            },
            'data_source': 'preset',
            'meal_date': user_date.isoformat(),  # User's date for grouping
            'logged_at': meal_datetime_utc.isoformat() + 'Z',  # Store UTC with Z marker
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        print(f"💾 Saving preset meal with logged_at (UTC): {meal_entry['logged_at']}")
        
        # Save meal
        saved = await supabase_service.create_meal_entry(meal_entry)
        
        print(f"✅ Preset meal saved in UTC!")
        
        # Update preset usage
        await supabase_service.update_preset_usage(preset_id)

        await context_manager.update_context_activity(
            user_id=preset['user_id'],
            activity_type='meal',
            data={
                'id': saved['id'],
                'food_item': preset['preset_name'],
                'meal_type': data.get('meal_type', preset.get('meal_type', 'snack')),
                'calories': saved['calories'],
                'protein_g': saved['protein_g'],
                'carbs_g': saved['carbs_g'],
                'fat_g': saved['fat_g'],
                'fiber_g': saved.get('fiber_g', 0),
                'sugar_g': saved.get('sugar_g', 0),
                'sodium_mg': saved.get('sodium_mg', 0),
                'created_at': saved['logged_at'],
                'data_source': 'preset',
                'preset_id': preset_id
            },
            date=user_date
        )

        return {"success": True, "meal": saved}
        
    except Exception as e:
        print(f"❌ Error using preset: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions/{user_id}")
async def get_meal_suggestions(user_id: str):
    """Get meal suggestions from history and presets"""
    try:
        supabase_service = get_supabase_service()
        
        # Get recent unique meals (15 instead of default 10)
        recent_meals = await supabase_service.get_recent_unique_meals(user_id, limit=15)
        
        # Get top presets
        presets = await supabase_service.get_user_meal_presets(user_id)
        top_presets = presets[:5] if presets else []
        
        return {
            "success": True,
            "recent_meals": recent_meals,
            "presets": top_presets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/presets/{preset_id}")
async def delete_meal_preset(preset_id: str):
    """Delete a meal preset"""
    try:
        supabase_service = get_supabase_service()
        
        # Get the preset first to verify it exists
        response = supabase_service.client.table('meal_presets')\
            .select('*')\
            .eq('id', preset_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Preset not found")
        
        # Delete the preset
        delete_response = supabase_service.client.table('meal_presets')\
            .delete()\
            .eq('id', preset_id)\
            .execute()
        
        return {"success": True, "message": "Preset deleted successfully"}
        
    except Exception as e:
        print(f"❌ Error deleting preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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