# services/openai_service.py
import openai
import os
import json
from typing import Dict, Any

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
            
            Be specific about fiber, sugar, and sodium content. If the food naturally has low amounts, use realistic values (not zero).
            
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
            
            Important: Always include realistic values for fiber_g, sugar_g, and sodium_mg - never use null or undefined.
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
            
            # Ensure all required fields exist with proper types
            nutrition_data = {
                "calories": int(nutrition_data.get("calories", 200)),
                "protein_g": float(nutrition_data.get("protein_g", 10.0)),
                "carbs_g": float(nutrition_data.get("carbs_g", 25.0)),
                "fat_g": float(nutrition_data.get("fat_g", 8.0)),
                "fiber_g": float(nutrition_data.get("fiber_g", 2.0)),
                "sugar_g": float(nutrition_data.get("sugar_g", 3.0)),
                "sodium_mg": int(nutrition_data.get("sodium_mg", 200)),
                "serving_description": str(nutrition_data.get("serving_description", f"{quantity} of {food_item}")),
                "nutrition_notes": str(nutrition_data.get("nutrition_notes", "")),
                "healthiness_score": int(nutrition_data.get("healthiness_score", 6)),
                "suggestions": str(nutrition_data.get("suggestions", ""))
            }
            
            print(f"✅ Meal analysis complete: {nutrition_data['calories']} calories")
            print(f"   Fiber: {nutrition_data['fiber_g']}g, Sugar: {nutrition_data['sugar_g']}g, Sodium: {nutrition_data['sodium_mg']}mg")
            
            return nutrition_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"   Raw content: {content}")
            # Return fallback data
            return self._get_fallback_nutrition(food_item, quantity)
        except Exception as e:
            print(f"❌ Error analyzing meal: {e}")
            import traceback
            traceback.print_exc()
            # Return fallback data
            return self._get_fallback_nutrition(food_item, quantity)

    def _get_fallback_nutrition(self, food_item: str, quantity: str) -> Dict[str, Any]:
        """Get fallback nutrition data when AI analysis fails"""
        return {
            "calories": 250,
            "protein_g": 12.0,
            "carbs_g": 30.0,
            "fat_g": 10.0,
            "fiber_g": 3.0,
            "sugar_g": 5.0,
            "sodium_mg": 300,
            "serving_description": f"Estimated for {quantity} of {food_item}",
            "nutrition_notes": "Estimated values due to analysis error",
            "healthiness_score": 6,
            "suggestions": "Consider tracking more detailed portion sizes for better accuracy"
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