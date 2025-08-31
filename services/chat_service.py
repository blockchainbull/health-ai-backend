# services/chat_service.py
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from services.openai_service import get_openai_service
from services.supabase_service import get_supabase_service

class HealthChatService:
    def __init__(self):
        self.openai_service = get_openai_service()
        self.supabase_service = get_supabase_service()
    
    async def get_today_activities(self, user_id: str, target_date: date) -> dict:
        """Fetch all activities for a specific date"""
        activities = {}
        
        try:
            # Get today's meals
            meals_response = await self.supabase_service.client.table('meal_logs')\
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
            water_response = await self.supabase_service.client.table('water_logs')\
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
            sleep_response = await self.supabase_service.client.table('sleep_logs')\
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
            weight_response = await self.supabase_service.client.table('weight_logs')\
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
            steps_response = await self.supabase_service.client.table('step_logs')\
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
            
            # Get recent activity data
            recent_meals = []
            recent_exercises = []
            recent_sleep = []
            recent_weight = []
            recent_water = []
            
            # Try to get weekly data
            try:
                recent_meals = await self.supabase_service.get_meals_by_date_range(
                    user_id, str(week_ago), str(today)
                )
            except AttributeError:
                print("⚠️ get_meals_by_date_range method not available")
                try:
                    recent_meals = await self.supabase_service.get_meals_by_user(user_id)
                except:
                    recent_meals = []
            except Exception as e:
                print(f"⚠️ Error getting meals: {e}")
                recent_meals = []
            
            try:
                recent_exercises = await self.supabase_service.get_exercise_logs(
                    user_id, start_date=str(week_ago), end_date=str(today)
                )
            except:
                recent_exercises = []
            
            try:
                recent_sleep = await self.supabase_service.get_sleep_history(user_id, limit=7)
            except:
                recent_sleep = []
            
            try:
                recent_weight = await self.supabase_service.get_weight_history(user_id, limit=5)
            except:
                recent_weight = []
            
            try:
                # Get water history
                water_response = await self.supabase_service.client.table('water_logs')\
                    .select('*')\
                    .eq('user_id', user_id)\
                    .gte('date', str(week_ago))\
                    .lte('date', str(today))\
                    .execute()
                recent_water = water_response.data if water_response.data else []
            except:
                recent_water = []
            
            # Calculate progress metrics
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
                    "total_protein": sum(m.get('protein_g', 0) for m in today_activities.get('meals', [])),
                    "total_carbs": sum(m.get('carbs_g', 0) for m in today_activities.get('meals', [])),
                    "total_fat": sum(m.get('fat_g', 0) for m in today_activities.get('meals', [])),
                    "water_glasses": today_activities.get('water', {}).get('glasses', 0),
                    "exercise_minutes": sum(e.get('duration_minutes', 0) for e in today_activities.get('exercise', [])),
                    "exercises_done": [e.get('exercise_type', 'Unknown') for e in today_activities.get('exercise', [])],
                    "steps": today_activities.get('steps', {}).get('count', 0),
                    "sleep_hours": today_activities.get('sleep', {}).get('total_hours', 0),
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
                    "daily_calorie_goal": user.get('tdee', 2000),
                    "water_goal_glasses": user.get('water_intake_glasses', 8),
                    "step_goal": user.get('step_goal', 10000),
                    "sleep_goal_hours": user.get('sleep_hours', 8),
                },
                "recent_activity": {
                    "meals_this_week": len(recent_meals),
                    "avg_daily_calories": self._calculate_avg_calories(recent_meals),
                    "workouts_this_week": len(recent_exercises),
                    "total_exercise_minutes": sum(e.get('duration_minutes', 0) for e in recent_exercises),
                }
            }
            
            print(f"✅ User context prepared with today's data and {len(recent_meals)} weekly meals, {len(recent_exercises)} workouts")
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
        
        # Calculate completion percentages
        calorie_completion = (today_progress.get('total_calories', 0) / goals_progress.get('daily_calorie_goal', 2000)) * 100
        water_completion = (today_progress.get('water_glasses', 0) / goals_progress.get('water_goal_glasses', 8)) * 100
        step_completion = (today_progress.get('steps', 0) / goals_progress.get('step_goal', 10000)) * 100
        
        prompt = f"""You are a personalized AI health coach for {user_profile.get('name', 'User')}. You have access to their complete activity data.

USER PROFILE:
- Age: {user_profile.get('age')}, Gender: {user_profile.get('gender')}
- Current Weight: {user_profile.get('weight')}kg, Target: {user_profile.get('target_weight')}kg
- Primary Goal: {user_profile.get('primary_goal')}
- Activity Level: {user_profile.get('activity_level')}
- TDEE: {user_profile.get('tdee')} calories
- Preferred Workouts: {', '.join(user_profile.get('preferred_workouts', []))}
- Dietary Preferences: {', '.join(user_profile.get('dietary_preferences', []))}

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
- Steps: {today_progress.get('steps'):,} / {goals_progress.get('step_goal'):,} ({step_completion:.0f}% complete)

😴 SLEEP:
- Last Night: {today_progress.get('sleep_hours')} hours
- Quality: {today_progress.get('sleep_quality')}

⚖️ WEIGHT:
- Today's Weight: {'Logged - ' + str(today_progress.get('weight_logged')) + 'kg' if today_progress.get('weight_logged') else 'Not logged'}

💊 SUPPLEMENTS:
- Taken: {sum(1 for taken in today_progress.get('supplements_taken', {}).values() if taken)} supplements

WEEKLY TRENDS:
- Average Daily Calories: {weekly_summary.get('avg_daily_calories')}
- Total Workouts: {weekly_summary.get('total_workouts')}
- Average Sleep: {weekly_summary.get('avg_sleep_hours')} hours
- Weight Trend: {weekly_summary.get('weight_trend')}
- Hydration Consistency: {weekly_summary.get('hydration_consistency')}%

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
            print(f"Generating chat response for user: {user_id}")
            
            # Save user message
            try:
                await self.supabase_service.save_chat_message(user_id, message, is_user=True)
            except Exception as e:
                print(f"Error saving user message: {e}")
            
            # Get comprehensive user context with today's activities
            user_context = await self.get_user_context(user_id)
            
            # Get recent messages
            recent_messages = []
            try:
                recent_messages = await self.supabase_service.get_recent_chat_context(user_id, limit=10)
            except Exception as e:
                print(f"Error getting recent chat context: {e}")
            
            # Create enhanced system prompt with all activity data
            system_prompt = self._create_system_prompt(user_context)
            
            # Build conversation for OpenAI
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent conversation context
            for msg in recent_messages:
                role = "user" if msg.get("is_user") else "assistant"
                messages.append({"role": role, "content": msg.get("message", "")})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Get AI response
            response = await self.openai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=600
            )
            
            reply = response.choices[0].message.content.strip()
            
            # Save AI response
            try:
                await self.supabase_service.save_chat_message(user_id, reply, is_user=False)
            except Exception as e:
                print(f"Error saving AI response: {e}")
            
            print(f"Generated response with full context: {len(reply)} characters")
            return reply
            
        except Exception as e:
            print(f"Error generating chat response: {e}")
            return self._get_fallback_response(message, user_id)
    
    def _get_fallback_response(self, message: str, user_id: str) -> str:
        """Generate a helpful fallback response when AI is unavailable"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['dinner', 'food', 'meal', 'eat']):
            return "For a healthy dinner, I recommend lean protein with vegetables and complex carbs. Try grilled chicken with roasted vegetables, or salmon with quinoa and steamed broccoli."
        elif any(word in message_lower for word in ['exercise', 'workout', 'fitness']):
            return "For today's workout, try a mix of cardio and strength training. Even 30 minutes of walking or bodyweight exercises can make a difference!"
        elif any(word in message_lower for word in ['progress', 'weight', 'goal']):
            return "Keep tracking your daily habits! Consistency with nutrition and exercise is key to reaching your goals."
        else:
            return "I'm having trouble connecting right now, but I'm here to help with your health journey! Try asking about nutrition, exercise, or your goals."

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