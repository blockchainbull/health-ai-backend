# services/chat_service.py
import json
from typing import Dict, Any, List
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
                return {}
            
            # Get recent activity data
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            # Get recent meals
            recent_meals = await self.supabase_service.get_meals_by_date_range(
                user_id, str(week_ago), str(today)
            )
            
            # Get recent exercise
            recent_exercises = await self.supabase_service.get_exercise_logs(
                user_id, start_date=str(week_ago), end_date=str(today)
            )
            
            # Get recent sleep
            recent_sleep = await self.supabase_service.get_sleep_history(
                user_id, limit=7
            )
            
            # Get recent weight
            recent_weight = await self.supabase_service.get_weight_history(
                user_id, limit=5
            )
            
            # Get supplement status
            supplement_prefs = await self.supabase_service.get_supplement_preferences(user_id)
            today_supplements = await self.supabase_service.get_supplement_status_by_date(user_id, today)
            
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
            return {}
    
    def _calculate_avg_calories(self, meals: List[Dict]) -> float:
        if not meals:
            return 0
        total_calories = sum(meal.get('calories', 0) for meal in meals)
        days = len(set(meal.get('date', '').split('T')[0] for meal in meals))
        return round(total_calories / max(days, 1), 1)
    
    def _calculate_avg_sleep(self, sleep_entries: List[Dict]) -> float:
        if not sleep_entries:
            return 0
        total_hours = sum(entry.get('total_hours', 0) for entry in sleep_entries)
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
        taken = sum(1 for name in today_status.values() if name)
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
            day = exercise.get('exercise_date', '').split('T')[0]
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
        days_with_meals = len(set(meal.get('date', '').split('T')[0] for meal in meals))
        avg_meals_per_day = total_meals / max(days_with_meals, 1)
        
        score = min(100, (avg_meals_per_day / 3) * 100)  # Assuming 3 meals per day is ideal
        
        return {
            "total_meals": total_meals,
            "days_tracked": days_with_meals,
            "avg_meals_per_day": round(avg_meals_per_day, 1),
            "score": round(score, 1),
            "status": "good" if score >= 70 else "needs_improvement"
        }
    
    def _is_on_track(self, user: Dict, recent_weight: List[Dict]) -> bool:
        # Simple logic - can be enhanced based on timeline and goals
        weight_goal = user.get('weight_goal', '')
        if len(recent_weight) < 2:
            return True
        
        latest = recent_weight[0]['weight']
        previous = recent_weight[1]['weight']
        change = latest - previous
        
        if weight_goal == 'lose_weight':
            return change <= 0
        elif weight_goal == 'gain_weight':
            return change >= 0
        else:  # maintain_weight
            return abs(change) <= 1.0
    
    async def generate_chat_response(self, user_id: str, message: str) -> str:
        """Generate personalized chat response with full user context"""
        try:
            user_context = await self.get_user_context(user_id)
            
            # Create comprehensive system prompt
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
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Error generating chat response: {e}")
            return "I'm sorry, I'm having trouble accessing your data right now. Please try again later."
    
    def _create_system_prompt(self, context: Dict[str, Any]) -> str:
        """Create detailed system prompt with user context"""
        user_profile = context.get('user_profile', {})
        recent_activity = context.get('recent_activity', {})
        goals_progress = context.get('goals_progress', {})
        
        prompt = f"""
            You are a personalized AI health coach. Never mention "frameworks" or "plans" - just give natural advice.
            
            USER PROFILE:
            - Goal: {user_profile.get('weight_goal', 'maintain health')}
            - Current: {user_profile.get('weight')}kg → Target: {user_profile.get('target_weight')}kg
            
            COACHING APPROACH:
            - For weight loss: Focus on caloric deficit, protein, cardio
            - For weight gain: Focus on caloric surplus, strength training
            - For maintenance: Focus on balance and sustainability
            
            NEVER say: "According to your framework" or "Your plan suggests"
            ALWAYS say: "For your goals" or "Since you want to lose weight" or "Based on your progress"
            
            Be natural, supportive, and reference their actual data.
            """
        
        return prompt.strip()

# Global instance
chat_service = None

def get_chat_service() -> HealthChatService:
    global chat_service
    if chat_service is None:
        chat_service = HealthChatService()
    return chat_service