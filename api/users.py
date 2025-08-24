# api/users.py
from fastapi import APIRouter, HTTPException
import uuid
from datetime import datetime
import bcrypt
from models.schemas import UserUpdate

from models.schemas import UserCreate, UserResponse, UserLogin, UserLoginResponse
from services.supabase_service import get_supabase_service 

router = APIRouter()

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

@router.post("/register", response_model=UserLoginResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        print(f"🔍 Registering user: {user_data.email}")
        
        # Get the service instance
        supabase_service = get_supabase_service()
        
        # Check if user already exists
        existing_user = await supabase_service.get_user_by_email(user_data.email)
        if existing_user:
            return UserLoginResponse(
                success=False,
                error="User with this email already exists"
            )
        
        # Hash the password
        hashed_password = hash_password(user_data.password)
        
        # Prepare user data for database
        user_dict = user_data.dict()
        user_dict['id'] = str(uuid.uuid4())
        user_dict['password_hash'] = hashed_password
        user_dict['created_at'] = datetime.utcnow().isoformat()
        user_dict['updated_at'] = datetime.utcnow().isoformat()
        
        # Remove plain password - we only store the hash
        del user_dict['password']
        
        # Handle None values for required fields
        if user_dict.get('sleep_issues') is None:
            user_dict['sleep_issues'] = []
        if user_dict.get('dietary_preferences') is None:
            user_dict['dietary_preferences'] = []
        if user_dict.get('medical_conditions') is None:
            user_dict['medical_conditions'] = []
        if user_dict.get('preferred_workouts') is None:
            user_dict['preferred_workouts'] = []
        if user_dict.get('available_equipment') is None:
            user_dict['available_equipment'] = []
        if user_dict.get('preferences') is None:
            user_dict['preferences'] = {}
        
        print(f"🔍 User data to insert: {user_dict}")
        
        # Create user in Supabase
        created_user = await supabase_service.create_user(user_dict)
        
        if not created_user:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # Return user response
        user_response = UserResponse(
            id=created_user['id'],
            name=created_user['name'],
            email=created_user['email'],
            gender=created_user.get('gender'),
            age=created_user.get('age'),
            height=created_user.get('height'),
            weight=created_user.get('weight'),
            activity_level=created_user.get('activity_level'),
            bmi=created_user.get('bmi'),
            bmr=created_user.get('bmr'),
            tdee=created_user.get('tdee'),
            primary_goal=created_user.get('primary_goal'),
            created_at=created_user.get('created_at'),
            updated_at=created_user.get('updated_at')
        )
        
        return UserLoginResponse(
            success=True,
            user=user_response,
            message="User registered successfully"
        )
        
    except Exception as e:
        print(f"❌ Error registering user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=UserLoginResponse)
async def login_user(login_data: UserLogin):
    """Login user"""
    try:
        print(f"🔍 Login attempt for: {login_data.email}")
        
        # Get the service instance
        supabase_service = get_supabase_service() 
        
        # Get user by email
        user = await supabase_service.get_user_by_email(login_data.email)
        if not user:
            return UserLoginResponse(
                success=False,
                error="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user['password_hash']):
            return UserLoginResponse(
                success=False,
                error="Invalid email or password"
            )
        
        # Return user response
        user_response = UserResponse(
            id=user['id'],
            name=user['name'],
            email=user['email'],
            gender=user.get('gender'),
            age=user.get('age'),
            height=user.get('height'),
            weight=user.get('weight'),
            activity_level=user.get('activity_level'),
            bmi=user.get('bmi'),
            bmr=user.get('bmr'),
            tdee=user.get('tdee'),
            primary_goal=user.get('primary_goal'),
            created_at=user.get('created_at'),
            updated_at=user.get('updated_at')
        )
        
        return UserLoginResponse(
            success=True,
            user=user_response,
            message="Login successful"
        )
        
    except Exception as e:
        print(f"❌ Error during login: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID"""
    try:
        supabase_service = get_supabase_service()  
        user = await supabase_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            id=user['id'],
            name=user['name'],
            email=user['email'],
            gender=user.get('gender'),
            age=user.get('age'),
            height=user.get('height'),
            weight=user.get('weight'),
            activity_level=user.get('activity_level'),
            bmi=user.get('bmi'),
            bmr=user.get('bmr'),
            tdee=user.get('tdee'),
            primary_goal=user.get('primary_goal'),
            created_at=user.get('created_at'),
            updated_at=user.get('updated_at')
        )
        
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/update-user/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate):
    try:
        supabase_service = get_supabase_service()
        
        # Convert to dict and remove None values
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}
        
        updated_user = await supabase_service.update_user(user_id, update_data)
        
        return {"success": True, "user": updated_user}
        
    except Exception as e:
        print(f"❌ Error updating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def health_check():
    """Health check for users API"""
    return {"status": "Users API is healthy", "timestamp": datetime.utcnow()}