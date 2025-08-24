# services/supabase_service.py
from supabase import create_client, Client
import os
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime, date, timezone, timedelta

class SupabaseService:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
        
        self.client: Client = create_client(url, key)
        print("✅ Supabase client initialized")
    
    # User Management Operations
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user in the database"""
        try:
            print(f"🔍 Creating user in Supabase: {user_data.get('email')}")
            
            # Ensure we have an ID
            if 'id' not in user_data:
                user_data['id'] = str(uuid.uuid4())
            
            # Insert user into Supabase
            response = self.client.table('users').insert(user_data).execute()
            
            if response.data:
                print(f"✅ User created successfully: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
                
        except Exception as e:
            print(f"❌ Error creating user in Supabase: {e}")
            raise Exception(f"Failed to create user: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            print(f"🔍 Getting user by ID: {user_id}")
            
            response = self.client.table('users').select('*').eq('id', user_id).execute()
            
            if response.data:
                print(f"✅ User found: {response.data[0]['email']}")
                return response.data[0]
            else:
                print(f"❌ User not found: {user_id}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting user by ID: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            print(f"🔍 Getting user by email: {email}")
            
            response = self.client.table('users').select('*').eq('email', email).execute()
            
            if response.data:
                print(f"✅ User found by email: {email}")
                return response.data[0]
            else:
                print(f"❌ User not found by email: {email}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting user by email: {e}")
            return None
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile including step goal"""
        try:
            response = self.client.table('users').update(user_data).eq('id', user_id).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error updating user: {e}")
            raise Exception(f"Failed to update user: {str(e)}")

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile including step goal"""
        try:
            response = self.client.table('users').select('*').eq('id', user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"❌ Error getting user: {e}")
            return None
    
    # Meal Operations (we'll expand this later)
    async def create_meal_entry(self, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new meal entry"""
        try:
            print(f"🔍 Creating meal entry with data: {meal_data}")
            
            # Ensure all nutrition fields are present
            required_fields = ['fiber_g', 'sugar_g', 'sodium_mg']
            for field in required_fields:
                if field not in meal_data:
                    print(f"⚠️ Missing {field} in meal_data, setting to 0")
                    meal_data[field] = 0
            
            response = self.client.table('meal_entries').insert(meal_data).execute()
            
            if response.data:
                created_meal = response.data[0]
                return created_meal
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            print(f"❌ Error creating meal entry: {e}")
            import traceback
            traceback.print_exc()
            raise e
    
    # Chat/Conversation Operations (placeholder for later)
    async def create_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a conversation entry (placeholder for later)"""
        try:
            print(f"🔍 Creating conversation for user: {conversation_data.get('user_id')}")
            
            if 'id' not in conversation_data:
                conversation_data['id'] = str(uuid.uuid4())
            
            response = self.client.table('conversations').insert(conversation_data).execute()
            
            if response.data:
                print(f"✅ Conversation created: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
                
        except Exception as e:
            print(f"❌ Error creating conversation: {e}")
            raise Exception(f"Failed to create conversation: {str(e)}")
    
    # Health check method
    async def health_check(self) -> Dict[str, Any]:
        """Check if Supabase connection is working"""
        try:
            # Simple query to test connection
            response = self.client.table('users').select('count').execute()
            
            return {
                "status": "healthy",
                "message": "Supabase connection working",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Supabase connection failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
    
    async def create_meal_entry(self, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a meal entry"""
        try:
            print(f"🔍 Creating meal entry for user: {meal_data.get('user_id')}")
        
            if 'id' not in meal_data:
                meal_data['id'] = str(uuid.uuid4())
        
            response = self.client.table('meal_entries').insert(meal_data).execute()
        
            if response.data:
                print(f"✅ Meal entry created: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
            
        except Exception as e:
            print(f"❌ Error creating meal entry: {e}")
            raise Exception(f"Failed to create meal entry: {str(e)}")

    async def get_user_meals(self, user_id: str, limit: int = 20, date_from: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user meals for date range"""
        try:
            print(f"🔍 Getting meals for user: {user_id}")
        
            query = self.client.table('meal_entries').select('*').eq('user_id', user_id)
        
            if date_from:
                query = query.gte('meal_date', date_from)
        
            response = query.order('meal_date', desc=True).limit(limit).execute()
        
            print(f"✅ Found {len(response.data)} meals")
            return response.data or []
        
        except Exception as e:
            print(f"❌ Error getting user meals: {e}")
            return []
        
    async def get_user_meals_by_date(self, user_id: str, date: str) -> List[Dict[str, Any]]:
        """Get user meals for a specific date"""
        try:
            print(f"🔍 Getting meals for user: {user_id}, date: {date}")
    
            # Handle different date formats
            if 'T' in date:
                date = date.split('T')[0]  # Extract just the date part
    
            # Query meals for the specific date - explicitly select all fields
            start_date = f"{date}T00:00:00"
            end_date = f"{date}T23:59:59"
    
            response = self.client.table('meal_entries').select(
                'id, user_id, food_item, quantity, meal_type, calories, '
                'protein_g, carbs_g, fat_g, fiber_g, sugar_g, sodium_mg, '
                'meal_date, logged_at, nutrition_data, preparation'
            ).eq(
                'user_id', user_id
            ).gte(
                'meal_date', start_date
            ).lte(
                'meal_date', end_date
            ).order('meal_date', desc=True).execute()
    
            meals = response.data or []
        
            # Debug: Check what we're getting
            print(f"✅ Found {len(meals)} meals for {date}")
            for meal in meals:
                print(f"   Meal: {meal.get('food_item')} - fiber: {meal.get('fiber_g')}, sugar: {meal.get('sugar_g')}, sodium: {meal.get('sodium_mg')}")
        
            return meals
    
        except Exception as e:
            print(f"❌ Error getting meals by date: {e}")
            import traceback
            traceback.print_exc()
            return []
        
    async def get_water_entry_by_date(self, user_id: str, entry_date: date) -> Optional[Dict[str, Any]]:
        """Get water entry for a specific date"""
        try:
            response = self.client.table('daily_water')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('date', str(entry_date))\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"❌ Error getting water entry by date: {e}")
            return None

    async def create_water_entry(self, water_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new water entry"""
        try:
            response = self.client.table('daily_water').insert(water_data).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error creating water entry: {e}")
            raise Exception(f"Failed to create water entry: {str(e)}")

    async def update_water_entry(self, entry_id: str, water_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing water entry"""
        try:
            response = self.client.table('daily_water').update(water_data).eq('id', entry_id).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error updating water entry: {e}")
            raise Exception(f"Failed to update water entry: {str(e)}")

    async def get_water_history(self, user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get water intake history for a user"""
        try:
            print(f"🔍 Getting {limit} water entries for user: {user_id}")
            
            response = self.client.table('daily_water')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('date', desc=True)\
                .limit(limit)\
                .execute()
            
            if response.data:
                # Format the data to ensure consistency
                formatted_entries = []
                for entry in response.data:
                    formatted_entry = {
                        'id': entry['id'],
                        'user_id': entry['user_id'],
                        'date': entry['date'],
                        'glasses_consumed': entry.get('glasses_consumed', 0),
                        'total_ml': float(entry.get('total_ml', 0.0)),
                        'target_ml': float(entry.get('target_ml', 2000.0)),
                        'notes': entry.get('notes'),
                        'created_at': entry.get('created_at'),
                        'updated_at': entry.get('updated_at')
                    }
                    formatted_entries.append(formatted_entry)
                
                print(f"✅ Retrieved {len(formatted_entries)} water entries")
                return formatted_entries
            
            return []
        except Exception as e:
            print(f"❌ Error getting water history: {e}")
            return []

    async def get_water_entries_in_range(self, user_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get water entries within a date range"""
        try:
            response = self.client.table('daily_water')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('date', start_date)\
                .lte('date', end_date)\
                .order('date', desc=True)\
                .execute()
            
            return response.data or []
        except Exception as e:
            print(f"❌ Error getting water entries in range: {e}")
            return []
        
    async def create_step_entry(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new step entry"""
        try:
            response = self.client.table('daily_steps').insert(step_data).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error creating step entry: {e}")
            raise Exception(f"Failed to create step entry: {str(e)}")

    async def update_step_entry(self, entry_id: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing step entry"""
        try:
            response = self.client.table('daily_steps').update(step_data).eq('id', entry_id).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error updating step entry: {e}")
            raise Exception(f"Failed to update step entry: {str(e)}")

    async def get_step_entry_by_date(self, user_id: str, entry_date: date) -> Optional[Dict[str, Any]]:
        """Get step entry for a specific date"""
        try:
            response = self.client.table('daily_steps')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('date', str(entry_date))\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"❌ Error getting step entry by date: {e}")
            return None

    async def get_step_history(self, user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get step history for a user"""
        try:
            print(f"🔍 Getting {limit} step entries for user: {user_id}")
            
            response = self.client.table('daily_steps')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('date', desc=True)\
                .limit(limit)\
                .execute()
            
            if response.data:
                # Format the data to ensure consistency
                formatted_entries = []
                for entry in response.data:
                    formatted_entry = {
                        'id': entry['id'],
                        'userId': entry['user_id'],  # Convert to Flutter format
                        'date': entry['date'],
                        'steps': entry.get('steps', 0),
                        'goal': entry.get('goal', 10000),
                        'caloriesBurned': float(entry.get('calories_burned', 0.0)),
                        'distanceKm': float(entry.get('distance_km', 0.0)),
                        'activeMinutes': entry.get('active_minutes', 0),
                        'sourceType': entry.get('source_type', 'manual'),
                        'lastSynced': entry.get('last_synced'),
                        'createdAt': entry.get('created_at'),
                        'updatedAt': entry.get('updated_at')
                    }
                    formatted_entries.append(formatted_entry)
                
                print(f"✅ Retrieved {len(formatted_entries)} step entries")
                return formatted_entries
            
            return []
        except Exception as e:
            print(f"❌ Error getting step history: {e}")
            return []

    async def get_step_entries_in_range(self, user_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get step entries within a date range"""
        try:
            response = self.client.table('daily_steps')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('date', start_date)\
                .lte('date', end_date)\
                .order('date', desc=True)\
                .execute()
            
            if response.data:
                # Format for Flutter
                formatted_entries = []
                for entry in response.data:
                    formatted_entry = {
                        'id': entry['id'],
                        'userId': entry['user_id'],
                        'date': entry['date'],
                        'steps': entry.get('steps', 0),
                        'goal': entry.get('goal', 10000),
                        'caloriesBurned': float(entry.get('calories_burned', 0.0)),
                        'distanceKm': float(entry.get('distance_km', 0.0)),
                        'activeMinutes': entry.get('active_minutes', 0),
                        'sourceType': entry.get('source_type', 'manual'),
                        'lastSynced': entry.get('last_synced'),
                        'createdAt': entry.get('created_at'),
                        'updatedAt': entry.get('updated_at')
                    }
                    formatted_entries.append(formatted_entry)
                return formatted_entries
            
            return []
        except Exception as e:
            print(f"❌ Error getting step entries in range: {e}")
            return []

    async def delete_step_entry_by_date(self, user_id: str, entry_date: date) -> bool:
        """Delete step entry for a specific date"""
        try:
            response = self.client.table('daily_steps')\
                .delete()\
                .eq('user_id', user_id)\
                .eq('date', str(entry_date))\
                .execute()
            
            return True
        except Exception as e:
            print(f"❌ Error deleting step entry: {e}")
            return False
        
    async def create_weight_entry(self, weight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new weight entry"""
        try:
            response = self.client.table('weight_entries').insert(weight_data).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error creating weight entry: {e}")
            raise Exception(f"Failed to create weight entry: {str(e)}")

    async def get_weight_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get weight history for a user"""
        try:
            print(f"🔍 Getting {limit} weight entries for user: {user_id}")
            
            response = self.client.table('weight_entries')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('date', desc=True)\
                .limit(limit)\
                .execute()
            
            if response.data:
                # Format the data to ensure consistency
                formatted_entries = []
                for entry in response.data:
                    formatted_entry = {
                        'id': entry['id'],
                        'user_id': entry['user_id'],
                        'date': entry['date'],
                        'weight': float(entry.get('weight', 0.0)),
                        'notes': entry.get('notes'),
                        'body_fat_percentage': float(entry['body_fat_percentage']) if entry.get('body_fat_percentage') else None,
                        'muscle_mass_kg': float(entry['muscle_mass_kg']) if entry.get('muscle_mass_kg') else None,
                        'created_at': entry.get('created_at'),
                        'updated_at': entry.get('updated_at')
                    }
                    formatted_entries.append(formatted_entry)
                
                print(f"✅ Retrieved {len(formatted_entries)} weight entries")
                return formatted_entries
            
            return []
        except Exception as e:
            print(f"❌ Error getting weight history: {e}")
            return []

    async def get_latest_weight(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest weight entry for a user"""
        try:
            response = self.client.table('weight_entries')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('date', desc=True)\
                .limit(1)\
                .execute()
            
            if response.data:
                entry = response.data[0]
                return {
                    'id': entry['id'],
                    'user_id': entry['user_id'],
                    'date': entry['date'],
                    'weight': float(entry.get('weight', 0.0)),
                    'notes': entry.get('notes'),
                    'body_fat_percentage': float(entry['body_fat_percentage']) if entry.get('body_fat_percentage') else None,
                    'muscle_mass_kg': float(entry['muscle_mass_kg']) if entry.get('muscle_mass_kg') else None,
                    'created_at': entry.get('created_at'),
                    'updated_at': entry.get('updated_at')
                }
            return None
        except Exception as e:
            print(f"❌ Error getting latest weight: {e}")
            return None

    async def delete_weight_entry(self, entry_id: str) -> bool:
        """Delete a weight entry"""
        try:
            response = self.client.table('weight_entries')\
                .delete()\
                .eq('id', entry_id)\
                .execute()
            
            return True
        except Exception as e:
            print(f"❌ Error deleting weight entry: {e}")
            return False
        
    async def create_sleep_entry(self, sleep_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new sleep entry"""
        try:
            response = self.client.table('sleep_entries').insert(sleep_data).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error creating sleep entry: {e}")
            raise Exception(f"Failed to create sleep entry: {str(e)}")

    async def update_sleep_entry(self, entry_id: str, sleep_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing sleep entry"""
        try:
            response = self.client.table('sleep_entries').update(sleep_data).eq('id', entry_id).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error updating sleep entry: {e}")
            raise Exception(f"Failed to update sleep entry: {str(e)}")

    async def get_sleep_entry_by_date(self, user_id: str, entry_date: date) -> Optional[Dict[str, Any]]:
        """Get sleep entry for a specific date"""
        try:
            response = self.client.table('sleep_entries')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('date', str(entry_date))\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"❌ Error getting sleep entry by date: {e}")
            return None

    async def get_sleep_history(self, user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get sleep history for a user"""
        try:
            print(f"🔍 Getting {limit} sleep entries for user: {user_id}")
            
            response = self.client.table('sleep_entries')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('date', desc=True)\
                .limit(limit)\
                .execute()
            
            if response.data:
                print(f"✅ Retrieved {len(response.data)} sleep entries")
                return response.data
            
            return []
        except Exception as e:
            print(f"❌ Error getting sleep history: {e}")
            return []

    async def delete_sleep_entry(self, entry_id: str) -> bool:
        """Delete a sleep entry"""
        try:
            response = self.client.table('sleep_entries')\
                .delete()\
                .eq('id', entry_id)\
                .execute()
            
            return True
        except Exception as e:
            print(f"❌ Error deleting sleep entry: {e}")
            return False
        
    async def create_supplement_preference(self, preference_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplement preference"""
        try:
            response = self.client.table('supplement_preferences').insert(preference_data).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error creating supplement preference: {e}")
            raise Exception(f"Failed to create supplement preference: {str(e)}")

    async def get_supplement_preferences(self, user_id: str) -> List[Dict[str, Any]]:
        """Get supplement preferences for a user"""
        try:
            print(f"🔍 Getting supplement preferences for user: {user_id}")
            
            response = self.client.table('supplement_preferences')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .order('created_at', desc=False)\
                .execute()
            
            if response.data:
                print(f"✅ Retrieved {len(response.data)} supplement preferences")
                return response.data
            
            return []
        except Exception as e:
            print(f"❌ Error getting supplement preferences: {e}")
            return []

    async def clear_supplement_preferences(self, user_id: str) -> bool:
        """Clear all supplement preferences for a user (mark as inactive)"""
        try:
            response = self.client.table('supplement_preferences')\
                .update({'is_active': False, 'updated_at': datetime.now().isoformat()})\
                .eq('user_id', user_id)\
                .execute()
            
            return True
        except Exception as e:
            print(f"❌ Error clearing supplement preferences: {e}")
            return False

    async def create_supplement_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplement log entry"""
        try:
            response = self.client.table('supplement_logs').insert(log_data).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error creating supplement log: {e}")
            raise Exception(f"Failed to create supplement log: {str(e)}")

    async def update_supplement_log(self, log_id: str, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplement log entry"""
        try:
            response = self.client.table('supplement_logs').update(log_data).eq('id', log_id).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error updating supplement log: {e}")
            raise Exception(f"Failed to update supplement log: {str(e)}")

    async def get_supplement_log_by_date(self, user_id: str, supplement_name: str, entry_date: date) -> Optional[Dict[str, Any]]:
        """Get supplement log for a specific supplement and date"""
        try:
            response = self.client.table('supplement_logs')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('supplement_name', supplement_name)\
                .eq('date', str(entry_date))\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"❌ Error getting supplement log by date: {e}")
            return None

    async def get_supplement_status_by_date(self, user_id: str, entry_date: date) -> Dict[str, bool]:
        """Get supplement status for all supplements on a specific date"""
        try:
            response = self.client.table('supplement_logs')\
                .select('supplement_name, taken')\
                .eq('user_id', user_id)\
                .eq('date', str(entry_date))\
                .execute()
            
            status = {}
            if response.data:
                for log in response.data:
                    status[log['supplement_name']] = log['taken']
            
            return status
        except Exception as e:
            print(f"❌ Error getting supplement status by date: {e}")
            return {}

    async def get_supplement_history(self, user_id: str, supplement_name: Optional[str] = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get supplement history for a user"""
        try:
            print(f"🔍 Getting supplement history for user: {user_id}")
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            query = self.client.table('supplement_logs')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('date', str(start_date))\
                .lte('date', str(end_date))\
                .order('date', desc=True)
            
            if supplement_name:
                query = query.eq('supplement_name', supplement_name)
            
            response = query.execute()
            
            if response.data:
                print(f"✅ Retrieved {len(response.data)} supplement history records")
                return response.data
            
            return []
        except Exception as e:
            print(f"❌ Error getting supplement history: {e}")
            return []

    async def delete_supplement_preference(self, preference_id: str) -> bool:
        """Delete a supplement preference"""
        try:
            response = self.client.table('supplement_preferences')\
                .update({'is_active': False, 'updated_at': datetime.now().isoformat()})\
                .eq('id', preference_id)\
                .execute()
            
            return True
        except Exception as e:
            print(f"❌ Error deleting supplement preference: {e}")
            return False
    
    # Exercise methods
    async def create_exercise_log(self, exercise_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new exercise log"""
        try:
            response = self.client.table('exercise_logs').insert(exercise_data).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error creating exercise log: {e}")
            raise Exception(f"Failed to create exercise log: {str(e)}")

    async def get_exercise_logs(self, user_id: str, exercise_type: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get exercise logs for a user"""
        try:
            print(f"🔍 Getting exercise logs for user: {user_id}")
            print(f"🔍 Filters - type: {exercise_type}, start: {start_date}, end: {end_date}, limit: {limit}")
            
            query = self.client.table('exercise_logs')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('exercise_date', desc=True)\
                .limit(limit)
            
            # Apply date filters if provided
            if start_date and end_date:
                if start_date == end_date:
                    # ✅ For same day filtering, use date range for the entire day
                    start_datetime = f"{start_date}T00:00:00"
                    end_datetime = f"{end_date}T23:59:59"
                    query = query.gte('exercise_date', start_datetime).lte('exercise_date', end_datetime)
                    print(f"🔍 Same day filter: {start_datetime} to {end_datetime}")
                else:
                    # Different start and end dates
                    query = query.gte('exercise_date', start_date).lte('exercise_date', end_date)
                    print(f"🔍 Date range filter: {start_date} to {end_date}")
            elif start_date:
                query = query.gte('exercise_date', start_date)
                print(f"🔍 Start date filter: >= {start_date}")
            elif end_date:
                query = query.lte('exercise_date', end_date)
                print(f"🔍 End date filter: <= {end_date}")
                
            if exercise_type:
                query = query.eq('exercise_type', exercise_type)
                print(f"🔍 Exercise type filter: {exercise_type}")
            
            response = query.execute()
            
            logs = response.data or []
            print(f"✅ Retrieved {len(logs)} exercise logs")
            
            # Debug the logs
            for i, log in enumerate(logs):
                print(f"🔍 Log {i+1}: {log.get('exercise_name')} - {log.get('duration_minutes')}min on {log.get('exercise_date')}")
            
            return logs
        except Exception as e:
            print(f"❌ Error getting exercise logs: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def delete_exercise_log(self, exercise_id: str) -> bool:
        """Delete an exercise log"""
        try:
            response = self.client.table('exercise_logs')\
                .delete()\
                .eq('id', exercise_id)\
                .execute()
            
            return True
        except Exception as e:
            print(f"❌ Error deleting exercise log: {e}")
            return False

    # Period methods
    async def create_period_entry(self, period_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new period entry"""
        try:
            response = self.client.table('period_entries').insert(period_data).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error creating period entry: {e}")
            raise Exception(f"Failed to create period entry: {str(e)}")

    async def update_period_entry(self, entry_id: str, period_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing period entry"""
        try:
            response = self.client.table('period_entries').update(period_data).eq('id', entry_id).execute()
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from Supabase")
        except Exception as e:
            print(f"❌ Error updating period entry: {e}")
            raise Exception(f"Failed to update period entry: {str(e)}")

    async def get_period_history(self, user_id: str, limit: int = 12) -> List[Dict[str, Any]]:
        """Get period history for a user"""
        try:
            response = self.client.table('period_entries')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('start_date', desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data or []
        except Exception as e:
            print(f"❌ Error getting period history: {e}")
            return []

    async def get_current_period(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current ongoing period (no end date)"""
        try:
            response = self.client.table('period_entries')\
                .select('*')\
                .eq('user_id', user_id)\
                .is_('end_date', 'null')\
                .order('start_date', desc=True)\
                .limit(1)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"❌ Error getting current period: {e}")
            return None

    async def delete_period_entry(self, entry_id: str) -> bool:
        """Delete a period entry"""
        try:
            response = self.client.table('period_entries')\
                .delete()\
                .eq('id', entry_id)\
                .execute()
            
            return True
        except Exception as e:
            print(f"❌ Error deleting period entry: {e}")
            return False
    
    async def save_chat_message(self, user_id: str, message: str, is_user: bool) -> bool:
        """Save a chat message"""
        try:
            # Get or create today's session
            session_id = await self.get_or_create_daily_session(user_id)
            
            message_data = {
                "user_id": user_id,
                "message": message,
                "is_user": is_user,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Add session_id if we have one
            if session_id:
                message_data["session_id"] = session_id
            
            self.client.table("chat_messages").insert(message_data).execute()
            return True
        except Exception as e:
            print(f"Error saving chat message: {e}")
            return False

    async def get_chat_messages(self, user_id: str, limit: int = 50, session_id: str = None) -> List[Dict]:
        """Get chat messages for a user"""
        try:
            query = self.client.table("chat_messages")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=False)\
                .limit(limit)
            
            if session_id:
                query = query.eq("session_id", session_id)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting chat messages: {e}")
            return []

    async def clear_chat_messages(self, user_id: str) -> bool:
        """Clear all chat messages for a user"""
        try:
            self.client.table("chat_messages")\
                .delete()\
                .eq("user_id", user_id)\
                .execute()
            return True
        except Exception as e:
            print(f"Error clearing chat messages: {e}")
            return False

    async def get_recent_chat_context(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent messages for AI context"""
        try:
            result = self.client.table("chat_messages")\
                .select("message, is_user, created_at")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            messages = result.data if result.data else []
            return list(reversed(messages))  # Return in chronological order
        except Exception as e:
            print(f"Error getting recent chat context: {e}")
            return []
    
    async def create_chat_session(self, user_id: str, title: str = None) -> Dict[str, Any]:
        """Create a new chat session"""
        try:
            session_data = {
                "user_id": user_id,
                "title": title or "New Chat",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table("chat_sessions").insert(session_data).execute()
            return response.data[0]
        except Exception as e:
            print(f"Error creating chat session: {e}")
            raise e

    async def get_or_create_daily_session(self, user_id: str) -> str:
        """Get today's session or create a new one"""
        try:
            today = datetime.now().date()
            
            # Look for today's session
            response = self.client.table("chat_sessions")\
                .select("id")\
                .eq("user_id", user_id)\
                .gte("created_at", f"{today}T00:00:00")\
                .lte("created_at", f"{today}T23:59:59")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if response.data:
                return response.data[0]["id"]
            
            # Create new session for today
            session = await self.create_chat_session(user_id, f"Health Chat - {today}")
            return session["id"]
        except Exception as e:
            print(f"Error getting/creating daily session: {e}")
            # Fallback - continue without session_id
            return None

# Global instance - we'll initialize this in main.py
supabase_service = None

def get_supabase_service() -> SupabaseService:
    """Get the global Supabase service instance"""
    global supabase_service
    if supabase_service is None:
        supabase_service = SupabaseService()
    return supabase_service

def init_supabase_service():
    """Initialize the global Supabase service"""
    global supabase_service
    supabase_service = SupabaseService()
    return supabase_service