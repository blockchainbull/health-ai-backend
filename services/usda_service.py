# services/usda_service.py
import aiohttp
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

class USDAService:
    def __init__(self):
        self.api_key = os.getenv("USDA_API_KEY", "DEMO_KEY") 
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        print("✅ USDA FoodData Central service initialized")
    
    async def search_food(self, query: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Search for food items in USDA database"""
        try:
            url = f"{self.base_url}/foods/search"
            params = {
                "query": query,
                "limit": limit,
                "api_key": self.api_key,
                "dataType": ["Foundation", "SR Legacy", "Branded"]  # Include all food types
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("foods", [])
                    else:
                        print(f"⚠️ USDA API returned status {response.status}")
                        return None
                        
        except Exception as e:
            print(f"❌ Error searching USDA database: {e}")
            return None
    
    async def get_food_details(self, fdc_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed nutrition info for a specific food"""
        try:
            url = f"{self.base_url}/food/{fdc_id}"
            params = {"api_key": self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
                    
        except Exception as e:
            print(f"❌ Error getting food details: {e}")
            return None
    
    def parse_nutrition_from_usda(self, food_data: Dict[str, Any], quantity: str) -> Dict[str, Any]:
        """Parse USDA data into our nutrition format"""
        try:
            # Extract nutrients
            nutrients = {}
            nutrient_map = {
                "Energy": "calories",
                "Protein": "protein_g",
                "Carbohydrate, by difference": "carbs_g",
                "Total lipid (fat)": "fat_g",
                "Fiber, total dietary": "fiber_g",
                "Sugars, total including NLEA": "sugar_g",
                "Sodium, Na": "sodium_mg"
            }
            
            # Process food nutrients
            for nutrient in food_data.get("foodNutrients", []):
                nutrient_name = nutrient.get("nutrient", {}).get("name", "")
                if nutrient_name in nutrient_map:
                    value = nutrient.get("amount", 0)
                    
                    # Convert units if needed
                    unit = nutrient.get("nutrient", {}).get("unitName", "")
                    if nutrient_name == "Energy" and unit == "kcal":
                        nutrients["calories"] = int(value)
                    elif nutrient_name == "Sodium, Na" and unit == "mg":
                        nutrients["sodium_mg"] = int(value)
                    elif unit == "g":
                        nutrients[nutrient_map[nutrient_name]] = float(value)
            
            # Calculate serving size multiplier based on quantity
            serving_multiplier = self._calculate_serving_multiplier(quantity, food_data)
            
            # Apply multiplier to all nutrients
            for key in nutrients:
                if key == "calories" or key == "sodium_mg":
                    nutrients[key] = int(nutrients[key] * serving_multiplier)
                else:
                    nutrients[key] = round(nutrients[key] * serving_multiplier, 1)
            
            # Ensure all required fields exist
            nutrition_data = {
                "calories": nutrients.get("calories", 0),
                "protein_g": nutrients.get("protein_g", 0.0),
                "carbs_g": nutrients.get("carbs_g", 0.0),
                "fat_g": nutrients.get("fat_g", 0.0),
                "fiber_g": nutrients.get("fiber_g", 0.0),
                "sugar_g": nutrients.get("sugar_g", 0.0),
                "sodium_mg": nutrients.get("sodium_mg", 0),
                "serving_description": quantity,
                "data_source": "USDA",
                "fdc_id": food_data.get("fdcId"),
                "food_description": food_data.get("description", ""),
                "confidence_score": 0.95  # High confidence for USDA data
            }
            
            return nutrition_data
            
        except Exception as e:
            print(f"❌ Error parsing USDA nutrition data: {e}")
            return None
    
    def _calculate_serving_multiplier(self, quantity: str, food_data: Dict) -> float:
        """Calculate how much to multiply base nutrition by"""
        try:
            quantity_lower = quantity.lower()
            
            # Common quantity patterns
            if "cup" in quantity_lower:
                cups = self._extract_number(quantity_lower, default=1.0)
                return cups * 240 / 100  # 1 cup ≈ 240g, USDA base is per 100g
            elif "tbsp" in quantity_lower or "tablespoon" in quantity_lower:
                tbsp = self._extract_number(quantity_lower, default=1.0)
                return tbsp * 15 / 100  # 1 tbsp ≈ 15g
            elif "tsp" in quantity_lower or "teaspoon" in quantity_lower:
                tsp = self._extract_number(quantity_lower, default=1.0)
                return tsp * 5 / 100  # 1 tsp ≈ 5g
            elif "oz" in quantity_lower or "ounce" in quantity_lower:
                oz = self._extract_number(quantity_lower, default=1.0)
                return oz * 28.35 / 100  # 1 oz ≈ 28.35g
            elif "g" in quantity_lower or "gram" in quantity_lower:
                grams = self._extract_number(quantity_lower, default=100.0)
                return grams / 100
            elif any(size in quantity_lower for size in ["small", "medium", "large"]):
                # Estimate based on typical serving sizes
                if "small" in quantity_lower:
                    return 0.75
                elif "large" in quantity_lower:
                    return 1.5
                else:  # medium
                    return 1.0
            else:
                # Try to extract a number (e.g., "2 apples")
                number = self._extract_number(quantity_lower, default=1.0)
                return number
                
        except Exception:
            return 1.0  # Default to 1 serving if parsing fails
    
    def _extract_number(self, text: str, default: float = 1.0) -> float:
        """Extract numeric value from text"""
        import re
        
        # Handle fractions
        fraction_map = {
            "1/4": 0.25, "1/3": 0.33, "1/2": 0.5, 
            "2/3": 0.67, "3/4": 0.75
        }
        
        for fraction, value in fraction_map.items():
            if fraction in text:
                return value
        
        # Extract decimal/integer
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            return float(numbers[0])
        
        return default

# Singleton instance
_usda_service = None

def get_usda_service():
    global _usda_service
    if _usda_service is None:
        _usda_service = USDAService()
    return _usda_service

def init_usda_service():
    """Initialize USDA service on startup"""
    global _usda_service
    _usda_service = USDAService()
    return _usda_service