"""
Crop recommendation service for Hageglede.
Provides plant recommendations based on hardiness zone and effort level.
"""

from typing import List, Dict, Any

# Plant database mapping zone (int) -> list of plants
PLANT_DATABASE: Dict[int, List[Dict[str, Any]]] = {
    1: [
        {
            'name': 'Carrots',
            'effort': 1,
            'yield_desc': 'Medium - 5-8 lbs per 10 ft row',
            'meals': ['Carrot soup', 'Roasted carrots', 'Carrot cake']
        },
        {
            'name': 'Spinach',
            'effort': 1,
            'yield_desc': 'High - continuous harvest',
            'meals': ['Spinach salad', 'Spinach quiche', 'Smoothies']
        },
        {
            'name': 'Potatoes',
            'effort': 2,
            'yield_desc': 'Very High - 10-15 lbs per plant',
            'meals': ['Mashed potatoes', 'Roasted potatoes', 'Potato soup']
        },
        {
            'name': 'Lettuce',
            'effort': 1,
            'yield_desc': 'Medium - heads every 6-8 weeks',
            'meals': ['Salads', 'Sandwiches', 'Lettuce wraps']
        },
        {
            'name': 'Radishes',
            'effort': 1,
            'yield_desc': 'Fast - ready in 3-4 weeks',
            'meals': ['Salads', 'Pickled radishes', 'Roasted radishes']
        },
        {
            'name': 'Cherry Tomatoes',
            'effort': 3,
            'yield_desc': 'High - 10-15 lbs per plant',
            'meals': ['Caprese salad', 'Pasta pomodoro', 'Fresh snacks']
        }
    ],
    2: [
        {
            'name': 'Zucchini',
            'effort': 2,
            'yield_desc': 'Very High - 6-10 lbs per plant',
            'meals': ['Zucchini bread', 'Grilled zucchini', 'Zucchini pasta']
        },
        {
            'name': 'Beans',
            'effort': 2,
            'yield_desc': 'High - continuous harvest',
            'meals': ['Bean salad', 'Bean soup', 'Stewed beans']
        },
        {
            'name': 'Cucumbers',
            'effort': 2,
            'yield_desc': 'High - 10-15 cucumbers per plant',
            'meals': ['Cucumber salad', 'Pickles', 'Tzatziki']
        },
        {
            'name': 'Beets',
            'effort': 1,
            'yield_desc': 'Medium - 3-5 lbs per 10 ft row',
            'meals': ['Roasted beets', 'Beet salad', 'Borscht']
        },
        {
            'name': 'Kale',
            'effort': 1,
            'yield_desc': 'High - continuous harvest',
            'meals': ['Kale chips', 'Kale salad', 'Kale smoothies']
        },
        {
            'name': 'Bell Peppers',
            'effort': 3,
            'yield_desc': 'Medium - 5-8 peppers per plant',
            'meals': ['Stuffed peppers', 'Fajitas', 'Salads']
        }
    ],
    3: [
        {
            'name': 'Tomatoes',
            'effort': 3,
            'yield_desc': 'Very High - 15-20 lbs per plant',
            'meals': ['Tomato sauce', 'BLT sandwiches', 'Salsa']
        },
        {
            'name': 'Corn',
            'effort': 3,
            'yield_desc': 'Medium - 1-2 ears per stalk',
            'meals': ['Corn on the cob', 'Corn chowder', 'Corn salad']
        },
        {
            'name': 'Squash',
            'effort': 2,
            'yield_desc': 'High - 3-5 squash per plant',
            'meals': ['Roasted squash', 'Squash soup', 'Squash casserole']
        },
        {
            'name': 'Peas',
            'effort': 2,
            'yield_desc': 'Medium - continuous harvest',
            'meals': ['Pea soup', 'Pea salad', 'Stir-fry']
        },
        {
            'name': 'Onions',
            'effort': 1,
            'yield_desc': 'Medium - 5-8 lbs per 10 ft row',
            'meals': ['French onion soup', 'Caramelized onions', 'Onion rings']
        },
        {
            'name': 'Herbs (Basil, Parsley, Cilantro)',
            'effort': 1,
            'yield_desc': 'High - continuous harvest',
            'meals': ['Pesto', 'Herb sauces', 'Seasoning']
        }
    ]
}


def get_recommendations(zone: int, effort_level: int) -> List[Dict[str, Any]]:
    """
    Get crop recommendations for a given zone and effort level.
    
    Args:
        zone: Hardiness zone (1, 2, or 3)
        effort_level: Maximum effort level (1-5)
    
    Returns:
        List of plant dictionaries filtered by effort <= effort_level,
        sorted by effort ascending, limited to top 12-20 plants.
    
    Raises:
        KeyError: If zone is not in PLANT_DATABASE
    """
    if zone not in PLANT_DATABASE:
        raise KeyError(f"Zone {zone} not found in plant database. Available zones: {list(PLANT_DATABASE.keys())}")
    
    # Filter plants by effort level
    filtered_plants = [
        plant for plant in PLANT_DATABASE[zone]
        if plant['effort'] <= effort_level
    ]
    
    # Sort by effort level (ascending)
    sorted_plants = sorted(filtered_plants, key=lambda x: x['effort'])
    
    # Return top 12-20 plants (in this case, we have 6 per zone, so return all filtered)
    # If we had more, we'd return 12-20, but with 6 per zone we return all that match the criteria
    return sorted_plants[:20]  # Cap at 20 for future expansion