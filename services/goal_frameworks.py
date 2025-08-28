# services/goal_frameworks.py
from typing import Dict, Any
from datetime import datetime, timedelta

class WeightGoalFrameworks:

    @staticmethod
    def parse_timeline(timeline_str: str) -> int:
        """Parse timeline string to weeks
        
        Accepts formats:
        - '6_weeks', '12_weeks', '20_weeks' (new format)
        - 'Gradual', 'Moderate', 'Ambitious' (legacy format)
        - '3_months', '6_months' (old format - for backwards compatibility)
        """
        timeline_map = {
            # New week-based format
            '6_weeks': 6,
            '12_weeks': 12,
            '20_weeks': 20,
            '24_weeks': 24,
            
            # Legacy text format
            'Ambitious': 6,
            'Moderate': 12,
            'Gradual': 20,
            
            # Old month-based format (for backwards compatibility)
            '1_month': 4,
            '2_months': 8,
            '3_months': 12,
            '4_months': 16,
            '6_months': 24,
            
            # Default
            None: 12,
            '': 12,
        }
        
        return timeline_map.get(timeline_str, 12)
    
    @staticmethod
    def get_weight_loss_framework(user_profile: Dict[str, Any], activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive weight loss framework"""
        
        current_weight = user_profile.get('weight', 70)
        target_weight = user_profile.get('target_weight', 65)
        height = user_profile.get('height', 170)
        age = user_profile.get('age', 30)
        gender = user_profile.get('gender', 'Female')
        activity_level = user_profile.get('activity_level', 'Sedentary')
        tdee = user_profile.get('tdee', 1800)
        timeline_str = user_profile.get('goal_timeline', '12_weeks')
        
        # Parse timeline to weeks
        target_weeks = WeightGoalFrameworks.parse_timeline(timeline_str)
        
        # Calculate weight loss specifics
        weight_to_lose = current_weight - target_weight
        
        # Calculate weekly loss rate based on selected timeline
        weekly_loss_rate = weight_to_lose / target_weeks if target_weeks > 0 else 0.5
        
        # Ensure safe rate (max 1kg/week, recommended 0.5-0.75kg/week)
        safe_weekly_loss = min(1.0, weekly_loss_rate)
        if safe_weekly_loss < weekly_loss_rate:
            # Adjust timeline if rate is too aggressive
            estimated_weeks = weight_to_lose / safe_weekly_loss
        else:
            estimated_weeks = target_weeks
        
        # Caloric deficit calculation
        weekly_deficit_needed = safe_weekly_loss * 7700  # 7700 cal = 1kg fat
        daily_deficit = weekly_deficit_needed / 7
        target_calories = max(1200, tdee - daily_deficit)  # Never below 1200
        
        # Macronutrient targets for weight loss
        protein_per_kg = 1.6  # Higher protein for weight loss
        protein_grams = current_weight * protein_per_kg
        protein_calories = protein_grams * 4
        
        fat_percentage = 0.25  # 25% of calories from fat
        fat_calories = target_calories * fat_percentage
        fat_grams = fat_calories / 9
        
        carb_calories = target_calories - protein_calories - fat_calories
        carb_grams = carb_calories / 4
        
        # Exercise recommendations
        cardio_minutes_week = 150 + (weight_to_lose * 30)  # More cardio for more weight loss
        strength_sessions_week = 3
        
        # Meal timing and frequency
        meal_strategy = "intermittent_fasting" if weight_to_lose > 5 else "balanced_meals"
        meals_per_day = 3 if meal_strategy == "intermittent_fasting" else 4
        
        return {
            "framework_type": "weight_loss",
            "timeline": {
                "target_weeks": target_weeks,
                "estimated_weeks": round(estimated_weeks),
                "safe_weekly_loss": round(safe_weekly_loss, 2),
                "target_date": (datetime.now() + timedelta(weeks=estimated_weeks)).strftime("%Y-%m-%d"),
                "is_aggressive": weekly_loss_rate > 0.75,
                "timeline_label": timeline_str
            },
            "nutrition": {
                "daily_calories": round(target_calories),
                "caloric_deficit": round(daily_deficit),
                "macros": {
                    "protein_grams": round(protein_grams),
                    "carb_grams": round(carb_grams),
                    "fat_grams": round(fat_grams),
                    "protein_percentage": round((protein_calories / target_calories) * 100),
                    "carb_percentage": round((carb_calories / target_calories) * 100),
                    "fat_percentage": round((fat_calories / target_calories) * 100)
                },
                "meal_strategy": meal_strategy,
                "meals_per_day": meals_per_day,
                "hydration_glasses": 10,  # Increased for weight loss
                "fiber_target": 30
            },
            "exercise": {
                "cardio_minutes_week": cardio_minutes_week,
                "strength_sessions_week": strength_sessions_week,
                "daily_steps": 10000 + (weight_to_lose * 1000),
                "intensity_focus": "moderate_to_high",
                "recommended_activities": [
                    "Brisk walking", "Swimming", "Cycling", "HIIT workouts",
                    "Resistance training", "Yoga for flexibility"
                ]
            },
            "monitoring": {
                "weigh_frequency": "weekly",
                "progress_photos": "biweekly",
                "measurements": ["waist", "hips", "thighs"],
                "key_metrics": ["weight", "body_fat_percentage", "energy_levels"]
            },
            "supplements": {
                "recommended": ["Multivitamin", "Omega-3", "Vitamin D", "Magnesium"],
                "optional": ["Green tea extract", "L-Carnitine", "CLA"],
                "avoid": ["Mass gainers", "High-calorie protein powders"]
            },
            "behavioral_strategies": [
                "Track all food intake",
                "Meal prep on weekends",
                "Create caloric deficit through both diet and exercise",
                "Focus on whole, unprocessed foods",
                "Practice portion control",
                "Stay hydrated",
                "Get adequate sleep (7-9 hours)",
                "Manage stress levels"
            ],
            "warning_signs": [
                "Losing more than 1kg per week consistently",
                "Extreme fatigue or weakness",
                "Loss of menstrual cycle (for women)",
                "Obsessive thoughts about food",
                "Social isolation due to diet restrictions"
            ]
        }
    
    @staticmethod
    def get_weight_gain_framework(user_profile: Dict[str, Any], activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive weight gain framework"""
        
        current_weight = user_profile.get('weight', 60)
        target_weight = user_profile.get('target_weight', 70)
        height = user_profile.get('height', 170)
        age = user_profile.get('age', 25)
        gender = user_profile.get('gender', 'Male')
        tdee = user_profile.get('tdee', 2200)
        fitness_level = user_profile.get('fitness_level', 'Beginner')
        timeline_str = user_profile.get('goal_timeline', '12_weeks')
        
        # Parse timeline to weeks
        target_weeks = WeightGoalFrameworks.parse_timeline(timeline_str)
    
        # Calculate weight gain specifics
        weight_to_gain = target_weight - current_weight
        
        # Calculate weekly gain rate based on selected timeline
        weekly_gain_rate = weight_to_gain / target_weeks if target_weeks > 0 else 0.25
        
        # FIXED: For weight gain, we need to check if rate is TOO FAST
        # Safe gain: 0.25-0.5kg/week (0.5kg/week max for lean gains)
        safe_weekly_gain = min(0.5, weekly_gain_rate)  # Cap at 0.5kg/week max
        
        # If user wants to gain faster than safe rate, adjust timeline
        if weekly_gain_rate > safe_weekly_gain:
            # Need more time to gain safely
            estimated_weeks = weight_to_gain / safe_weekly_gain
        else:
            estimated_weeks = target_weeks
        
        # Caloric surplus calculation
        weekly_surplus_needed = safe_weekly_gain * 7700  # 7700 cal = 1kg
        daily_surplus = weekly_surplus_needed / 7
        target_calories = tdee + daily_surplus
        
        # Macronutrient targets for weight gain (muscle-focused)
        protein_per_kg = 2.0  # Higher protein for muscle gain
        protein_grams = current_weight * protein_per_kg
        protein_calories = protein_grams * 4
        
        fat_percentage = 0.3  # 30% of calories from healthy fats
        fat_calories = target_calories * fat_percentage
        fat_grams = fat_calories / 9
        
        carb_calories = target_calories - protein_calories - fat_calories
        carb_grams = carb_calories / 4
        
        # Exercise recommendations (strength-focused)
        strength_sessions_week = 4
        cardio_minutes_week = 90  # Minimal cardio to preserve calories
        
        return {
            "framework_type": "weight_gain",
            "timeline": {
                "estimated_weeks": round(estimated_weeks),
                "safe_weekly_gain": round(safe_weekly_gain, 2),
                "target_date": (datetime.now() + timedelta(weeks=estimated_weeks)).strftime("%Y-%m-%d")
            },
            "nutrition": {
                "daily_calories": round(target_calories),
                "caloric_surplus": round(daily_surplus),
                "macros": {
                    "protein_grams": round(protein_grams),
                    "carb_grams": round(carb_grams),
                    "fat_grams": round(fat_grams),
                    "protein_percentage": round((protein_calories / target_calories) * 100),
                    "carb_percentage": round((carb_calories / target_calories) * 100),
                    "fat_percentage": round((fat_calories / target_calories) * 100)
                },
                "meal_strategy": "frequent_meals",
                "meals_per_day": 5,
                "hydration_glasses": 10,
                "fiber_target": 25,
                "pre_workout_carbs": round(carb_grams * 0.3),
                "post_workout_protein": round(protein_grams * 0.4)
            },
            "exercise": {
                "strength_sessions_week": strength_sessions_week,
                "cardio_minutes_week": cardio_minutes_week,
                "daily_steps": 8000,
                "intensity_focus": "progressive_overload",
                "recommended_activities": [
                    "Compound lifts (squats, deadlifts, bench press)",
                    "Progressive resistance training",
                    "Bodyweight exercises",
                    "Light cardio for recovery"
                ],
                "rest_days": 2,
                "workout_duration": "45-60 minutes"
            },
            "monitoring": {
                "weigh_frequency": "weekly",
                "progress_photos": "biweekly",
                "measurements": ["chest", "arms", "thighs", "shoulders"],
                "key_metrics": ["weight", "muscle_mass", "strength_progress", "energy_levels"]
            },
            "supplements": {
                "recommended": ["Whey protein", "Creatine", "Multivitamin", "Vitamin D"],
                "optional": ["Mass gainer", "Beta-alanine", "HMB", "ZMA"],
                "timing": {
                    "pre_workout": ["Creatine", "Beta-alanine"],
                    "post_workout": ["Whey protein", "Simple carbs"],
                    "before_bed": ["Casein protein", "ZMA"]
                }
            },
            "behavioral_strategies": [
                "Eat calorie-dense, nutrient-rich foods",
                "Never skip meals",
                "Liquid calories (smoothies, milk)",
                "Prioritize compound exercises",
                "Focus on progressive overload",
                "Get adequate sleep (8-9 hours)",
                "Manage stress to optimize hormones",
                "Track strength progress"
            ],
            "warnings": [
                "Gaining too fast leads to excess fat gain" if weekly_gain_rate > 0.5 else None,
                "Ensure adequate protein for muscle synthesis",
                "Don't neglect vegetables despite caloric surplus",
                "Monitor body composition, not just weight"
            ],
            "food_recommendations": {
                "calorie_dense": [
                    "Nuts and nut butters", "Avocados", "Olive oil", "Quinoa",
                    "Salmon", "Whole grain pasta", "Sweet potatoes"
                ],
                "protein_rich": [
                    "Lean meats", "Fish", "Eggs", "Greek yogurt",
                    "Legumes", "Protein powder"
                ],
                "healthy_carbs": [
                    "Oats", "Brown rice", "Fruits", "Vegetables"
                ]
            }
        }
    
    @staticmethod
    def get_maintenance_framework(user_profile: Dict[str, Any], activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Weight maintenance framework"""
        
        current_weight = user_profile.get('weight', 65)
        tdee = user_profile.get('tdee', 2000)
        activity_level = user_profile.get('activity_level', 'Moderately active')
        
        # Maintenance calories (no deficit/surplus)
        target_calories = tdee
        maintenance_range = (tdee - 100, tdee + 100)  # ±100 calories
        
        # Balanced macronutrient distribution
        protein_per_kg = 1.2
        protein_grams = current_weight * protein_per_kg
        protein_calories = protein_grams * 4
        
        fat_percentage = 0.28
        fat_calories = target_calories * fat_percentage
        fat_grams = fat_calories / 9
        
        carb_calories = target_calories - protein_calories - fat_calories
        carb_grams = carb_calories / 4
        
        return {
            "framework_type": "weight_maintenance",
            "timeline": {
                "approach": "ongoing_lifestyle",
                "review_frequency": "monthly",
                "weight_fluctuation_range": "±1kg"
            },
            "nutrition": {
                "daily_calories": round(target_calories),
                "calorie_range": [round(maintenance_range[0]), round(maintenance_range[1])],
                "macros": {
                    "protein_grams": round(protein_grams),
                    "carb_grams": round(carb_grams),
                    "fat_grams": round(fat_grams),
                    "protein_percentage": round((protein_calories / target_calories) * 100),
                    "carb_percentage": round((carb_calories / target_calories) * 100),
                    "fat_percentage": round((fat_calories / target_calories) * 100)
                },
                "meal_strategy": "intuitive_eating",
                "meals_per_day": 3,
                "hydration_glasses": 8,
                "fiber_target": 25
            },
            "exercise": {
                "strength_sessions_week": 2,
                "cardio_minutes_week": 120,
                "daily_steps": 8000,
                "intensity_focus": "variety_and_enjoyment",
                "recommended_activities": [
                    "Mix of cardio and strength training",
                    "Recreational sports",
                    "Yoga or Pilates",
                    "Outdoor activities"
                ]
            },
            "monitoring": {
                "weigh_frequency": "weekly",
                "focus_metrics": ["energy_levels", "mood", "sleep_quality", "fitness_performance"],
                "body_composition": "every 3 months"
            },
            "supplements": {
                "recommended": ["Multivitamin", "Vitamin D", "Omega-3"],
                "seasonal": ["Vitamin C during flu season", "Extra Vitamin D in winter"]
            },
            "behavioral_strategies": [
                "Listen to hunger and fullness cues",
                "Maintain consistent eating schedule",
                "Stay active with enjoyable activities",
                "Practice stress management",
                "Prioritize sleep quality",
                "Allow flexibility in diet",
                "Regular health check-ups"
            ],
            "flexibility_principles": [
                "80/20 rule - healthy choices 80% of the time",
                "Enjoy social events without guilt",
                "Adjust portions based on activity level",
                "Seasonal eating variety",
                "Focus on overall patterns, not daily perfection"
            ]
        }
    
    @classmethod
    def get_framework_for_user(cls, user_profile: Dict[str, Any], activity_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get the appropriate framework based on user's weight goal"""
        
        if activity_data is None:
            activity_data = {}
            
        weight_goal = user_profile.get('weight_goal', 'maintain_weight')
        
        if weight_goal == 'lose_weight':
            return cls.get_weight_loss_framework(user_profile, activity_data)
        elif weight_goal == 'gain_weight':
            return cls.get_weight_gain_framework(user_profile, activity_data)
        else:  # maintain_weight or any other value
            return cls.get_maintenance_framework(user_profile, activity_data)