# services/chat_service.py
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from services.openai_service import get_openai_service
from services.supabase_service import get_supabase_service

class HealthChatService:
    def __init__(self):
        self.openai_service = get_openai_service()
        self.supabase_service = get_supabase_service()
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user context for chat"""
        try:
            print(f"🔍 Getting user context for: {user_id}")
            
            # Get user profile
            user = await self.supabase_service.get_user_by_id(user_id)
            if not user:
                print(f"❌ No user found for ID: {user_id}")
                return {}
            
            # Get recent activity data
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            # Initialize empty data structures
            recent_meals = []
            recent_exercises = []
            recent_sleep = []
            recent_weight = []
            supplement_prefs = []
            today_supplements = {}
            
            # Try to get data, but don't fail if methods don't exist
            try:
                recent_meals = await self.supabase_service.get_meals_by_date_range(
                    user_id, str(week_ago), str(today)
                )
            except AttributeError:
                print("⚠️ get_meals_by_date_range method not available")
                try:
                    # Try alternative method
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
                supplement_prefs = await self.supabase_service.get_supplement_preferences(user_id)
                today_supplements = await self.supabase_service.get_supplement_status_by_date(user_id, today)
            except:
                supplement_prefs = []
                today_supplements = {}
            
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
                },
                "recent_activity": {
                    "meals_this_week": len(recent_meals),
                    "avg_daily_calories": self._calculate_avg_calories(recent_meals),
                    "workouts_this_week": len(recent_exercises),
                    "total_exercise_minutes": sum(e.get('duration_minutes', 0) for e in recent_exercises),
                    "avg_sleep_hours": self._calculate_avg_sleep(recent_sleep),
                    "weight_trend": self._calculate_weight_trend(recent_weight),
                    "supplement_adherence": self._calculate_supplement_adherence(supplement_prefs, today_supplements),
                },
                "goals_progress": {
                    "weight_progress": self._calculate_weight_progress(user, recent_weight),
                    "activity_consistency": self._calculate_activity_consistency(recent_exercises),
                    "nutrition_quality": self._calculate_nutrition_quality(recent_meals),
                }
            }
            
            print(f"✅ User context prepared with {len(recent_meals)} meals, {len(recent_exercises)} workouts")
            return context
            
        except Exception as e:
            print(f"❌ Error getting user context: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
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
    
    def _calculate_supplement_adherence(self, prefs: List[Dict], today_status: Dict) -> float:
        if not prefs:
            return 100.0
        taken = sum(1 for taken in today_status.values() if taken)
        return round((taken / len(prefs)) * 100, 1)
    
    def _calculate_weight_progress(self, user: Dict, recent_weight: List[Dict]) -> Dict:
        target = user.get('target_weight')
        current = user.get('weight')
        starting = user.get('starting_weight', current)
        
        if not all([target, current, starting]):
            return {"status": "no_data"}
        
        total_needed = abs(target - starting)
        progress_made = abs(current - starting)
        remaining = abs(target - current)
        
        progress_percentage = (progress_made / total_needed * 100) if total_needed > 0 else 100
        
        return {
            "current_weight": current,
            "target_weight": target,
            "starting_weight": starting,
            "progress_percentage": round(progress_percentage, 1),
            "remaining": round(remaining, 1),
            "on_track": self._is_on_track(user, recent_weight)
        }
    
    def _calculate_activity_consistency(self, exercises: List[Dict]) -> Dict:
        if not exercises:
            return {"status": "no_activity", "score": 0}
        
        # Group by day
        days_with_activity = set()
        for exercise in exercises:
            day = exercise.get('exercise_date', exercise.get('date', '')).split('T')[0]
            if day:
                days_with_activity.add(day)
        
        consistency_score = len(days_with_activity) / 7 * 100
        
        return {
            "days_active": len(days_with_activity),
            "consistency_score": round(consistency_score, 1),
            "status": "good" if consistency_score >= 70 else "needs_improvement"
        }
    
    def _calculate_nutrition_quality(self, meals: List[Dict]) -> Dict:
        if not meals:
            return {"status": "no_data", "score": 0}
        
        # Simple scoring based on variety and frequency
        total_meals = len(meals)
        days_with_meals = len(set(meal.get('date', '').split('T')[0] for meal in meals if meal.get('date')))
        avg_meals_per_day = total_meals / max(days_with_meals, 1)
        
        score = min(100, (avg_meals_per_day / 3) * 100)
        
        return {
            "total_meals": total_meals,
            "days_tracked": days_with_meals,
            "avg_meals_per_day": round(avg_meals_per_day, 1),
            "score": round(score, 1),
            "status": "good" if score >= 70 else "needs_improvement"
        }
    
    def _is_on_track(self, user: Dict, recent_weight: List[Dict]) -> bool:
        weight_goal = user.get('weight_goal', '')
        if len(recent_weight) < 2:
            return True
        
        latest = recent_weight[0]['weight']
        previous = recent_weight[1]['weight']
        change = latest - previous
        
        if 'lose' in weight_goal.lower():
            return change <= 0
        elif 'gain' in weight_goal.lower():
            return change >= 0
        else:  # maintain_weight
            return abs(change) <= 1.0
    
    async def generate_chat_response(self, user_id: str, message: str) -> str:
        """Generate personalized chat response with full user context"""
        try:
            print(f"💬 Generating chat response for user: {user_id}")
            print(f"💬 Message: {message[:100]}...")
            
            user_context = await self.get_user_context(user_id)
            system_prompt = self._create_system_prompt(user_context)
            
            response = await self.openai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            reply = response.choices[0].message.content.strip()
            print(f"✅ Generated {len(reply)} character response")
            return reply
            
        except Exception as e:
            print(f"❌ Error generating chat response: {e}")
            import traceback
            traceback.print_exc()
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
    
    def _create_system_prompt(self, context: Dict[str, Any]) -> str:
        """Create detailed system prompt with user context"""
        user_profile = context.get('user_profile', {})
        recent_activity = context.get('recent_activity', {})
        goals_progress = context.get('goals_progress', {})
        
        # Get goal-specific guidance
        weight_goal = user_profile.get('weight_goal', 'maintain_weight')
        goal_guidance = self._get_goal_specific_guidance(weight_goal)
        
        prompt = f"""
You are a personalized AI health and fitness coach. You have access to the user's complete health profile and recent activity data.

USER PROFILE:
- Name: {user_profile.get('name', 'User')}
- Age: {user_profile.get('age', 'Unknown')} years old
- Gender: {user_profile.get('gender', 'Unknown')}
- Height: {user_profile.get('height', 'Unknown')} cm
- Current Weight: {user_profile.get('weight', 'Unknown')} kg
- Target Weight: {user_profile.get('target_weight', 'Unknown')} kg
- Primary Goal: {user_profile.get('primary_goal', 'General health')}
- Weight Goal: {user_profile.get('weight_goal', 'Unknown')}
- Activity Level: {user_profile.get('activity_level', 'Unknown')}
- BMI: {user_profile.get('bmi', 'Unknown')}
- TDEE: {user_profile.get('tdee', 'Unknown')} calories/day
- Fitness Level: {user_profile.get('fitness_level', 'Unknown')}
- Sleep Target: {user_profile.get('sleep_hours', 'Unknown')} hours
- Bedtime: {user_profile.get('bedtime', 'Unknown')}
- Wake Time: {user_profile.get('wakeup_time', 'Unknown')}
- Dietary Preferences: {', '.join(user_profile.get('dietary_preferences', []))}
- Medical Conditions: {', '.join(user_profile.get('medical_conditions', []))}
- Preferred Workouts: {', '.join(user_profile.get('preferred_workouts', []))}

RECENT ACTIVITY (Last 7 days):
- Meals logged: {recent_activity.get('meals_this_week', 0)}
- Average daily calories: {recent_activity.get('avg_daily_calories', 0)}
- Workouts completed: {recent_activity.get('workouts_this_week', 0)}
- Total exercise minutes: {recent_activity.get('total_exercise_minutes', 0)}
- Average sleep: {recent_activity.get('avg_sleep_hours', 0)} hours
- Weight trend: {recent_activity.get('weight_trend', 'unknown')}
- Supplement adherence: {recent_activity.get('supplement_adherence', 0)}%

PROGRESS TOWARDS GOALS:
- Weight progress: {goals_progress.get('weight_progress', {}).get('progress_percentage', 0)}% towards target
- Activity consistency: {goals_progress.get('activity_consistency', {}).get('score', 0)}%
- Nutrition tracking: {goals_progress.get('nutrition_quality', {}).get('score', 0)}%

{goal_guidance}

COACHING STYLE:
- Be encouraging and supportive
- Reference specific data when relevant (e.g., "I see you've logged X calories today")
- Provide actionable, personalized advice
- Celebrate achievements and progress
- Address areas needing improvement with kindness
- Ask follow-up questions to engage the user
- Use their name naturally in conversation
- Be specific about recommendations based on their data
- Never mention "frameworks" or "plans" - speak naturally about their goals

NEVER say: "According to your framework" or "Your plan suggests"
ALWAYS say: "For your goals" or "Since you want to lose weight" or "Based on your progress"

Respond naturally and conversationally, incorporating relevant data points to show you understand their journey.
"""
        
        return prompt.strip()
    
    def _get_goal_specific_guidance(self, weight_goal: str) -> str:
        """Get goal-specific coaching guidance"""
        weight_goal_lower = weight_goal.lower()
        
        if 'lose' in weight_goal_lower:
            return """
For weight loss focus:
- Emphasize caloric deficit (eat fewer calories than TDEE)
- Recommend high protein intake (1.6g per kg bodyweight)
- Suggest cardio and strength training combination
- Encourage hydration (10+ glasses water daily)
- Promote portion control and meal tracking
- Recommend 0.5-1kg loss per week as safe target
"""
        elif 'gain' in weight_goal_lower:
            return """
For weight gain focus:
- Emphasize caloric surplus (eat more calories than TDEE)
- Recommend high protein intake (2.0g per kg bodyweight)
- Focus on strength training for muscle building
- Suggest frequent meals (5-6 per day)
- Encourage calorie-dense, nutritious foods
- Recommend 0.25-0.5kg gain per week as safe target
"""
        else:  # maintain_weight
            return """
For weight maintenance focus:
- Emphasize caloric balance (eat around TDEE calories)
- Recommend balanced macronutrients
- Suggest variety in exercise types
- Encourage intuitive eating practices
- Focus on sustainable lifestyle habits
- Allow for small weight fluctuations (±1kg)
"""

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