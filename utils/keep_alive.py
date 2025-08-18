# utils/keep_alive.py
import asyncio
import aiohttp
import os
from datetime import datetime

async def ping_self():
    """Ping the service every 10 minutes to keep it awake"""
    url = os.getenv("RENDER_EXTERNAL_URL", "https://health-ai-backend-i28b.onrender.com")
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health") as response:
                    if response.status == 200:
                        print(f"✅ Keep-alive ping successful at {datetime.now()}")
                    else:
                        print(f"⚠️ Keep-alive ping failed: {response.status}")
        except Exception as e:
            print(f"❌ Keep-alive ping error: {e}")
        
        # Wait 10 minutes (600 seconds)
        await asyncio.sleep(600)

def start_keep_alive():
    """Start the keep-alive task"""
    asyncio.create_task(ping_self())