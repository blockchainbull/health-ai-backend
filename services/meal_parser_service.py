# services/meal_parser_service.py
import re
from typing import List, Dict, Any, Tuple
from services.meal_analysis_service import get_meal_analysis_service

class MealParserService:
    """Intelligently parse and analyze multi-food meal entries"""
    
    def __init__(self):
        self.meal_service = get_meal_analysis_service()
        
        # Common separators that indicate multiple foods
        self.separators = [
            ' and ', ' with ', ' plus ', ' & ', ', ',
            ' alongside ', ' accompanied by ', ' served with '
        ]
        
        # Quantity indicators
        self.quantity_words = [
            'cup', 'cups', 'tbsp', 'tsp', 'oz', 'ounce', 'gram', 'g',
            'piece', 'pieces', 'slice', 'slices', 'serving', 'plate',
            'bowl', 'small', 'medium', 'large', 'handful'
        ]
    
    async def parse_and_analyze_meal(
        self,
        meal_input: str,
        default_quantity: str,
        user_context: Dict[str, Any],
        meal_type: str
    ) -> Dict[str, Any]:
        """Parse complex meal input and analyze each component"""
        
        print(f"🔍 Parsing meal input: {meal_input}")
        
        # Step 1: Detect if this is a multi-food entry
        food_items = self._parse_food_items(meal_input, default_quantity)
        
        if len(food_items) == 1:
            # Single food item - analyze normally
            food, quantity = food_items[0]
            return await self.meal_service.analyze_meal(
                food_item=food,
                quantity=quantity,
                user_context=user_context
            )
        
        # Step 2: Multi-food entry - analyze each component
        print(f"📦 Detected {len(food_items)} food items")
        
        components = []
        total_nutrition = {
            "calories": 0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
            "fiber_g": 0.0,
            "sugar_g": 0.0,
            "sodium_mg": 0
        }
        
        # Analyze each food item
        for food, quantity in food_items:
            try:
                print(f"  • Analyzing: {food} ({quantity})")
                
                result = await self.meal_service.analyze_meal(
                    food_item=food,
                    quantity=quantity,
                    user_context=user_context
                )
                
                # Add to total
                total_nutrition["calories"] += result.get("calories", 0)
                total_nutrition["protein_g"] += result.get("protein_g", 0)
                total_nutrition["carbs_g"] += result.get("carbs_g", 0)
                total_nutrition["fat_g"] += result.get("fat_g", 0)
                total_nutrition["fiber_g"] += result.get("fiber_g", 0)
                total_nutrition["sugar_g"] += result.get("sugar_g", 0)
                total_nutrition["sodium_mg"] += result.get("sodium_mg", 0)
                
                # Store component details
                components.append({
                    "food": food,
                    "quantity": quantity,
                    "calories": result.get("calories", 0),
                    "protein_g": result.get("protein_g", 0),
                    "source": result.get("data_source", "unknown")
                })
                
            except Exception as e:
                print(f"  ⚠️ Failed to analyze {food}: {e}")
                continue
        
        # Step 3: Calculate health score for combined meal
        healthiness_score = self._calculate_combined_health_score(
            total_nutrition, user_context
        )
        
        # Step 4: Generate suggestions for the complete meal
        suggestions = self._generate_meal_suggestions(
            total_nutrition, components, user_context
        )
        
        # Return combined analysis
        return {
            **total_nutrition,
            "serving_description": meal_input,
            "components": components,
            "component_count": len(components),
            "healthiness_score": healthiness_score,
            "suggestions": suggestions,
            "nutrition_notes": f"Combined meal with {len(components)} items",
            "data_source": "multi-food-parser",
            "confidence_score": 0.9
        }
    
    def _parse_food_items(self, meal_input: str, default_quantity: str) -> List[Tuple[str, str]]:
        """Parse meal input into individual food items with quantities"""
        
        meal_lower = meal_input.lower()
        items = []
        
        # Check for common meal patterns
        if self._is_standard_meal(meal_lower):
            return self._parse_standard_meal(meal_input, default_quantity)
        
        # Try to split by separators
        parts = [meal_input]
        for separator in self.separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(separator))
            parts = new_parts
        
        # Process each part
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Extract quantity from the part
            food, quantity = self._extract_quantity_from_text(part)
            
            # Use default quantity if none found
            if not quantity:
                quantity = default_quantity if default_quantity else "1 serving"
            
            items.append((food, quantity))
        
        # If no splitting occurred, treat as single item
        if len(items) == 0:
            items.append((meal_input, default_quantity or "1 serving"))
        
        return items
    
    def _extract_quantity_from_text(self, text: str) -> Tuple[str, str]:
        """Extract quantity from food text"""
        
        # Pattern: number + unit at the beginning
        pattern = r'^(\d+\.?\d*)\s*(' + '|'.join(self.quantity_words) + r')\s+(.+)$'
        match = re.match(pattern, text.lower())
        
        if match:
            quantity = f"{match.group(1)} {match.group(2)}"
            food = match.group(3)
            return food, quantity
        
        # Pattern: number at the beginning (e.g., "2 apples")
        pattern = r'^(\d+\.?\d*)\s+(.+)$'
        match = re.match(pattern, text)
        
        if match:
            quantity = match.group(1)
            food = match.group(2)
            return food, quantity
        
        # No quantity found
        return text, ""
    
    def _is_standard_meal(self, meal_text: str) -> bool:
        """Check if this is a standard meal combo"""
        
        standard_meals = [
            "burger and fries",
            "fish and chips",
            "rice and beans",
            "pasta and salad",
            "sandwich and chips",
            "eggs and toast",
            "chicken and rice",
            "steak and potatoes"
        ]
        
        return any(meal in meal_text for meal in standard_meals)
    
    def _parse_standard_meal(self, meal_input: str, default_quantity: str) -> List[Tuple[str, str]]:
        """Parse standard meal combinations"""
        
        meal_lower = meal_input.lower()
        
        # Define standard meal compositions
        meal_patterns = {
            "burger and fries": [
                ("burger", "1 medium"),
                ("french fries", "1 medium serving")
            ],
            "fish and chips": [
                ("fried fish fillet", "1 piece"),
                ("french fries", "1 serving")
            ],
            "eggs and toast": [
                ("scrambled eggs", "2 eggs"),
                ("toast", "2 slices")
            ],
            # Add more patterns as needed
        }
        
        for pattern, components in meal_patterns.items():
            if pattern in meal_lower:
                return components
        
        return [(meal_input, default_quantity or "1 serving")]
    
    def _calculate_combined_health_score(
        self,
        nutrition: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> int:
        """Calculate health score for combined meal"""
        
        score = 7  # Base score
        
        # Adjust based on calories vs TDEE
        tdee = user_context.get('tdee', 2000)
        meal_percent = (nutrition['calories'] / tdee) * 100
        
        if 20 <= meal_percent <= 35:  # Good meal size
            score += 1
        elif meal_percent > 50:  # Too large
            score -= 2
        elif meal_percent < 15:  # Too small
            score -= 1
        
        # Check macronutrient balance
        if nutrition['calories'] > 0:
            protein_percent = (nutrition['protein_g'] * 4 / nutrition['calories']) * 100
            if protein_percent >= 20:
                score += 1
        
        # Fiber content
        if nutrition['fiber_g'] >= 5:
            score += 1
        
        # Sodium check
        if nutrition['sodium_mg'] > 1000:
            score -= 1
        
        return max(1, min(10, score))
    
    def _generate_meal_suggestions(
        self,
        nutrition: Dict[str, Any],
        components: List[Dict],
        user_context: Dict[str, Any]
    ) -> str:
        """Generate suggestions for the complete meal"""
        
        suggestions = []
        
        # Check if meal is balanced
        if nutrition['protein_g'] < 20:
            suggestions.append("Consider adding more protein")
        
        if nutrition['fiber_g'] < 5:
            suggestions.append("Add vegetables or whole grains for fiber")
        
        # Check portion size
        tdee = user_context.get('tdee', 2000)
        if nutrition['calories'] > tdee * 0.5:
            suggestions.append("This is a large meal - consider splitting it")
        
        # Goal-specific advice
        goal = user_context.get('primary_goal', '')
        if 'lose' in goal.lower() and nutrition['calories'] > 600:
            suggestions.append("For weight loss, aim for smaller portions")
        elif 'gain' in goal.lower() and nutrition['protein_g'] < 30:
            suggestions.append("Add more protein for muscle gain")
        
        if not suggestions:
            suggestions.append("Well-balanced meal choice!")
        
        return ". ".join(suggestions)

# Singleton
_parser_service = None

def get_meal_parser_service():
    global _parser_service
    if _parser_service is None:
        _parser_service = MealParserService()
    return _parser_service