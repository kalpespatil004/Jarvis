"""
categories.py
--------------
Supported news categories for NewsAPI
"""

CATEGORIES = {
    "general": "General News",
    "business": "Business",
    "entertainment": "Entertainment",
    "health": "Health",
    "science": "Science",
    "sports": "Sports",
    "technology": "Technology"
}


def is_valid_category(category: str) -> bool:
    """
    Check if category is supported.

    Args:
        category (str)

    Returns:
        bool
    """
    return category in CATEGORIES


def list_categories() -> list:
    """
    Get all available news categories.

    Returns:
        list
    """
    return list(CATEGORIES.keys())
