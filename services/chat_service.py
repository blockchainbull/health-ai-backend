# services/chat_service.py
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from services.openai_service import get_openai_service
from services.supabase_service import get_supabase_service

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
    
    async def get_today_activities(self, user_id: str, target_date: date) -> dict:
        """Fetch all activities for a specific date"""
        activities = {}
        
        try:
            # Get today's meals
            meals_response = await self.supabase_service.client.table('meal_entries')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('date', str(target_date))\
                .execute()
            activities['meals'] = meals_response.data if meals_response.data else []
        except Exception as e:
            print(f"⚠️ Error fetching meals: {e}")
            activities['meals'] = []
        
        try:
            # Get today's water intake
            water_response = await self.supabase_service.client.table('daily_water')\
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
            exercise_response = await self.supabase_service.client.table('exercise_logs')\
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
            sleep_response = await self.supabase_service.client.table('sleep_entries')\
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
            weight_response = await self.supabase_service.client.table('weight_entries')\
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
            steps_response = await self.supabase_service.client.table('daily_steps')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('date', str(target_date))\
                .execute()
            activities['steps'] = steps_response.data[0] if steps_response.data else {}
        except Exception as e:
            print(f"⚠️ Error fetching steps: {e}")
            activities['steps'] = {}
        
        return activities
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user context for chat"""
        try:
            print(f"🔍 Getting user context for: {user_id}")
            
            # Get user profile
            user = await self.supabase_service.get_user_by_id(user_id)
            if not user:
                print(f"❌ No user found for ID: {user_id}")
                return {}
            
            # Get today's date
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            # Get today's activities
            today_activities = await self.get_today_activities(user_id, today)
            
            # Get recent activity data (initialize all as empty lists)
            recent_meals = []
            recent_exercises = []
            recent_sleep = []
            recent_weight = []
            recent_water = []
            
            # Try to get weekly exercise data
            try:
                recent_exercises = await self.supabase_service.get_exercise_logs(
                    user_id, start_date=str(week_ago), end_date=str(today)
                )
            except Exception as e:
                print(f"⚠️ Error getting exercises: {e}")
                recent_exercises = []
            
            # Try to get sleep history
            try:
                recent_sleep = await self.supabase_service.get_sleep_history(user_id, limit=7)
            except Exception as e:
                print(f"⚠️ Error getting sleep: {e}")
                recent_sleep = []
            
            # Try to get weight history
            try:
                recent_weight = await self.supabase_service.get_weight_history(user_id, limit=5)
            except Exception as e:
                print(f"⚠️ Error getting weight: {e}")
                recent_weight = []
            
            # Try to get water history with corrected table name
            try:
                water_response = await self.supabase_service.client.table('daily_water')\
                    .select('*')\
                    .eq('user_id', user_id)\
                    .gte('date', str(week_ago))\
                    .lte('date', str(today))\
                    .execute()
                recent_water = water_response.data if water_response.data else []
            except Exception as e:
                print(f"⚠️ Error getting water: {e}")
                recent_water = []
            
            # Try to get meal history with corrected table name
            try:
                meals_response = await self.supabase_service.client.table('meal_entries')\
                    .select('*')\
                    .eq('user_id', user_id)\
                    .gte('date', str(week_ago))\
                    .lte('date', str(today))\
                    .execute()
                recent_meals = meals_response.data if meals_response.data else []
            except Exception as e:
                print(f"⚠️ Error getting meals: {e}")
                recent_meals = []
            
            # Safe calculation of exercise minutes (handle None values)
            def safe_get_duration(exercise):
                duration = exercise.get('duration_minutes')
                if duration is None:
                    # Try alternative field names
                    duration = exercise.get('duration', 0)
                return duration if duration is not None else 0
            
            # Calculate progress metrics with safe None handling
            context = {
                "user_profile": {
                    "name": user.get('name', 'User'),
                    "age": user.get('age'),
                    "gender": user.get('gender'),
                    "height": user.get('height'),
                    "weight": user.get('weight'),
                    "activity_level": user.get('activity_level'),
                    "primary_goal": user.get('primary_goal'),
                    "weight_goal": user.get('weight_goal'),
                    "target_weight": user.get('target_weight'),
                    "bmi": user.get('bmi'),
                    "bmr": user.get('bmr'),
                    "tdee": user.get('tdee'),
                    "dietary_preferences": user.get('dietary_preferences', []),
                    "medical_conditions": user.get('medical_conditions', []),
                    "preferred_workouts": user.get('preferred_workouts', []),
                    "fitness_level": user.get('fitness_level'),
                    "sleep_hours": user.get('sleep_hours'),
                    "bedtime": user.get('bedtime'),
                    "wakeup_time": user.get('wakeup_time'),
                    "water_intake_glasses": user.get('water_intake_glasses', 8),
                    "step_goal": user.get('step_goal', 10000),
                },
                "today_progress": {
                    "date": str(today),
                    "meals": today_activities.get('meals', []),
                    "total_calories": sum(m.get('calories', 0) for m in today_activities.get('meals', [])),
                    "total_protein": sum(m.get('protein_g', 0) or 0 for m in today_activities.get('meals', [])),
                    "total_carbs": sum(m.get('carbs_g', 0) or 0 for m in today_activities.get('meals', [])),
                    "total_fat": sum(m.get('fat_g', 0) or 0 for m in today_activities.get('meals', [])),
                    "water_glasses": today_activities.get('water', {}).get('glasses', 0),
                    "exercise_minutes": sum(safe_get_duration(e) for e in today_activities.get('exercise', [])),
                    "exercises_done": [e.get('exercise_type', 'Unknown') for e in today_activities.get('exercise', [])],
                    "steps": today_activities.get('steps', {}).get('count', 0) or today_activities.get('steps', {}).get('steps', 0),
                    "sleep_hours": today_activities.get('sleep', {}).get('total_hours', 0) or today_activities.get('sleep', {}).get('hours', 0),
                    "sleep_quality": today_activities.get('sleep', {}).get('quality', 'Not logged'),
                    "supplements_taken": today_activities.get('supplements', {}),
                    "weight_logged": today_activities.get('weight', {}).get('weight', None),
                },
                "weekly_summary": {
                    "avg_daily_calories": self._calculate_avg_calories(recent_meals),
                    "total_workouts": len(recent_exercises),
                    "avg_sleep_hours": self._calculate_avg_sleep(recent_sleep),
                    "weight_trend": self._calculate_weight_trend(recent_weight),
                    "hydration_consistency": self._calculate_hydration_consistency(recent_water),
                },
                "goals_progress": {
                    "daily_calorie_goal": user.get('tdee', 2000) or 2000,
                    "water_goal_glasses": user.get('water_intake_glasses', 8) or 8,
                    "step_goal": user.get('step_goal', 10000) or 10000,
                    "sleep_goal_hours": user.get('sleep_hours', 8) or 8,
                },
                "recent_activity": {
                    "meals_this_week": len(recent_meals),
                    "avg_daily_calories": self._calculate_avg_calories(recent_meals),
                    "workouts_this_week": len(recent_exercises),
                    "total_exercise_minutes": sum(safe_get_duration(e) for e in recent_exercises),
                }
            }
            
            print(f"✅ User context prepared with {len(recent_meals)} meals, {len(recent_exercises)} workouts")
            return context
            
        except Exception as e:
            print(f"❌ Error getting user context: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
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
    
    def _calculate_weight_trend(self, weight_entries: List[Dict]) -> str:
        if len(weight_entries) < 2:
            return "insufficient_data"
        
        latest = weight_entries[0]['weight']
        oldest = weight_entries[-1]['weight']
        change = latest - oldest
        
        if abs(change) < 0.5:
            return "stable"
        elif change > 0:
            return f"gaining_{abs(change):.1f}kg"
        else:
            return f"losing_{abs(change):.1f}kg"
    
    def _create_system_prompt(self, context: Dict[str, Any]) -> str:
        """Create enhanced system prompt with all activity data"""
        user_profile = context.get('user_profile', {})
        today_progress = context.get('today_progress', {})
        weekly_summary = context.get('weekly_summary', {})
        goals_progress = context.get('goals_progress', {})
        
        # Safe division to avoid None errors
        def safe_percentage(value, goal):
            if value is None or goal is None or goal == 0:
                return 0
            return (value / goal) * 100
        
        # Calculate completion percentages safely
        calorie_completion = safe_percentage(
            today_progress.get('total_calories', 0),
            goals_progress.get('daily_calorie_goal', 2000)
        )
        water_completion = safe_percentage(
            today_progress.get('water_glasses', 0),
            goals_progress.get('water_goal_glasses', 8)
        )
        step_completion = safe_percentage(
            today_progress.get('steps', 0),
            goals_progress.get('step_goal', 10000)
        )
        
        # Use safe formatting for numbers that might be None
        def safe_format(value, format_str="{}", default="Not set"):
            if value is None:
                return default
            if format_str == "{:,}":
                return f"{value:,}"
            return str(value)
        
        prompt = f"""You are a personalized AI health coach for {user_profile.get('name', 'User')}. You have access to their complete activity data.

USER PROFILE:
- Age: {safe_format(user_profile.get('age'))}, Gender: {safe_format(user_profile.get('gender'))}
- Current Weight: {safe_format(user_profile.get('weight'))}kg, Target: {safe_format(user_profile.get('target_weight'))}kg
- Primary Goal: {safe_format(user_profile.get('primary_goal'))}
- Activity Level: {safe_format(user_profile.get('activity_level'))}
- TDEE: {safe_format(user_profile.get('tdee'))} calories
- Preferred Workouts: {', '.join(user_profile.get('preferred_workouts', [])) or 'Not specified'}
- Dietary Preferences: {', '.join(user_profile.get('dietary_preferences', [])) or 'None specified'}

TODAY'S PROGRESS ({today_progress.get('date')}):
📊 NUTRITION:
- Meals Logged: {len(today_progress.get('meals', []))} meals
- Calories: {today_progress.get('total_calories')} / {goals_progress.get('daily_calorie_goal')} ({calorie_completion:.0f}% complete)
- Protein: {today_progress.get('total_protein')}g, Carbs: {today_progress.get('total_carbs')}g, Fat: {today_progress.get('total_fat')}g

💧 HYDRATION:
- Water: {today_progress.get('water_glasses')} / {goals_progress.get('water_goal_glasses')} glasses ({water_completion:.0f}% complete)

🏃 ACTIVITY:
- Exercise: {today_progress.get('exercise_minutes')} minutes
- Exercises: {', '.join(today_progress.get('exercises_done', [])) if today_progress.get('exercises_done') else 'None logged'}
- Steps: {safe_format(today_progress.get('steps'), '{:,}')} / {safe_format(goals_progress.get('step_goal'), '{:,}')} ({step_completion:.0f}% complete)

😴 SLEEP:
- Last Night: {today_progress.get('sleep_hours')} hours
- Quality: {today_progress.get('sleep_quality')}

⚖️ WEIGHT:
- Today's Weight: {'Logged - ' + str(today_progress.get('weight_logged')) + 'kg' if today_progress.get('weight_logged') else 'Not logged'}

WEEKLY TRENDS:
- Average Daily Calories: {safe_format(weekly_summary.get('avg_daily_calories'))}
- Total Workouts: {weekly_summary.get('total_workouts')}
- Average Sleep: {safe_format(weekly_summary.get('avg_sleep_hours'))} hours
- Weight Trend: {weekly_summary.get('weight_trend')}

COACHING INSTRUCTIONS:
1. Always reference their actual logged data when giving advice
2. Be specific about what they've accomplished today and what's left to do
3. Provide encouragement based on their progress percentages
4. Suggest specific next actions based on incomplete activities
5. Keep responses conversational, supportive, and actionable
6. If they haven't logged certain activities, gently remind them to do so
7. Use their name ({user_profile.get('name')}) occasionally to personalize responses

Remember: You can see all their logged activities, so be specific and reference their actual data."""
        
        return prompt.strip()
    
    async def generate_chat_response(self, user_id: str, message: str) -> str:
        """Generate chat response with message persistence"""
        try:
            print(f"💬 Generating chat response for user: {user_id}")
            
            # Save user message
            try:
                await self.supabase_service.save_chat_message(user_id, message, is_user=True)
            except Exception as e:
                print(f"⚠️ Error saving user message: {e}")
            
            # Get comprehensive user context with today's activities
            user_context = await self.get_user_context(user_id)
            print(f"📊 User context retrieved: {bool(user_context)}")
            
            # Get recent messages
            recent_messages = []
            try:
                recent_messages = await self.supabase_service.get_recent_chat_context(user_id, limit=10)
                print(f"💬 Retrieved {len(recent_messages)} recent messages")
            except Exception as e:
                print(f"⚠️ Error getting recent chat context: {e}")
            
            # Create enhanced system prompt with all activity data
            system_prompt = self._create_system_prompt(user_context)
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
            # LOG THE ACTUAL ERROR
            print(f"❌ Error generating chat response: {str(e)}")
            print(f"❌ Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()  # This will print the full stack trace
            
            # Return fallback with error info for debugging
            return f"I'm having trouble connecting to my AI service. Error: {str(e)[:100]}... Please try again or ask about nutrition, exercise, or your goals."

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