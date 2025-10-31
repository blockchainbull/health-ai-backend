# api/notifications_simple.py
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
    """Log a notification when it's shown to user"""
    try:
        supabase = get_supabase_service()
        
        data = {
            'id': str(uuid.uuid4()),
            'user_id': notification.user_id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'is_read': False,
            'created_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.client.table('notifications').insert(data).execute()
        
        return {
            "success": True,
            "notification": response.data[0] if response.data else None
        }
        
    except Exception as e:
        print(f"❌ Error logging notification: {e}")
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
        
        return {
            "success": True,
            "notifications": response.data if response.data else []
        }
        
    except Exception as e:
        print(f"❌ Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """Mark a notification as read"""
    try:
        supabase = get_supabase_service()
        
        response = supabase.client.table('notifications')\
            .update({'is_read': True})\
            .eq('id', notification_id)\
            .execute()
        
        return {
            "success": True,
            "message": "Notification marked as read"
        }
        
    except Exception as e:
        print(f"❌ Error marking as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}/read-all")
async def mark_all_as_read(user_id: str):
    """Mark all notifications as read"""
    try:
        supabase = get_supabase_service()
        
        response = supabase.client.table('notifications')\
            .update({'is_read': True})\
            .eq('user_id', user_id)\
            .eq('is_read', False)\
            .execute()
        
        return {
            "success": True,
            "message": "All notifications marked as read"
        }
        
    except Exception as e:
        print(f"❌ Error marking all as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))