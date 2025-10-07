# services/background_tasks.py

from datetime import datetime, timedelta
import asyncio
from services.weekly_context_manager import get_weekly_context_manager
from services.supabase_service import get_supabase_service

async def generate_weekly_contexts_for_all_users():
    """Background task to generate weekly contexts for all active users"""
    try:
        supabase = get_supabase_service()
        manager = get_weekly_context_manager()
        
        # Get all users who have logged data in the past week
        one_week_ago = (datetime.now().date() - timedelta(days=7)).isoformat()
        
        # Get unique user IDs from recent activities
        response = supabase.client.table('meal_entries')\
            .select('user_id')\
            .gte('created_at', one_week_ago)\
            .execute()
        
        user_ids = set(entry['user_id'] for entry in response.data)
        
        print(f"🔄 Generating weekly contexts for {len(user_ids)} active users")
        
        for user_id in user_ids:
            try:
                # Generate context for the previous week (completed week)
                last_week = datetime.now().date() - timedelta(days=7)
                await manager.update_weekly_context(user_id, last_week)
                print(f"✅ Generated weekly context for user {user_id}")
            except Exception as e:
                print(f"❌ Error generating context for user {user_id}: {e}")
        
        print(f"✅ Weekly context generation complete")
        
    except Exception as e:
        print(f"❌ Error in weekly context generation task: {e}")

# Schedule this to run every Sunday night
async def schedule_weekly_tasks():
    """Run weekly tasks every Sunday at midnight"""
    while True:
        now = datetime.now()
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0 and now.hour >= 23:
            # It's Sunday night, run the task
            await generate_weekly_contexts_for_all_users()
            # Wait until Monday to avoid running again
            await asyncio.sleep(3600 * 25)  # Sleep for 25 hours
        else:
            # Check every hour
            await asyncio.sleep(3600)