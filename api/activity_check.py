# api/activity_check.py
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, date
from services.supabase_service import get_supabase_service
from utils.timezone_utils import get_timezone_offset, get_user_today

router = APIRouter()

@router.get("/check-activity/{user_id}/{activity_type}")
async def check_activity_logged(
    user_id: str, 
    activity_type: str, 
    date_str: str = None,
    tz_offset: int = Depends(get_timezone_offset)
):
    """
    Check if a specific activity has been logged for today
    
    activity_type can be: meal, exercise, water, sleep, supplement, weight
    """
    try:
        print(f"🔍 Checking if {activity_type} logged for user {user_id}")
        
        supabase_service = get_supabase_service()
        
        # Get the check date
        if date_str:
            check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            check_date = get_user_today(tz_offset)
        
        is_logged = False
        details = {}
        
        # Check based on activity type
        if activity_type == 'meal':
            # Check if any meal logged today
            meals = await supabase_service.get_meals_by_date(user_id, check_date)
            is_logged = len(meals) > 0
            details = {
                'meals_count': len(meals),
                'meal_types': [m.get('meal_type') for m in meals]
            }
            
        elif activity_type == 'exercise':
            # Check if exercise logged today
            exercises = await supabase_service.get_exercise_logs(
                user_id,
                start_date=str(check_date),
                end_date=str(check_date)
            )
            is_logged = len(exercises) > 0
            details = {
                'workouts_count': len(exercises),
                'exercises': [e.get('exercise_name') for e in exercises]
            }
            
        elif activity_type == 'water':
            # Check if water logged today
            water_entry = await supabase_service.get_water_entry_by_date(user_id, check_date)
            is_logged = water_entry is not None and water_entry.get('total_glasses', 0) > 0
            details = {
                'glasses': water_entry.get('total_glasses', 0) if water_entry else 0,
                'liters': water_entry.get('total_liters', 0) if water_entry else 0
            }
            
        elif activity_type == 'sleep':
            # Check if sleep logged today
            sleep_entry = await supabase_service.get_sleep_entry_by_date(user_id, check_date)
            is_logged = sleep_entry is not None and sleep_entry.get('total_hours', 0) > 0
            details = {
                'hours': sleep_entry.get('total_hours', 0) if sleep_entry else 0,
                'quality': sleep_entry.get('quality_score', 0) if sleep_entry else 0
            }
            
        elif activity_type == 'supplement':
            # Check if any supplement logged today
            supplement_status = await supabase_service.get_supplement_status_by_date(user_id, check_date)
            is_logged = any(supplement_status.values())
            details = {
                'supplements_taken': sum(1 for taken in supplement_status.values() if taken),
                'supplements': supplement_status
            }
            
        elif activity_type == 'weight':
            # Check if weight logged in last 7 days (for weekly reminder)
            # Get date 7 days ago
            week_ago = check_date - timedelta(days=7)
            
            # Check for any weight entry in the last 7 days
            weight_entries = await supabase_service.get_weight_history(user_id, limit=100)
            
            # Filter entries from last 7 days
            recent_entries = [
                e for e in weight_entries 
                if e.get('date') and datetime.fromisoformat(e['date'].replace('Z', '+00:00')).date() >= week_ago
            ]
            
            is_logged = len(recent_entries) > 0
            details = {
                'entries_count': len(recent_entries),
                'last_entry_date': recent_entries[0].get('date') if recent_entries else None,
                'last_weight': recent_entries[0].get('weight') if recent_entries else None
            }
        else:
            raise HTTPException(status_code=400, detail=f"Invalid activity type: {activity_type}")
        
        return {
            'success': True,
            'logged': is_logged,
            'activity_type': activity_type,
            'date': str(check_date),
            'details': details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error checking activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-summary/{user_id}")
async def get_daily_activity_summary(
    user_id: str,
    date_str: str = None,
    tz_offset: int = Depends(get_timezone_offset)
):
    """
    Get a summary of all activities logged for today
    """
    try:
        print(f"📊 Getting daily summary for user {user_id}")
        
        supabase_service = get_supabase_service()
        
        # Get the check date
        if date_str:
            check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            check_date = get_user_today(tz_offset)
        
        # Check all activities
        meals = await supabase_service.get_meals_by_date(user_id, check_date)
        exercises = await supabase_service.get_exercise_logs(
            user_id,
            start_date=str(check_date),
            end_date=str(check_date)
        )
        water_entry = await supabase_service.get_water_entry_by_date(user_id, check_date)
        sleep_entry = await supabase_service.get_sleep_entry_by_date(user_id, check_date)
        supplement_status = await supabase_service.get_supplement_status_by_date(user_id, check_date)
        
        # Get weight entries from last 7 days
        week_ago = check_date - timedelta(days=7)
        weight_entries = await supabase_service.get_weight_history(user_id, limit=100)
        recent_weight_entries = [
            e for e in weight_entries 
            if e.get('date') and datetime.fromisoformat(e['date'].replace('Z', '+00:00')).date() >= week_ago
        ]
        
        # Build summary
        summary = {
            'date': str(check_date),
            'meals': {
                'logged': len(meals) > 0,
                'count': len(meals),
                'types': [m.get('meal_type') for m in meals]
            },
            'exercise': {
                'logged': len(exercises) > 0,
                'count': len(exercises),
                'total_minutes': sum(e.get('duration_minutes', 0) for e in exercises)
            },
            'water': {
                'logged': water_entry is not None and water_entry.get('total_glasses', 0) > 0,
                'glasses': water_entry.get('total_glasses', 0) if water_entry else 0,
                'liters': water_entry.get('total_liters', 0) if water_entry else 0
            },
            'sleep': {
                'logged': sleep_entry is not None and sleep_entry.get('total_hours', 0) > 0,
                'hours': sleep_entry.get('total_hours', 0) if sleep_entry else 0,
                'quality': sleep_entry.get('quality_score', 0) if sleep_entry else 0
            },
            'supplements': {
                'logged': any(supplement_status.values()),
                'taken_count': sum(1 for taken in supplement_status.values() if taken),
                'total_supplements': len(supplement_status),
                'details': supplement_status
            },
            'weight': {
                'logged_this_week': len(recent_weight_entries) > 0,
                'entries_count': len(recent_weight_entries),
                'last_entry_date': recent_weight_entries[0].get('date') if recent_weight_entries else None,
                'last_weight': recent_weight_entries[0].get('weight') if recent_weight_entries else None
            }
        }
        
        return {
            'success': True,
            'summary': summary
        }
        
    except Exception as e:
        print(f"❌ Error getting daily summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))