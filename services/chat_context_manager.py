# services/chat_context_manager.py
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
import json
from services.supabase_service import get_supabase_service

class ChatContextManager:
    def __init__(self):
        self.supabase_service = get_supabase_service()
    
    async def get_or_create_context(self, user_id: str, target_date: date = None) -> Dict[str, Any]:
        """Get existing context or create a new one for the specified date"""
        if target_date is None:
            target_date = datetime.now().date()
        
        try:
            # Try to get existing context
            response = self.supabase_service.client.table('chat_contexts')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('date', str(target_date))\
                .execute()
            
            if response.data:
                context_record = response.data[0]
                return {
                    'context': context_record['context_data'],
                    'version': context_record['version'],
                    'last_updated': context_record['last_updated']
                }
            
            # Create new context if none exists
            return await self.create_initial_context(user_id, target_date)
            
        except Exception as e:
            print(f"Error getting/creating context: {e}")
            # Fallback to generating fresh context
            return await self.generate_fresh_context(user_id, target_date)
    
    async def create_initial_context(self, user_id: str, target_date: date) -> Dict[str, Any]:
        """Create initial context for a new day"""
        try:
            # Get user profile
            user = await self.supabase_service.get_user_by_id(user_id)
            if not user:
                raise Exception("User not found")
            
            # Initialize empty context structure
            initial_context = {
                'user_profile': {
                    'name': user.get('name', ''),
                    'age': user.get('age'),
                    'weight': user.get('weight'),
                    'height': user.get('height'),
                    'primary_goal': user.get('primary_goal'),
                    'weight_goal': user.get('weight_goal'),
                    'activity_level': user.get('activity_level'),
                    'tdee': user.get('tdee'),
                    'target_weight': user.get('target_weight'),
                    'dietary_preferences': user.get('dietary_preferences', []),
                    'medical_conditions': user.get('medical_conditions', []),
                },
                'today_progress': {
                    'date': str(target_date),
                    'meals': [],
                    'exercises': [],
                    'water_glasses': 0,
                    'steps': 0,
                    'weight': None,
                    'sleep_hours': None,
                    'supplements_taken': [],
                    'totals': {
                        'calories': 0,
                        'protein': 0,
                        'carbs': 0,
                        'fat': 0,
                        'fiber': 0
                    }
                },
                'context_metadata': {
                    'created_at': datetime.now().isoformat(),
                    'version': 1,
                    'day_of_week': target_date.strftime('%A'),
                }
            }
            
            # Save to database
            response = self.supabase_service.client.table('chat_contexts')\
                .insert({
                    'user_id': user_id,
                    'date': str(target_date),
                    'context_data': initial_context,
                    'version': 1
                })\
                .execute()
            
            return {
                'context': initial_context,
                'version': 1,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error creating initial context: {e}")
            raise
    
    async def update_context_activity(
        self, 
        user_id: str, 
        activity_type: str, 
        data: Dict[str, Any],
        target_date: date = None
    ) -> Dict[str, Any]:
        """Update context when user logs an activity"""
        if target_date is None:
            target_date = datetime.now().date()
        
        try:
            # Get current context
            current = await self.get_or_create_context(user_id, target_date)
            context = current['context']
            version = current['version']
            
            # Update based on activity type
            if activity_type == 'meal':
                # Add meal to list
                meal_entry = {
                    'id': data.get('id'),
                    'food_item': data.get('food_item'),
                    'meal_type': data.get('meal_type'),
                    'calories': data.get('calories', 0),
                    'protein_g': data.get('protein_g', 0),
                    'carbs_g': data.get('carbs_g', 0),
                    'fat_g': data.get('fat_g', 0),
                    'fiber_g': data.get('fiber_g', 0),
                    'logged_at': data.get('created_at', datetime.now().isoformat())
                }
                context['today_progress']['meals'].append(meal_entry)
                
                # Update totals
                context['today_progress']['totals']['calories'] += data.get('calories', 0)
                context['today_progress']['totals']['protein'] += data.get('protein_g', 0)
                context['today_progress']['totals']['carbs'] += data.get('carbs_g', 0)
                context['today_progress']['totals']['fat'] += data.get('fat_g', 0)
                context['today_progress']['totals']['fiber'] += data.get('fiber_g', 0)
            
            elif activity_type == 'exercise':
                exercise_entry = {
                    'id': data.get('id'),
                    'exercise_name': data.get('exercise_name'),
                    'muscle_group': data.get('muscle_group'),
                    'duration_minutes': data.get('duration_minutes', 0),
                    'calories_burned': data.get('calories_burned', 0),
                    'sets': data.get('sets'),
                    'reps': data.get('reps'),
                    'weight_kg': data.get('weight_kg'),
                    'logged_at': data.get('created_at', datetime.now().isoformat())
                }
                context['today_progress']['exercises'].append(exercise_entry)
            
            elif activity_type == 'water':
                context['today_progress']['water_glasses'] = data.get('glasses_consumed', 0)
            
            elif activity_type == 'steps':
                context['today_progress']['steps'] = data.get('steps', 0)
            
            elif activity_type == 'weight':
                context['today_progress']['weight'] = data.get('weight', 0)
            
            elif activity_type == 'sleep':
                context['today_progress']['sleep_hours'] = data.get('total_hours', 0)
            
            elif activity_type == 'supplement':
                if data.get('taken') and data.get('supplement_name'):
                    if data.get('supplement_name') not in context['today_progress']['supplements_taken']:
                        context['today_progress']['supplements_taken'].append(data.get('supplement_name'))
                elif not data.get('taken') and data.get('supplement_name'):
                    # Remove from list if marked as not taken
                    context['today_progress']['supplements_taken'] = [
                        s for s in context['today_progress']['supplements_taken'] 
                        if s != data.get('supplement_name')
                    ]
            
            # Update metadata
            context['context_metadata']['last_activity'] = activity_type
            context['context_metadata']['last_activity_time'] = datetime.now().isoformat()
            
            # Save updated context with optimistic locking
            response = self.supabase_service.client.table('chat_contexts')\
                .update({
                    'context_data': context,
                    'version': version + 1,
                    'last_updated': datetime.now().isoformat()
                })\
                .eq('user_id', user_id)\
                .eq('date', str(target_date))\
                .eq('version', version)\
                .execute()
            
            if not response.data:
                # Version conflict, retry with fresh context
                return await self.update_context_activity(user_id, activity_type, data, target_date)
            
            return {
                'success': True,
                'context': context,
                'version': version + 1
            }
            
        except Exception as e:
            print(f"Error updating context: {e}")
            return {'success': False, 'error': str(e)}
    
    async def remove_from_context(
        self,
        user_id: str,
        activity_type: str,
        item_id: str,
        target_date: date = None
    ) -> Dict[str, Any]:
        """Remove an activity from context (for deletes)"""
        if target_date is None:
            target_date = datetime.now().date()
        
        try:
            # Get current context
            current = await self.get_or_create_context(user_id, target_date)
            context = current['context']
            version = current['version']
            
            if activity_type == 'meal':
                # Find and remove meal
                removed_meal = None
                for meal in context['today_progress']['meals']:
                    if meal.get('id') == item_id:
                        removed_meal = meal
                        break
                
                if removed_meal:
                    context['today_progress']['meals'].remove(removed_meal)
                    # Update totals
                    context['today_progress']['totals']['calories'] -= removed_meal.get('calories', 0)
                    context['today_progress']['totals']['protein'] -= removed_meal.get('protein_g', 0)
                    context['today_progress']['totals']['carbs'] -= removed_meal.get('carbs_g', 0)
                    context['today_progress']['totals']['fat'] -= removed_meal.get('fat_g', 0)
                    context['today_progress']['totals']['fiber'] -= removed_meal.get('fiber_g', 0)
            
            elif activity_type == 'exercise':
                # Find and remove exercise
                context['today_progress']['exercises'] = [
                    ex for ex in context['today_progress']['exercises']
                    if ex.get('id') != item_id
                ]
            
            # Save updated context
            response = self.supabase_service.client.table('chat_contexts')\
                .update({
                    'context_data': context,
                    'version': version + 1,
                    'last_updated': datetime.now().isoformat()
                })\
                .eq('user_id', user_id)\
                .eq('date', str(target_date))\
                .eq('version', version)\
                .execute()
            
            return {
                'success': True,
                'context': context,
                'version': version + 1
            }
            
        except Exception as e:
            print(f"Error removing from context: {e}")
            return {'success': False, 'error': str(e)}
    
    async def rebuild_context(self, user_id: str, target_date: date = None) -> Dict[str, Any]:
        """Rebuild context from source tables (for fixing sync issues)"""
        if target_date is None:
            target_date = datetime.now().date()
        
        try:
            # Delete existing context
            self.supabase_service.client.table('chat_contexts')\
                .delete()\
                .eq('user_id', user_id)\
                .eq('date', str(target_date))\
                .execute()
            
            # Generate fresh context from source tables
            return await self.generate_fresh_context(user_id, target_date)
            
        except Exception as e:
            print(f"Error rebuilding context: {e}")
            raise
    
    async def generate_fresh_context(self, user_id: str, target_date: date) -> Dict[str, Any]:
        """Generate fresh context from source tables (fallback)"""
        try:
            # Use existing context generation logic
            from api.chat import get_user_chat_context
            
            context = await get_user_chat_context(user_id)
            
            # Save to cache for next time
            try:
                self.supabase_service.client.table('chat_contexts')\
                    .upsert({
                        'user_id': user_id,
                        'date': str(target_date),
                        'context_data': context,
                        'version': 1
                    })\
                    .execute()
            except:
                pass  # Don't fail if cache save fails
            
            return {
                'context': context,
                'version': 1,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating fresh context: {e}")
            raise

# Singleton instance
_context_manager = None

def get_context_manager() -> ChatContextManager:
    global _context_manager
    if _context_manager is None:
        _context_manager = ChatContextManager()
    return _context_manager