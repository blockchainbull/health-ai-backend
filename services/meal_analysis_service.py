# services/meal_analysis_service.py
from typing import Dict, Any, Optional
import re
from services.usda_service import get_usda_service
from services.openai_service import get_openai_service

class MealAnalysisService:
    def __init__(self):
        self.usda_service = get_usda_service()
        self.openai_service = get_openai_service()
        print("✅ Meal Analysis Service initialized with USDA + ChatGPT fallback")
    
    async def analyze_meal(
        self, 
        food_item: str, 
        quantity: str, 
        user_context: Dict[str, Any],
        preparation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze meal with intelligent routing:
        1. Try USDA first for simple/common foods
        2. Use ChatGPT for complex dishes, recipes, or when USDA fails
        """
        
        print(f"🔍 Analyzing: {food_item} ({quantity})")
        
        # Determine if this is a simple or complex food item
        is_complex = self._is_complex_food(food_item, preparation)
        
        if not is_complex:
            # Try USDA first for simple foods
            usda_result = await self._try_usda_analysis(food_item, quantity)
            if usda_result:
                print(f"✅ Using USDA data for {food_item}")
                # Add health analysis from ChatGPT
                usda_result = await self._add_health_insights(
                    usda_result, food_item, user_context
                )
                return usda_result
        
        # Use ChatGPT for complex foods or when USDA fails
        print(f"🤖 Using ChatGPT for {food_item} (complex: {is_complex})")
        return await self._chatgpt_analysis(food_item, quantity, user_context, preparation)
    
    def _is_complex_food(self, food_item: str, preparation: Optional[str]) -> bool:
        """Determine if food requires ChatGPT analysis"""
        
        # Indicators of complex/prepared foods
        complex_indicators = [
            # Cooking methods
            "fried", "grilled", "baked", "roasted", "sauteed", "steamed",
            "boiled", "braised", "stir-fried", "deep-fried",
            
            # Restaurant/brand foods
            "mcdonald", "burger king", "starbucks", "subway", "chipotle",
            
            # Complex dishes
            "sandwich", "burger", "pizza", "pasta", "salad", "soup",
            "curry", "stir fry", "casserole", "burrito", "taco",
            
            # Multi-ingredient indicators
            "with", "and", "&", "+", "combo", "meal", "plate",
            
            # Homemade/recipe indicators
            "homemade", "recipe", "my", "grandma", "special"
        ]
        
        food_lower = food_item.lower()
        prep_lower = (preparation or "").lower()
        combined = f"{food_lower} {prep_lower}"
        
        # Check for complex indicators
        if any(indicator in combined for indicator in complex_indicators):
            return True
        
        # Check if multiple ingredients (has commas or "and")
        if "," in food_item or " and " in food_item:
            return True
        
        # Simple single-ingredient foods
        simple_foods = [
            "apple", "banana", "orange", "milk", "egg", "bread",
            "rice", "chicken breast", "salmon", "beef", "pork"
        ]
        
        # If it's a simple food without preparation, use USDA
        if any(simple in food_lower for simple in simple_foods) and not preparation:
            return False
        
        return False  # Default to trying USDA first
    
    async def _try_usda_analysis(self, food_item: str, quantity: str) -> Optional[Dict[str, Any]]:
        """Try to get nutrition from USDA database"""
        try:
            # Search USDA database
            search_results = await self.usda_service.search_food(food_item, limit=3)
            
            if not search_results:
                return None
            
            # Find best match
            best_match = self._find_best_match(food_item, search_results)
            
            if not best_match:
                return None
            
            # Get detailed nutrition
            fdc_id = best_match.get("fdcId")
            if not fdc_id:
                return None
            
            food_details = await self.usda_service.get_food_details(fdc_id)
            
            if not food_details:
                return None
            
            # Parse nutrition data
            nutrition = self.usda_service.parse_nutrition_from_usda(food_details, quantity)
            
            if nutrition and nutrition.get("calories", 0) > 0:
                return nutrition
            
            return None
            
        except Exception as e:
            print(f"⚠️ USDA analysis failed: {e}")
            return None
    
    def _find_best_match(self, query: str, results: list) -> Optional[Dict]:
        """Find the best matching food from USDA results"""
        if not results:
            return None
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        best_match = None
        best_score = 0
        
        for result in results:
            description = result.get("description", "").lower()
            brand = result.get("brandName", "").lower()
            
            # Calculate match score
            score = 0
            desc_words = set(description.split())
            
            # Word overlap score
            overlap = len(query_words.intersection(desc_words))
            score += overlap * 10
            
            # Exact match bonus
            if query_lower in description:
                score += 50
            
            # Prefer foundation/legacy foods over branded
            data_type = result.get("dataType", "")
            if data_type in ["Foundation", "SR Legacy"]:
                score += 20
            
            # Penalize if has brand name (unless query includes it)
            if brand and brand not in query_lower:
                score -= 10
            
            if score > best_score:
                best_score = score
                best_match = result
        
        # Only return if we have a reasonable match
        if best_score >= 10:
            return best_match
        
        return None
    
    async def _add_health_insights(
        self, 
        nutrition_data: Dict[str, Any], 
        food_item: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add health insights to USDA data using ChatGPT"""
        try:
            prompt = f"""
            Based on this nutrition data for {food_item}:
            - Calories: {nutrition_data['calories']}
            - Protein: {nutrition_data['protein_g']}g
            - Carbs: {nutrition_data['carbs_g']}g
            - Fat: {nutrition_data['fat_g']}g
            - Fiber: {nutrition_data['fiber_g']}g
            - Sugar: {nutrition_data['sugar_g']}g
            - Sodium: {nutrition_data['sodium_mg']}mg
            
            User context:
            - Goal: {user_context.get('primary_goal', 'maintain weight')}
            - TDEE: {user_context.get('tdee', 2000)} calories
            
            Provide ONLY a JSON response with:
            {{
                "healthiness_score": (1-10),
                "nutrition_notes": "Brief nutrition insight",
                "suggestions": "Brief suggestion for user's goal"
            }}
            """
            
            response = await self.openai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith('```'):
                content = content.split('```')[1].replace('json', '').strip()
            
            import json
            insights = json.loads(content)
            
            # Add insights to nutrition data
            nutrition_data.update({
                "healthiness_score": insights.get("healthiness_score", 7),
                "nutrition_notes": insights.get("nutrition_notes", ""),
                "suggestions": insights.get("suggestions", "")
            })
            
        except Exception as e:
            print(f"⚠️ Could not add health insights: {e}")
            # Add default insights
            nutrition_data.update({
                "healthiness_score": 7,
                "nutrition_notes": "Nutrition data from USDA database",
                "suggestions": "Track portion sizes for better results"
            })
        
        return nutrition_data
    
    async def _chatgpt_analysis(
        self, 
        food_item: str, 
        quantity: str,
        user_context: Dict[str, Any],
        preparation: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fallback to ChatGPT for complex analysis"""
        
        # Use existing OpenAI service method
        result = await self.openai_service.analyze_meal(
            food_item=food_item,
            quantity=quantity,
            user_context=user_context
        )
        
        # Mark as ChatGPT source
        result["data_source"] = "ChatGPT"
        result["confidence_score"] = 0.85  # Slightly lower confidence than USDA
        
        if preparation:
            result["preparation_method"] = preparation
        
        return result

# Singleton instance
_meal_analysis_service = None

def get_meal_analysis_service():
    global _meal_analysis_service
    if _meal_analysis_service is None:
        _meal_analysis_service = MealAnalysisService()
    return _meal_analysis_service

def init_meal_analysis_service():
    """Initialize meal analysis service on startup"""
    global _meal_analysis_service
    _meal_analysis_service = MealAnalysisService()
    return _meal_analysis_service