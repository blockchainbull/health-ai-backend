# api/notifications.py - UPDATED VERSION

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from services.supabase_service import get_supabase_service
import uuid

router = APIRouter(prefix="/notifications", tags=["notifications"])

class LogNotificationRequest(BaseModel):
    user_id: str
    title: str
    message: str
    type: str

@router.post("/log")
async def log_notification(notification: LogNotificationRequest):
    """Log a notification when it's scheduled"""
    try:
        supabase = get_supabase_service()
        
        notification_id = str(uuid.uuid4())
        data = {
            'id': notification_id,
            'user_id': notification.user_id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'is_read': False,
            'created_at': datetime.utcnow().isoformat()
        }
        
        print(f"📝 Logging notification to DB: {notification.type} for user {notification.user_id}")
        
        response = supabase.client.table('notifications').insert(data).execute()
        
        print(f"✅ Notification logged with ID: {notification_id}")
        
        return {
            "success": True,
            "notification": response.data[0] if response.data else None
        }
        
    except Exception as e:
        print(f"❌ Error logging notification: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count/{user_id}")
async def get_unread_count(user_id: str):
    """Get count of unread notifications"""
    try:
        supabase = get_supabase_service()
        
        response = supabase.client.table('notifications')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .eq('is_read', False)\
            .execute()
        
        count = response.count if hasattr(response, 'count') else 0
        
        print(f"📊 Unread count for {user_id}: {count}")
        
        return {
            "success": True,
            "count": count
        }
        
    except Exception as e:
        print(f"❌ Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}")
async def get_notifications(user_id: str, limit: int = 50):
    """Get all notifications for a user"""
    try:
        supabase = get_supabase_service()
        
        response = supabase.client.table('notifications')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        notifications_count = len(response.data) if response.data else 0
        print(f"📱 Retrieved {notifications_count} notifications for {user_id}")
        
        return {
            "success": True,
            "notifications": response.data if response.data else []
        }
        
    except Exception as e:
        print(f"❌ Error getting notifications: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """Mark a single notification as read"""
    try:
        supabase = get_supabase_service()
        
        response = supabase.client.table('notifications')\
            .update({'is_read': True, 'read_at': datetime.utcnow().isoformat()})\
            .eq('id', notification_id)\
            .execute()
        
        print(f"✅ Notification {notification_id} marked as read")
        
        return {
            "success": True,
            "notification": response.data[0] if response.data else None
        }
        
    except Exception as e:
        print(f"❌ Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}/read-all")
async def mark_all_as_read(user_id: str):
    """Mark all notifications as read for a user"""
    try:
        supabase = get_supabase_service()
        
        response = supabase.client.table('notifications')\
            .update({'is_read': True, 'read_at': datetime.utcnow().isoformat()})\
            .eq('user_id', user_id)\
            .eq('is_read', False)\
            .execute()
        
        updated_count = len(response.data) if response.data else 0
        print(f"✅ Marked {updated_count} notifications as read for {user_id}")
        
        return {
            "success": True,
            "updated_count": updated_count
        }
        
    except Exception as e:
        print(f"❌ Error marking all as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{notification_id}")
async def delete_notification(notification_id: str):
    """Delete a notification"""
    try:
        supabase = get_supabase_service()
        
        response = supabase.client.table('notifications')\
            .delete()\
            .eq('id', notification_id)\
            .execute()
        
        print(f"🗑️ Notification {notification_id} deleted")
        
        return {
            "success": True,
            "message": "Notification deleted successfully"
        }
        
    except Exception as e:
        print(f"❌ Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/clear-all")
async def clear_all_notifications(user_id: str):
    """Delete all notifications for a user"""
    try:
        supabase = get_supabase_service()
        
        response = supabase.client.table('notifications')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
        
        deleted_count = len(response.data) if response.data else 0
        print(f"🗑️ Cleared {deleted_count} notifications for {user_id}")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} notifications"
        }
        
    except Exception as e:
        print(f"❌ Error clearing notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))