# main.py
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Response
from utils.keep_alive import start_keep_alive
from api import users, meals, flutter_compat
from services.supabase_service import init_supabase_service

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Health AI Backend",
    description="AI-powered health tracking backend with user management",
    version="2.0.0"
)

# Add CORS middleware for your Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",                                # Local development
        "http://localhost:*",                                   # Any local port
        "https://*.vercel.app",                                 # All Vercel subdomains
        "https://vercel.app",                                   # Vercel domain
        "https://*.onrender.com",                               # Render domains
        "https://fitness-flutter-app.vercel.app/",              # Your specific Vercel URL
        "https://health-ai-backend-i28b.onrender.com"
        "*"                                                     # Allow all origins (for testing)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services when the app starts"""
    print("🚀 Starting Health AI Backend...")
    
    try:
        # Initialize Supabase
        init_supabase_service()
        print("✅ Supabase service initialized")
        
        # Initialize OpenAI
        from services.openai_service import init_openai_service
        init_openai_service()
        print("✅ OpenAI service initialized")
        
        # Start keep-alive (only in production)
        if os.getenv("RENDER_EXTERNAL_URL"):
            start_keep_alive()
            print("✅ Keep-alive service started")
        
        print("🎉 Backend startup complete!")
        
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        raise

# Include API routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(meals.router, prefix="/api/meals", tags=["meals"]) 
app.include_router(flutter_compat.router, prefix="/api/health", tags=["flutter-health"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Health AI Backend API",
        "version": "2.0.0",
        "status": "running",
        "features": ["user_management", "ai_meal_analysis", "health_chat"]
    }

@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    """Handle CORS preflight requests"""
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    from services.supabase_service import get_supabase_service
    from services.openai_service import get_openai_service
    
    try:
        supabase_service = get_supabase_service()
        supabase_health = await supabase_service.health_check()
        
        # Test OpenAI connection
        openai_service = get_openai_service()
        openai_health = {
            "status": "healthy",
            "message": "OpenAI service is initialized"
        }

        return {
            "status": "healthy",
            "services": {
                "api": "healthy",
                "supabase": supabase_health,
                "openai": openai_health
            },
            "message": "All services are running"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Some services are down"
        }
    
@app.post("/test/ai")
async def test_openai(test_data: dict):
    """Quick test of OpenAI service"""
    try:
        from services.openai_service import get_openai_service
        
        openai_service = get_openai_service()
        
        # Test meal analysis
        if test_data.get("type") == "meal":
            result = await openai_service.analyze_meal(
                food_item=test_data.get("food", "apple"),
                quantity=test_data.get("quantity", "1 medium"),
                user_context={"weight": 70, "primary_goal": "maintain", "activity_level": "moderate", "tdee": 2000}
            )
            return {"success": True, "result": result}
        
        # Test chat
        elif test_data.get("type") == "chat":
            result = await openai_service.health_chat(
                message=test_data.get("message", "Hello!"),
                user_context={"name": "Test User", "primary_goal": "lose weight", "weight": 70}
            )
            return {"success": True, "result": result}
        
        else:
            return {"error": "Specify type: 'meal' or 'chat'"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)