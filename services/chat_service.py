# services/chat_service.py
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from services.openai_service import get_openai_service
from services.supabase_service import get_supabase_service
from services.weekly_context_manager import get_weekly_context_manager

class HealthChatService:
    def __init__(self):
        try:
            self.openai_service = get_openai_service()
            print(f"✅ OpenAI service initialized: {self.openai_service is not None}")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI service: {e}")
            self.openai_service = None
            
        try:
            self.supabase_service = get_supabase_service()
            print(f"✅ Supabase service initialized: {self.supabase_service is not None}")
        except Exception as e:
            print(f"❌ Failed to initialize Supabase service: {e}")
            self.supabase_service = None

        try:
            self.weekly_manager = get_weekly_context_manager()
            print(f"✅ Weekly context manager initialized")
        except Exception as e:
            print(f"⚠️ Weekly context not available: {e}")
            self.weekly_manager = None
    
    async def get_today_activities(self, user_id: str, target_date: date) -> dict:
        """Fetch all activities for a specific date"""
        activities = {}
        
        try:
            # Get today's meals
            meals_response = self.supabase_service.client.table('meal_entries')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('meal_date', f"{target_date}T00:00:00")\
                .lte('meal_date', f"{target_date}T23:59:59")\
                .execute()
            activities['meals'] = meals_response.data if meals_response.data else []
        except Exception as e:
            print(f"⚠️ Error fetching meals: {e}")
            activities['meals'] = []
        
        try:
            # Get today's water intake
            water_response = self.supabase_service.client.table('daily_water')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('date', str(target_date))\
                .execute()
            activities['water'] = water_response.data[0] if water_response.data else {}
        except Exception as e:
            print(f"⚠️ Error fetching water: {e}")
            activities['water'] = {}
        
        try:
            # Get today's exercise
            exercise_response = self.supabase_service.client.table('exercise_logs')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('exercise_date', str(target_date))\
                .execute()
            activities['exercise'] = exercise_response.data if exercise_response.data else []
        except Exception as e:
            print(f"⚠️ Error fetching exercise: {e}")
            activities['exercise'] = []
        
        try:
            # Get today's sleep
            sleep_response = self.supabase_service.client.table('sleep_entries')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('date', str(target_date))\
                .execute()
            activities['sleep'] = sleep_response.data[0] if sleep_response.data else {}
        except Exception as e:
            print(f"⚠️ Error fetching sleep: {e}")
            activities['sleep'] = {}
        
        try:
            # Get today's supplements
            activities['supplements'] = await self.supabase_service.get_supplement_status_by_date(user_id, target_date)
        except Exception as e:
            print(f"⚠️ Error fetching supplements: {e}")
            activities['supplements'] = {}
        
        try:
            # Get today's weight
            weight_response = self.supabase_service.client.table('weight_entries')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('date', str(target_date))\
                .execute()
            activities['weight'] = weight_response.data[0] if weight_response.data else {}
        except Exception as e:
            print(f"⚠️ Error fetching weight: {e}")
            activities['weight'] = {}
        
        try:
            # Get today's steps
            steps_response = self.supabase_service.client.table('daily_steps')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('date', str(target_date))\
                .execute()
            activities['steps'] = steps_response.data[0] if steps_response.data else {}
        except Exception as e:
            print(f"⚠️ Error fetching steps: {e}")
            activities['steps'] = {}
        
        return activities
    
    async def _get_weekly_summary(self, user_id: str) -> Dict[str, Any]:
        """Get weekly summary statistics"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            
            total_calories = 0
            total_workouts = 0
            total_sleep_hours = 0
            sleep_count = 0
            weight_entries = []
            
            for i in range(7):
                date = start_date + timedelta(days=i)
                activities = await self.get_today_activities(user_id, date)
                
                # Sum up meals
                meals = activities.get('meals', [])
                for meal in meals:
                    total_calories += meal.get('total_calories', 0)
                
                # Count workouts
                if activities.get('exercise'):
                    total_workouts += len(activities['exercise'])
                
                # Sum sleep
                if activities.get('sleep') and activities['sleep'].get('total_hours'):
                    total_sleep_hours += activities['sleep']['total_hours']
                    sleep_count += 1
                
                # Collect weight entries
                if activities.get('weight') and activities['weight'].get('weight'):
                    weight_entries.append(activities['weight'])
            
            avg_daily_calories = round(total_calories / 7) if total_calories > 0 else 0
            avg_sleep_hours = round(total_sleep_hours / sleep_count, 1) if sleep_count > 0 else 0
            weight_trend = self._calculate_weight_trend(weight_entries)
            
            return {
                'avg_daily_calories': avg_daily_calories,
                'total_workouts': total_workouts,
                'avg_sleep_hours': avg_sleep_hours,
                'weight_trend': weight_trend,
            }
            
        except Exception as e:
            print(f"Error getting weekly summary: {e}")
            return {
                'avg_daily_calories': 0,
                'total_workouts': 0,
                'avg_sleep_hours': 0,
                'weight_trend': 'unknown',
            }

    async def _get_recent_activity_summary(self, user_id: str) -> Dict[str, Any]:
        """Get recent activity summary for the past week"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            
            meals_count = 0
            workouts_count = 0
            total_sleep_hours = 0
            sleep_count = 0
            
            for i in range(7):
                date = start_date + timedelta(days=i)
                activities = await self.get_today_activities(user_id, date)
                
                # Count meals
                meals_count += len(activities.get('meals', []))
                
                # Count workouts
                workouts_count += len(activities.get('exercise', []))
                
                # Sum sleep hours
                sleep = activities.get('sleep', {})
                if sleep.get('total_hours'):
                    total_sleep_hours += sleep['total_hours']
                    sleep_count += 1
            
            avg_sleep = round(total_sleep_hours / sleep_count, 1) if sleep_count > 0 else 0
            
            return {
                'meals_this_week': meals_count,
                'workouts_this_week': workouts_count,
                'avg_sleep_hours': avg_sleep,
            }
            
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return {
                'meals_this_week': 0,
                'workouts_this_week': 0,
                'avg_sleep_hours': 0,
            }
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user context for chat"""
        try:
            # Get user profile
            user = await self.supabase_service.get_user_by_id(user_id)
            if not user:
                return {}
            
            # Get today's activities using your existing method
            today = datetime.now().date()
            activities = await self.get_today_activities(user_id, today)
            
            # Get yesterday's activities for sleep
            yesterday = today - timedelta(days=1)
            yesterday_activities = await self.get_today_activities(user_id, yesterday)
            
            # Calculate meal totals
            meals = activities.get('meals', [])
            total_calories = sum(meal.get('total_calories', 0) for meal in meals)
            total_protein = sum(meal.get('protein', 0) for meal in meals)
            total_carbs = sum(meal.get('carbs', 0) for meal in meals)
            total_fat = sum(meal.get('fat', 0) for meal in meals)
            
            # Calculate exercise totals
            exercises = activities.get('exercise', [])
            total_exercise_minutes = sum(
                ex.get('duration_minutes', 0) if ex.get('duration_minutes') is not None else 0 
                for ex in exercises
            )
            exercise_names = [ex.get('exercise_name', '') for ex in exercises]
            
            # Get water, steps, weight data
            water = activities.get('water', {})
            steps = activities.get('steps', {})
            weight = activities.get('weight', {})
            sleep = yesterday_activities.get('sleep', {})  # Use yesterday's sleep
            
            # Get weekly summary
            weekly_summary = await self._get_weekly_summary(user_id)
            
            # Get recent activity
            recent_activity = await self._get_recent_activity_summary(user_id)
            
            context = {
                'user_profile': {
                    'id': user_id,
                    'name': user.get('name', ''),
                    'age': user.get('age'),
                    'weight': user.get('weight'),
                    'height': user.get('height'),
                    'primary_goal': user.get('primary_goal'),
                    'weight_goal': user.get('weight_goal'),
                    'target_weight': user.get('target_weight'),
                    'activity_level': user.get('activity_level'),
                    'tdee': user.get('tdee'),
                    'gender': user.get('gender'),
                    'preferred_workouts': user.get('preferred_workouts', []),
                    'dietary_preferences': user.get('dietary_preferences', []),
                },
                'today_progress': {
                    'date': str(today),
                    'meals_logged': len(meals),
                    'total_calories': total_calories,
                    'total_protein': total_protein,
                    'total_carbs': total_carbs,
                    'total_fat': total_fat,
                    'water_glasses': water.get('glasses_consumed', 0),
                    'water_ml': water.get('total_ml', 0),
                    'steps': steps.get('steps', 0),
                    'exercise_minutes': total_exercise_minutes,
                    'exercises_done': exercise_names,
                    'sleep_hours': sleep.get('total_hours', 0),
                    'sleep_quality': sleep.get('quality', 'Not logged'),
                    'weight_logged': weight.get('weight'),
                },
                'weekly_summary': weekly_summary,
                'goals_progress': {
                    'daily_calorie_goal': user.get('tdee', 2000),
                    'water_goal_glasses': user.get('water_intake_glasses', 8),
                    'step_goal': user.get('step_goal', 10000),
                    'weight_progress': {
                        'current': user.get('weight'),
                        'target': user.get('target_weight'),
                        'status': self._calculate_weight_status(user.get('weight'), user.get('target_weight'))
                    }
                },
                'recent_activity': recent_activity,
            }
            
            return context
            
        except Exception as e:
            print(f"❌ Error getting user context: {e}")
            import traceback
            traceback.print_exc()
            return self._get_empty_context()
        
    async def get_enhanced_context(self, user_id: str) -> Dict[str, Any]:
        """Get enhanced context using cache"""
        try:
            from services.chat_context_manager import get_context_manager
            
            context_manager = get_context_manager()
            result = await context_manager.get_or_create_context(user_id)
            
            return result['context']
            
        except Exception as e:
            print(f"Error getting enhanced context: {e}")
            # Fallback to regular context
            return await self.get_user_context(user_id)
    
    def _calculate_hydration_consistency(self, water_logs: List[Dict]) -> float:
        """Calculate water intake consistency"""
        if not water_logs:
            return 0
        
        days_with_water = len([w for w in water_logs if w.get('glasses', 0) > 0])
        return round((days_with_water / 7) * 100, 1)
    
    def _calculate_avg_calories(self, meals: List[Dict]) -> float:
        if not meals:
            return 0
        
        # Group by date to calculate daily averages
        daily_calories = {}
        for meal in meals:
            date_key = meal.get('date', '').split('T')[0]
            calories = meal.get('calories', 0)
            if date_key:
                daily_calories[date_key] = daily_calories.get(date_key, 0) + calories
        
        if not daily_calories:
            return 0
        
        total_calories = sum(daily_calories.values())
        return round(total_calories / len(daily_calories), 1)
    
    def _calculate_avg_sleep(self, sleep_entries: List[Dict]) -> float:
        if not sleep_entries:
            return 0
        total_hours = sum(entry.get('total_hours', entry.get('sleep_hours', 0)) for entry in sleep_entries)
        return round(total_hours / len(sleep_entries), 1)
    
    def _calculate_weight_status(self, current: float, target: float) -> str:
        """Calculate weight progress status"""
        if not current or not target:
            return 'no_data'
        
        diff = abs(current - target)
        if diff < 0.5:
            return 'at_goal'
        elif current > target:
            return f'lose_{diff:.1f}kg'
        else:
            return f'gain_{diff:.1f}kg'

    def _calculate_weight_trend(self, weight_entries: List[Dict]) -> str:
        """Calculate weight trend from entries"""
        if len(weight_entries) < 2:
            return 'insufficient_data'
        
        # Sort by date
        sorted_entries = sorted(weight_entries, key=lambda x: x.get('date', ''))
        
        if len(sorted_entries) >= 2:
            first_weight = sorted_entries[0].get('weight', 0)
            last_weight = sorted_entries[-1].get('weight', 0)
            change = last_weight - first_weight
            
            if abs(change) < 0.2:
                return 'stable'
            elif change > 0:
                return f'gaining_{abs(change):.1f}kg'
            else:
                return f'losing_{abs(change):.1f}kg'
        
        return 'insufficient_data'
        
    def _get_empty_context(self) -> Dict[str, Any]:
        """Return empty context structure when error occurs"""
        return {
            'user_profile': {},
            'today_progress': {
                'date': str(datetime.now().date()),
                'meals_logged': 0,
                'total_calories': 0,
                'total_protein': 0,
                'total_carbs': 0,
                'total_fat': 0,
                'water_glasses': 0,
                'water_ml': 0,
                'steps': 0,
                'exercise_minutes': 0,
                'exercises_done': [],
                'sleep_hours': 0,
                'sleep_quality': 'Not logged',
                'weight_logged': None,
            },
            'weekly_summary': {
                'avg_daily_calories': 0,
                'total_workouts': 0,
                'avg_sleep_hours': 0,
                'weight_trend': 'unknown',
            },
            'goals_progress': {
                'daily_calorie_goal': 2000,
                'water_goal_glasses': 8,
                'step_goal': 10000,
                'weight_progress': {
                    'current': None,
                    'target': None,
                    'status': 'no_data'
                }
            },
            'recent_activity': {
                'meals_this_week': 0,
                'workouts_this_week': 0,
                'avg_sleep_hours': 0,
            }
        }
    
    def _create_system_prompt(self, context: Dict[str, Any]) -> str:
        """Create enhanced system prompt with all activity data"""
        user_profile = context.get('user_profile', {})
        today_progress = context.get('today_progress', {})
        
        # Check which structure we have
        if 'totals' in today_progress:
            # Enhanced context structure
            meals_logged = today_progress.get('meals_logged', 0)
            total_calories = today_progress.get('totals', {}).get('calories', 0)
            total_protein = today_progress.get('totals', {}).get('protein', 0)
            total_carbs = today_progress.get('totals', {}).get('carbs', 0)
            total_fat = today_progress.get('totals', {}).get('fat', 0)
        else:
            # Regular context structure
            meals_logged = today_progress.get('meals_logged', 0)
            total_calories = today_progress.get('total_calories', 0)
            total_protein = today_progress.get('total_protein', 0)
            total_carbs = today_progress.get('total_carbs', 0)
            total_fat = today_progress.get('total_fat', 0)
        
        water_glasses = today_progress.get('water_glasses', 0)
        steps = today_progress.get('steps', 0)
        exercise_minutes = today_progress.get('exercise_minutes', 0)
        
        # Handle exercises_done - could be a number or list
        exercises_done = today_progress.get('exercises_done', 0)
        if isinstance(exercises_done, list):
            exercises_done = len(exercises_done)
        
        # Build the prompt with the ACTUAL data
        prompt = f"""You are a personalized AI health coach. 

    USER PROFILE:
    - Name: {user_profile.get('name', 'User')}
    - Age: {user_profile.get('age')}, Weight: {user_profile.get('weight')}kg
    - Goal: {user_profile.get('primary_goal')}
    - TDEE: {user_profile.get('tdee')} calories

    TODAY'S ACTUAL DATA ({today_progress.get('date')}):
    - Meals Logged: {meals_logged}
    - Total Calories: {total_calories}
    - Protein: {total_protein}g, Carbs: {total_carbs}g, Fat: {total_fat}g
    - Water: {water_glasses} glasses
    - Steps: {steps}
    - Exercise: {exercise_minutes} minutes ({exercises_done} exercises)

    IMPORTANT: Use these exact numbers when reporting progress. The user has logged {meals_logged} meal(s) with {total_calories} calories today."""
        
        return prompt
    
    async def generate_chat_response(self, user_id: str, message: str) -> str:
        """Generate chat response with message persistence"""
        try:
            print(f"💬 Generating chat response for user: {user_id}")
            
            # Save user message
            try:
                await self.supabase_service.save_chat_message(user_id, message, is_user=True)
            except Exception as e:
                print(f"⚠️ Error saving user message: {e}")
            
            # Try comprehensive context first, fallback to basic
            try:
                user_context = await self.get_comprehensive_context(user_id, include_weeks=4)
                print(f"📊 Using comprehensive context with weekly data: {user_context.get('has_weekly_data', False)}")
            except Exception as e:
                print(f"⚠️ Falling back to basic context: {e}")
                user_context = await self.get_enhanced_context(user_id)
            
            # Get recent messages
            recent_messages = []
            try:
                recent_messages = await self.supabase_service.get_recent_chat_context(user_id, limit=10)
                print(f"💬 Retrieved {len(recent_messages)} recent messages")
            except Exception as e:
                print(f"⚠️ Error getting recent chat context: {e}")
            
            # Create enhanced system prompt
            system_prompt = self._create_enhanced_system_prompt(user_context)
            print(f"📝 System prompt created: {len(system_prompt)} characters")
            
            # Build conversation for OpenAI
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent conversation context
            for msg in recent_messages:
                role = "user" if msg.get("is_user") else "assistant"
                messages.append({"role": role, "content": msg.get("message", "")})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            print(f"🤖 Calling OpenAI with {len(messages)} messages...")
            
            # Get AI response
            response = await self.openai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=600
            )
            
            reply = response.choices[0].message.content.strip()
            print(f"✅ OpenAI response received: {len(reply)} characters")
            
            # Save AI response
            try:
                await self.supabase_service.save_chat_message(user_id, reply, is_user=False)
            except Exception as e:
                print(f"⚠️ Error saving AI response: {e}")
            
            return reply
            
        except Exception as e:
            print(f"❌ Error generating chat response: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"I'm having trouble connecting to my AI service. Please try again."

    async def get_comprehensive_context(self, user_id: str, include_weeks: int = 4) -> Dict[str, Any]:
        """Get comprehensive context including daily and weekly data"""
        try:
            # Get basic context first
            basic_context = await self.get_enhanced_context(user_id)
            
            # Try to add weekly context if available
            if self.weekly_manager:
                try:
                    current_week = await self.weekly_manager.get_or_create_weekly_context(user_id)
                    previous_weeks = await self.weekly_manager.get_recent_weeks_context(user_id, weeks_count=include_weeks)
                    
                    # Add weekly data to context
                    basic_context['current_week'] = current_week.get('summary', {})
                    basic_context['recent_weeks'] = previous_weeks
                    basic_context['has_weekly_data'] = True
                    
                    print(f"✅ Added weekly context: {len(previous_weeks)} weeks")
                except Exception as e:
                    print(f"⚠️ Could not get weekly context: {e}")
                    basic_context['has_weekly_data'] = False
            else:
                basic_context['has_weekly_data'] = False
            
            return basic_context
            
        except Exception as e:
            print(f"Error getting comprehensive context: {e}")
            return await self.get_enhanced_context(user_id)

    def _create_enhanced_system_prompt(self, context: Dict[str, Any]) -> str:
        """Create system prompt with weekly context if available"""
        # Start with basic prompt
        base_prompt = self._create_system_prompt(context)
        
        # Add weekly context if available
        if context.get('has_weekly_data'):
            current_week = context.get('current_week', {})
            recent_weeks = context.get('recent_weeks', [])
            
            weekly_section = f"""

    WEEKLY PROGRESS (This Week):
    - Average Daily Calories: {current_week.get('avg_calories', 'N/A')}
    - Total Workouts: {current_week.get('total_workouts', 0)}
    - Average Sleep: {current_week.get('avg_sleep', 'N/A')}h
    - Weight Change: {current_week.get('weight_change', 'N/A')}kg

    RECENT TRENDS ({len(recent_weeks)} weeks of data available):
    You have access to the user's weekly patterns and can reference specific weeks when discussing progress.
    """
            return base_prompt + weekly_section
        
        return base_prompt

# Global instance
chat_service = None

def get_chat_service() -> HealthChatService:
    global chat_service
    if chat_service is None:
        chat_service = HealthChatService()
    return chat_service

def init_chat_service():
    global chat_service
    chat_service = HealthChatService()
    return chat_service