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
        
        # Quantity indicators with their standard conversions
        self.quantity_words = {
            'cup': 'cup', 'cups': 'cups',
            'tbsp': 'tbsp', 'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
            'tsp': 'tsp', 'teaspoon': 'tsp', 'teaspoons': 'tsp',
            'oz': 'oz', 'ounce': 'oz', 'ounces': 'oz',
            'gram': 'g', 'grams': 'g', 'g': 'g',
            'piece': 'piece', 'pieces': 'pieces',
            'slice': 'slice', 'slices': 'slices',
            'serving': 'serving', 'servings': 'servings',
            'plate': 'plate', 'plates': 'plates',
            'bowl': 'bowl', 'bowls': 'bowls',
            'small': 'small', 'medium': 'medium', 'large': 'large',
            'handful': 'handful', 'handfuls': 'handfuls'
        }
        
        # Common food items and their typical unit
        self.food_units = {
            'egg': 'eggs',
            'toast': 'slices',
            'bread': 'slices',
            'apple': 'medium',
            'banana': 'medium',
            'orange': 'medium',
            'sandwich': 'whole',
            'burger': 'burger',
            'pizza': 'slices',
            'cookie': 'cookies',
            'chicken breast': 'piece',
            'salmon': 'oz',
            'rice': 'cup cooked',
            'pasta': 'cup cooked',
            'milk': 'cup',
            'juice': 'cup',
            'coffee': 'cup',
            'tea': 'cup'
        }
    
    def _extract_quantity_from_text(self, text: str) -> Tuple[str, str]:
        """Extract quantity from food text with intelligent parsing"""
        
        text = text.strip()
        
        # STEP 1: Handle eggs specifically (most common issue)
        if 'egg' in text.lower():
            patterns = [
                # "2 scrambled eggs", "3 fried eggs", etc.
                (r'^(\d+)\s*(scrambled|fried|boiled|poached|hard[\s-]?boiled|soft[\s-]?boiled)?\s*eggs?', 
                 lambda m: (f"{m.group(2) or 'cooked'} eggs", f"{m.group(1)} eggs")),
                # "scrambled eggs (2)", "eggs, scrambled (3)"
                (r'(scrambled|fried|boiled|poached)?\s*eggs?\s*\((\d+)\)',
                 lambda m: (f"{m.group(1) or 'cooked'} eggs", f"{m.group(2)} eggs")),
                # "2 eggs, scrambled"
                (r'^(\d+)\s*eggs?,?\s*(scrambled|fried|boiled|poached)?',
                 lambda m: (f"{m.group(2) or 'cooked'} eggs", f"{m.group(1)} eggs")),
            ]
            
            for pattern, extractor in patterns:
                match = re.search(pattern, text.lower())
                if match:
                    return extractor(match)
        
        # STEP 2: Handle toast/bread specifically
        if 'toast' in text.lower() or 'bread' in text.lower():
            patterns = [
                # "2 slices whole wheat toast", "3 pieces of bread"
                (r'^(\d+)\s*(slices?|pieces?)\s+(?:of\s+)?(.*?)(toast|bread)',
                 lambda m: (f"{m.group(3)} {m.group(4)}".strip(), f"{m.group(1)} slices")),
                # "2 whole wheat toast"
                (r'^(\d+)\s+(.*?)(toast|bread)',
                 lambda m: (f"{m.group(2)} {m.group(3)}".strip(), f"{m.group(1)} slices")),
                # "whole wheat toast (2 slices)"
                (r'(.*?)(toast|bread)\s*\((\d+)\s*(slices?|pieces?)?\)',
                 lambda m: (f"{m.group(1)} {m.group(2)}".strip(), f"{m.group(3)} slices")),
            ]
            
            for pattern, extractor in patterns:
                match = re.search(pattern, text.lower())
                if match:
                    return extractor(match)
        
        # STEP 3: Handle items with explicit quantities in parentheses
        paren_pattern = r'^(.*?)\s*\((\d+\.?\d*)\s*([^)]+)?\)'
        match = re.match(paren_pattern, text)
        if match:
            food = match.group(1).strip()
            quantity_num = match.group(2)
            quantity_unit = match.group(3) or ''
            
            # Clean up the unit
            if quantity_unit:
                quantity_unit = quantity_unit.strip()
                if quantity_unit in self.quantity_words:
                    quantity_unit = self.quantity_words[quantity_unit]
            
            return food, f"{quantity_num} {quantity_unit}".strip()
        
        # STEP 4: Standard pattern matching for "X unit of food"
        all_units = '|'.join(self.quantity_words.keys())
        pattern = r'^(\d+\.?\d*)\s*(' + all_units + r')?\s+(?:of\s+)?(.+)$'
        match = re.match(pattern, text.lower())
        
        if match:
            quantity_num = match.group(1)
            quantity_unit = match.group(2) or ''
            food = match.group(3)
            
            # Standardize the unit
            if quantity_unit in self.quantity_words:
                quantity_unit = self.quantity_words[quantity_unit]
            
            # If no unit specified, try to infer from food type
            if not quantity_unit:
                quantity_unit = self._infer_unit(food)
            
            return food, f"{quantity_num} {quantity_unit}".strip()
        
        # STEP 5: Just a number at the beginning
        pattern = r'^(\d+\.?\d*)\s+(.+)$'
        match = re.match(pattern, text)
        
        if match:
            quantity_num = match.group(1)
            food = match.group(2)
            
            # Infer unit based on food
            unit = self._infer_unit(food)
            return food, f"{quantity_num} {unit}"
        
        # STEP 6: No quantity found - return as is
        return text, ""
    
    def _infer_unit(self, food: str) -> str:
        """Infer the appropriate unit for a food item"""
        food_lower = food.lower()
        
        # Check known foods
        for food_key, unit in self.food_units.items():
            if food_key in food_lower:
                return unit
        
        # Default based on food characteristics
        if any(word in food_lower for word in ['juice', 'milk', 'coffee', 'tea', 'water', 'soda']):
            return 'cup'
        elif any(word in food_lower for word in ['apple', 'banana', 'orange', 'pear', 'peach']):
            return 'medium'
        elif any(word in food_lower for word in ['cookie', 'cracker', 'chip']):
            return 'pieces'
        elif any(word in food_lower for word in ['salad', 'soup', 'cereal', 'oatmeal']):
            return 'bowl'
        elif any(word in food_lower for word in ['sandwich', 'burger', 'wrap', 'burrito']):
            return 'whole'
        else:
            return 'serving'
    
    def _parse_food_items(self, meal_input: str, default_quantity: str) -> List[Tuple[str, str]]:
        """Parse meal input into individual food items with quantities"""
        
        meal_input = meal_input.strip()
        items = []
        
        # First check if it's a known combo meal
        if self._is_standard_meal(meal_input.lower()):
            return self._parse_standard_meal(meal_input, default_quantity)
        
        # Split by common separators
        parts = [meal_input]
        for separator in self.separators:
            new_parts = []
            for part in parts:
                if separator in part.lower():
                    # Split but preserve the context
                    split_parts = part.split(separator)
                    new_parts.extend(split_parts)
                else:
                    new_parts.append(part)
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
            
            # Clean up the food name
            food = food.strip()
            if food:
                items.append((food, quantity))
                print(f"  📦 Parsed: '{food}' with quantity '{quantity}'")
        
        # If no items were parsed, treat as single item
        if len(items) == 0:
            items.append((meal_input, default_quantity or "1 serving"))
        
        return items
    
    def _is_standard_meal(self, meal_text: str) -> bool:
        """Check if this is a standard meal combo"""
        standard_meals = [
            "burger and fries",
            "fish and chips",
            "eggs and toast",
            "eggs and bacon",
            "chicken and rice",
            "steak and potatoes",
            "pasta and salad",
            "sandwich and chips"
        ]
        return any(meal in meal_text for meal in standard_meals)
    
    def _parse_standard_meal(self, meal_input: str, default_quantity: str) -> List[Tuple[str, str]]:
        """Parse standard meal combinations with better quantity handling"""
        
        meal_lower = meal_input.lower()
        
        # Special handling for eggs and toast (most common breakfast)
        if 'egg' in meal_lower and 'toast' in meal_lower:
            items = []
            
            # Extract egg info
            egg_patterns = [
                r'(\d+)\s*(scrambled|fried|boiled|poached)?\s*eggs?',
                r'(scrambled|fried|boiled|poached)?\s*eggs?\s*\((\d+)\)',
            ]
            
            for pattern in egg_patterns:
                match = re.search(pattern, meal_lower)
                if match:
                    if match.lastindex == 2:  # First pattern
                        num = match.group(1)
                        style = match.group(2) or 'scrambled'
                    else:  # Second pattern
                        style = match.group(1) or 'scrambled'
                        num = match.group(2)
                    items.append((f"{style} eggs", f"{num} eggs"))
                    break
            
            # Extract toast info
            toast_patterns = [
                r'(\d+)\s*(slices?)?\s*(whole wheat|wheat|white|multigrain)?\s*toast',
                r'(whole wheat|wheat|white|multigrain)?\s*toast\s*\((\d+)\s*(slices?)?\)',
            ]
            
            for pattern in toast_patterns:
                match = re.search(pattern, meal_lower)
                if match:
                    if '(' in pattern:  # Second pattern
                        bread_type = match.group(1) or 'wheat'
                        num = match.group(2)
                    else:  # First pattern
                        num = match.group(1)
                        bread_type = match.group(3) or 'wheat'
                    items.append((f"{bread_type} toast", f"{num} slices"))
                    break
            
            # Check for additional items like juice, bacon, etc.
            if 'juice' in meal_lower:
                juice_match = re.search(r'(\d+)\s*(cup|glass)?\s*(orange|apple|grape)?\s*juice', meal_lower)
                if juice_match:
                    amount = juice_match.group(1)
                    unit = juice_match.group(2) or 'cup'
                    juice_type = juice_match.group(3) or 'orange'
                    items.append((f"{juice_type} juice", f"{amount} {unit}"))
            
            if 'bacon' in meal_lower:
                bacon_match = re.search(r'(\d+)\s*(strips?|pieces?)?\s*(?:of\s+)?bacon', meal_lower)
                if bacon_match:
                    num = bacon_match.group(1)
                    items.append(("bacon", f"{num} strips"))
            
            if items:
                return items
        
        # Default patterns for other standard meals
        meal_patterns = {
            "burger and fries": [
                ("burger", "1 medium"),
                ("french fries", "1 medium serving")
            ],
            "fish and chips": [
                ("fried fish fillet", "1 piece"),
                ("french fries", "1 serving")
            ],
            "chicken and rice": [
                ("grilled chicken breast", "4 oz"),
                ("white rice", "1 cup cooked")
            ],
            # Add more as needed
        }
        
        for pattern, components in meal_patterns.items():
            if pattern in meal_lower:
                return components
        
        return [(meal_input, default_quantity or "1 serving")]

# Singleton pattern
_parser_service = None

def get_meal_parser_service():
    global _parser_service
    if _parser_service is None:
        _parser_service = MealParserService()
    return _parser_service