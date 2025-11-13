from fastapi import APIRouter
from datetime import datetime, timedelta
from services.supabase_service import get_supabase_service

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/check-data/{user_id}")
async def check_data(user_id: str):
    """Check what data exists in database"""
    try:
        supabase = get_supabase_service()
        
        # Get sample of ALL data for this user
        meals = supabase.client.table('meal_entries')\
            .select('meal_date, food_item')\
            .eq('user_id', user_id)\
            .limit(10)\
            .execute()
        
        exercises = supabase.client.table('exercise_logs')\
            .select('exercise_date, exercise_name')\
            .eq('user_id', user_id)\
            .limit(10)\
            .execute()
        
        sleep = supabase.client.table('sleep_entries')\
            .select('date, total_hours')\
            .eq('user_id', user_id)\
            .limit(10)\
            .execute()
        
        return {
            'meals': meals.data,
            'exercises': exercises.data,
            'sleep': sleep.data
        }
    except Exception as e:
        return {'error': str(e)}