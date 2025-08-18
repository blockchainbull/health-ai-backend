# services/openai_service.py
import openai
import os
import json
from typing import Dict, Any, List
import asyncio

class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        
        self.client = openai.AsyncOpenAI(api_key=api_key)
        print("✅ OpenAI service initialized")
    
    async def analyze_meal(self, food_item: str, quantity: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze meal nutrition using GPT"""
        try:
            print(f"🔍 Analyzing meal: {food_item} ({quantity})")
            
            prompt = f"""
            Analyze this meal and provide detailed nutrition information:
            
            Food: {food_item}
            Quantity: {quantity}
            
            User context:
            - Weight: {user_context.get('weight', 70)} kg
            - Goal: {user_context.get('primary_goal', 'maintain weight')}
            - Activity: {user_context.get('activity_level', 'moderate')}
            - TDEE: {user_context.get('tdee', 2000)} calories
            
            Return ONLY valid JSON with these exact fields:
            {{
                "calories": integer,
                "protein_g": float,
                "carbs_g": float,
                "fat_g": float,
                "fiber_g": float,
                "sugar_g": float,
                "sodium_mg": integer,
                "serving_description": "string",
                "nutrition_notes": "string",
                "healthiness_score": integer (1-10),
                "suggestions": "string"
            }}
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean JSON if needed
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            nutrition_data = json.loads(content)
            print(f"✅ Meal analysis complete: {nutrition_data['calories']} calories")
            return nutrition_data
            
        except Exception as e:
            print(f"❌ Error analyzing meal: {e}")
            # Return fallback data
            return {
                "calories": 200,
                "protein_g": 10.0,
                "carbs_g": 25.0,
                "fat_g": 8.0,
                "fiber_g": 3.0,
                "sugar_g": 5.0,
                "sodium_mg": 300,
                "serving_description": f"Estimated for {quantity} of {food_item}",
                "nutrition_notes": "Estimated values due to analysis error",
                "healthiness_score": 6,
                "suggestions": "Consider tracking more detailed portion sizes"
            }
    
    async def health_chat(self, message: str, user_context: Dict[str, Any]) -> str:
        """Health coaching chat"""
        try:
            print(f"🔍 Health chat message received")
            
            system_prompt = f"""
            You are a friendly AI health and nutrition coach. User context:
            - Name: {user_context.get('name', 'there')}
            - Goal: {user_context.get('primary_goal', 'general health')}
            - Weight: {user_context.get('weight', 'not specified')} kg
            - Activity: {user_context.get('activity_level', 'moderate')}
            
            Provide personalized, encouraging advice. Keep responses conversational and supportive.
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            reply = response.choices[0].message.content.strip()
            print(f"✅ Chat response generated")
            return reply
            
        except Exception as e:
            print(f"❌ Error in chat: {e}")
            return "I'm sorry, I'm having trouble responding right now. Please try again later."

# Global instance
openai_service = None

def get_openai_service() -> OpenAIService:
    """Get the global OpenAI service instance"""
    global openai_service
    if openai_service is None:
        openai_service = OpenAIService()
    return openai_service

def init_openai_service():
    """Initialize the global OpenAI service"""
    global openai_service
    openai_service = OpenAIService()
    return openai_service