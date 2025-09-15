from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from services.supabase_service import get_supabase_service

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/context/{user_id}")
async def get_user_chat_context(user_id: str):
    """Get comprehensive user context for chat with all actual data"""
    try:
        supabase_service = get_supabase_service()
        
        # Get today's date
        today = datetime.now().date()
        today_str = today.isoformat()
        
        # Get user profile
        user = await supabase_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get today's meals
        meals_response = await supabase_service.get_user_meals_by_date(user_id, today_str)
        meals = meals_response if meals_response else []

        # Debug print to see what's coming back
        print(f"📊 Meals fetched: {len(meals)} meals")
        for meal in meals:
            print(f"  - {meal.get('food_item')}: {meal.get('calories')} cal")
        
        # Calculate totals
        total_calories = sum(meal.get('calories', 0) for meal in meals)
        total_protein = sum(meal.get('protein_g', 0) for meal in meals)
        
        print(f"📊 Total calories calculated: {total_calories}")
        
        # Get today's water intake
        water_response = await supabase_service.get_water_entry_by_date(user_id, today_str)
        
        # Get today's steps
        steps_response = supabase_service.client.table('daily_steps')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('date', today_str)\
            .execute()
        steps_data = steps_response.data[0] if steps_response.data else None
        
        # Get today's exercises
        start_date = f"{today_str}T00:00:00"
        end_date = f"{today_str}T23:59:59"
        
        exercises_response = supabase_service.client.table('exercise_logs')\
        .select('*')\
        .eq('user_id', user_id)\
        .gte('exercise_date', start_date)\
        .lte('exercise_date', end_date)\
        .execute()
        exercises = exercises_response.data if exercises_response.data else []

        exercise_minutes = 0
        exercise_calories = 0.0
        
        for ex in exercises:
            # Use duration_minutes if available
            if ex.get('duration_minutes'):
                exercise_minutes += int(ex['duration_minutes'])
            # Otherwise estimate from sets and reps
            elif ex.get('sets') and ex.get('reps'):
                # Rough estimate: 3 seconds per rep + 60 seconds rest between sets
                estimated_mins = int((ex['sets'] * ex['reps'] * 3 + (ex['sets'] - 1) * 60) / 60)
                exercise_minutes += estimated_mins
                # Optionally update the record
                try:
                    supabase_service.client.table('exercise_logs')\
                        .update({'duration_minutes': estimated_mins})\
                        .eq('id', ex['id'])\
                        .execute()
                except:
                    pass
            
            # Sum calories
            if ex.get('calories_burned'):
                exercise_calories += float(ex['calories_burned'])
        
        # Get today's weight entry
        weight_response = supabase_service.client.table('weight_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('date', today_str)\
            .execute()
        weight_data = weight_response.data[0] if weight_response.data else None
        
        # Get last night's sleep (FIX: use total_hours instead of hours_slept)
        sleep_response = supabase_service.client.table('sleep_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('date', today_str)\
            .execute()
        sleep_data = sleep_response.data[0] if sleep_response.data else None
        
        # Calculate totals for today
        total_calories = sum(float(m.get('calories', 0)) for m in meals)
        total_protein = sum(float(m.get('protein_g', 0)) for m in meals)
        total_carbs = sum(float(m.get('carbs_g', 0)) for m in meals)
        total_fat = sum(float(m.get('fat_g', 0)) for m in meals)
        total_fiber = sum(float(m.get('fiber_g', 0)) for m in meals)
        
        exercise_minutes = sum(int(e.get('duration_minutes', 0)) for e in exercises if e.get('duration_minutes'))
        exercise_calories = sum(float(e.get('calories_burned', 0)) for e in exercises)
        
        # Get weekly summary (last 7 days) - FIX: week_ago is a date object
        week_ago = today - timedelta(days=7)
        week_ago_str = week_ago.isoformat()
        
        # Weekly meals
        weekly_meals_response = supabase_service.client.table('meal_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('meal_date', week_ago_str)\
            .lte('meal_date', today_str)\
            .execute()
        weekly_meals = weekly_meals_response.data if weekly_meals_response.data else []
        
        # Weekly exercises
        weekly_exercises_response = supabase_service.client.table('exercise_logs')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('exercise_date', f"{week_ago_str}T00:00:00")\
            .lte('exercise_date', f"{today_str}T23:59:59")\
            .execute()
        weekly_exercises = weekly_exercises_response.data if weekly_exercises_response.data else []
        
        # Weekly sleep
        weekly_sleep_response = supabase_service.client.table('sleep_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('date', week_ago_str)\
            .lte('date', today_str)\
            .execute()
        weekly_sleep = weekly_sleep_response.data if weekly_sleep_response.data else []
        
        # Calculate weekly averages
        days_with_data = len(set(m.get('meal_date', '')[:10] for m in weekly_meals)) or 1
        
        # FIX: Calculate average calories properly
        total_weekly_calories = sum(float(m.get('calories', 0)) for m in weekly_meals)
        avg_daily_calories = round(total_weekly_calories / days_with_data, 0) if days_with_data > 0 else 0
        
        # FIX: Use total_hours instead of hours_slept
        avg_sleep_hours = sum(s.get('total_hours', 0) for s in weekly_sleep) / len(weekly_sleep) if weekly_sleep else 0
        
        # Get weight trend
        weight_history_response = supabase_service.client.table('weight_entries')\
            .select('weight')\
            .eq('user_id', user_id)\
            .gte('date', week_ago_str)\
            .order('date', desc=False)\
            .execute()
        weight_history = weight_history_response.data if weight_history_response.data else []
        
        weight_trend = "stable"
        if len(weight_history) >= 2:
            first_weight = float(weight_history[0].get('weight', 0))
            last_weight = float(weight_history[-1].get('weight', 0))
            if last_weight < first_weight - 0.5:
                weight_trend = "losing"
            elif last_weight > first_weight + 0.5:
                weight_trend = "gaining"
        
        # Build complete context
        context = {
            'user_profile': {
                'id': user.get('id'),
                'name': user.get('name', ''),
                'age': user.get('age'),
                'weight': user.get('weight'),
                'height': user.get('height'),
                'primary_goal': user.get('primary_goal', ''),
                'weight_goal': user.get('weight_goal', ''),
                'target_weight': user.get('target_weight'),
                'tdee': user.get('tdee', 2000),
                'fitness_level': user.get('fitness_level', 'Beginner'),
                'dietary_preferences': user.get('dietary_preferences', []),
                'medical_conditions': user.get('medical_conditions', []),
            },
            'today_progress': {
                'date': today_str,
                'meals_logged': len(meals),
                'total_calories': int(total_calories),
                'total_protein': round(total_protein, 1),
                'total_carbs': round(total_carbs, 1),
                'total_fat': round(total_fat, 1),
                'total_fiber': round(total_fiber, 1),
                'water_glasses': water_response.get('glasses_consumed', 0) if water_response else 0,
                'water_ml': water_response.get('total_ml', 0) if water_response else 0,
                'steps': steps_data.get('steps', 0) if steps_data else 0,
                'exercise_minutes': int(exercise_minutes),
                'exercises_done': [
                    {
                        'name': e.get('exercise_name'),
                        'type': e.get('exercise_type'),
                        'calories': int(float(e.get('calories_burned', 0)))
                    } for e in exercises
                ],
                'exercise_calories': int(round(exercise_calories)),
                'sleep_hours': sleep_data.get('total_hours', 0) if sleep_data else 0,
                'sleep_quality': sleep_data.get('quality_score', 'Not logged') if sleep_data else 'Not logged',
                'weight_logged': weight_data.get('weight') if weight_data else None,
            },
            'weekly_summary': {
                'avg_daily_calories': avg_daily_calories,
                'total_workouts': len(weekly_exercises),
                'total_exercise_minutes': sum(int(e.get('duration_minutes', 0)) for e in weekly_exercises if e.get('duration_minutes')),
                'avg_sleep_hours': round(avg_sleep_hours, 1),
                'weight_trend': weight_trend,
                'meals_this_week': len(weekly_meals),
            },
            'goals_progress': {
                'daily_calorie_goal': user.get('tdee', 2000),
                'water_goal_glasses': user.get('water_intake_glasses', 8),
                'step_goal': user.get('daily_step_goal', 10000),
                'workout_frequency_goal': user.get('workout_frequency', 3),
                'weight_progress': {
                    'current': user.get('weight'),
                    'target': user.get('target_weight'),
                    'status': 'on_track' if weight_trend == 'losing' and user.get('weight_goal') == 'lose_weight' else 'needs_attention'
                }
            },
            'recent_activity': {
                'meals_this_week': len(weekly_meals),
                'workouts_this_week': len(set(e.get('exercise_date', '')[:10] for e in weekly_exercises)),
                'avg_sleep_hours': round(avg_sleep_hours, 1),
                'last_meal': meals[-1] if meals else None,
                'last_workout': exercises[-1] if exercises else weekly_exercises[-1] if weekly_exercises else None,
            }
        }
        
        return {
            'success': True,
            'context': context
        }
        
    except Exception as e:
        print(f"❌ Error getting chat context: {e}")
        import traceback
        traceback.print_exc()
        
        # Return empty context on error
        return {
            'success': False,
            'error': str(e),
            'context': {
                'user_profile': {},
                'today_progress': {
                    'date': datetime.now().date().isoformat(),
                    'meals_logged': 0,
                    'total_calories': 0,
                    'water_glasses': 0,
                    'steps': 0,
                    'exercise_minutes': 0,
                },
                'weekly_summary': {},
                'goals_progress': {},
                'recent_activity': {}
            }
        }