# services/supabase_service.py
from supabase import create_client, Client
import os
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
import json

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
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user data"""
        try:
            print(f"🔍 Updating user: {user_id}")
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            response = self.client.table('users').update(update_data).eq('id', user_id).execute()
            
            if response.data:
                print(f"✅ User updated successfully: {user_id}")
                return response.data[0]
            else:
                print(f"❌ User update failed: {user_id}")
                return None
                
        except Exception as e:
            print(f"❌ Error updating user: {e}")
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