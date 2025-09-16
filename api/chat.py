from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from services.supabase_service import get_supabase_service
from services.chat_context_manager import get_context_manager

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/context/{user_id}")
async def get_user_chat_context(user_id: str, date: Optional[str] = None):
    """Get user context - now using cached system"""
    try:
        context_manager = get_context_manager()
        
        target_date = datetime.strptime(date, '%Y-%m-%d').date() if date else datetime.now().date()
        result = await context_manager.get_or_create_context(user_id, target_date)
        
        # Format to match old structure for compatibility
        return {
            'success': True,
            **result['context']  # Unwrap the context directly
        }
        
    except Exception as e:
        print(f"Error getting context: {e}")
        # Fallback - generate fresh if cache fails
        context_manager = get_context_manager()
        result = await context_manager.generate_fresh_context(user_id, datetime.now().date())
        return {
            'success': True,
            **result['context']
        }
    
@router.delete("/context/cleanup")
async def cleanup_old_contexts(days_to_keep: int = 7):
    """Clean up contexts older than specified days"""
    try:
        supabase_service = get_supabase_service()
        cutoff_date = (datetime.now().date() - timedelta(days=days_to_keep)).isoformat()
        
        response = supabase_service.client.table('chat_contexts')\
            .delete()\
            .lt('date', cutoff_date)\
            .execute()
        
        return {
            'success': True,
            'message': f'Cleaned up contexts older than {cutoff_date}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    
@router.get("/context/cached/{user_id}")
async def get_cached_context(user_id: str, date: Optional[str] = None):
    """Get cached context for user - much faster than rebuilding"""
    try:
        context_manager = get_context_manager()
        
        target_date = datetime.strptime(date, '%Y-%m-%d').date() if date else datetime.now().date()
        result = await context_manager.get_or_create_context(user_id, target_date)
        
        return {
            'success': True,
            **result,
            'is_cached': True
        }
        
    except Exception as e:
        print(f"Error getting cached context: {e}")
        # Fallback to generating fresh
        return await get_user_chat_context(user_id)

@router.post("/context/update/{user_id}")
async def update_context_activity(
    user_id: str, 
    activity_type: str,
    data: dict
):
    """Update context when an activity is logged"""
    try:
        context_manager = get_context_manager()
        result = await context_manager.update_context_activity(
            user_id, 
            activity_type, 
            data
        )
        
        return {
            'success': True,
            'message': f'Context updated for {activity_type}',
            'version': result['version']
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    
@router.post("/context/rebuild/{user_id}")
async def rebuild_context(user_id: str, date: Optional[str] = None):
    """Force rebuild context from source tables"""
    try:
        context_manager = get_context_manager()
        
        target_date = datetime.strptime(date, '%Y-%m-%d').date() if date else datetime.now().date()
        result = await context_manager.rebuild_context(user_id, target_date)
        
        return {
            'success': True,
            'message': 'Context rebuilt successfully',
            **result
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }