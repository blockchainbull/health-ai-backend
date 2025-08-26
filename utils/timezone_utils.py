# api/utils/timezone_utils.py
from datetime import datetime, date, timedelta
from typing import Optional, Union, Dict, Any
from fastapi import Header

def parse_timezone_offset(offset_str: Optional[str]) -> int:
    """
    Parse timezone offset from various formats.
    Examples: "300" (minutes), "+05:00", "-08:00"
    """
    if not offset_str:
        return 0
    
    try:
        # If it's already in minutes
        if offset_str.lstrip('-').isdigit():
            return int(offset_str)
        
        # If it's in format "+05:00" or "-08:00"
        if ':' in offset_str:
            sign = -1 if offset_str.startswith('-') else 1
            parts = offset_str.lstrip('+-').split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return sign * (hours * 60 + minutes)
    except:
        pass
    
    return 0

def get_user_date(
    date_input: Optional[Union[str, Dict[str, Any]]] = None,
    timezone_offset: int = 0
) -> date:
    """
    Get a date in the user's timezone.
    
    Args:
        date_input: Can be:
            - None: returns today in user's timezone
            - String: "YYYY-MM-DD" or ISO datetime string
            - Dict: {"date": "YYYY-MM-DD", "timezone_offset": 300}
        timezone_offset: Timezone offset in minutes from UTC
    """
    if date_input is None:
        # Get current time in user's timezone
        utc_now = datetime.utcnow()
        user_now = utc_now + timedelta(minutes=timezone_offset)
        return user_now.date()
    
    if isinstance(date_input, dict):
        # Extract date and optional timezone offset
        date_str = date_input.get('date', '')
        tz_offset = date_input.get('timezone_offset', timezone_offset)
        
        if date_str:
            # If it's just a date (YYYY-MM-DD), use it directly
            if 'T' not in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # If it's a datetime, parse and apply timezone
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if tz_offset:
                dt = dt + timedelta(minutes=tz_offset)
            return dt.date()
    
    if isinstance(date_input, str):
        # Simple date string (YYYY-MM-DD)
        if 'T' not in date_input:
            return datetime.strptime(date_input, '%Y-%m-%d').date()
        
        # ISO datetime string
        dt = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
        if timezone_offset:
            dt = dt + timedelta(minutes=timezone_offset)
        return dt.date()
    
    # Fallback to UTC today
    return datetime.utcnow().date()

def get_user_now(timezone_offset: int = 0) -> datetime:
    """Get current datetime in user's timezone."""
    utc_now = datetime.utcnow()
    return utc_now + timedelta(minutes=timezone_offset)

def get_user_today(timezone_offset: int = 0) -> date:
    """Get today's date in user's timezone."""
    return get_user_now(timezone_offset).date()

# FastAPI dependency to extract timezone from headers
async def get_timezone_offset(
    x_timezone_offset: Optional[str] = Header(None),
    x_timezone_string: Optional[str] = Header(None)
) -> int:
    """
    Extract timezone offset from request headers.
    Returns offset in minutes from UTC.
    """
    # Try the direct offset first
    if x_timezone_offset:
        return parse_timezone_offset(x_timezone_offset)
    
    # Try parsing the string format
    if x_timezone_string:
        return parse_timezone_offset(x_timezone_string)
    
    # Default to UTC
    return 0