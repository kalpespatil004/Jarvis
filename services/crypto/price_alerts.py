"""
price_alerts.py
----------------
Simple crypto price alert system
"""

from typing import Union


def check_price_alert(
    current_price: Union[int, float],
    target_price: Union[int, float],
    direction: str = "above"
) -> dict:
    """
    Check if crypto price meets alert condition.

    Args:
        current_price (float): Current market price
        target_price (float): Target alert price
        direction (str): "above" or "below"

    Returns:
        dict: Alert result
    """

    if not isinstance(current_price, (int, float)):
        return {
            "success": False,
            "error": "Invalid current price"
        }

    if not isinstance(target_price, (int, float)):
        return {
            "success": False,
            "error": "Invalid target price"
        }

    direction = direction.lower()

    if direction not in ("above", "below"):
        return {
            "success": False,
            "error": "Direction must be 'above' or 'below'"
        }

    triggered = False

    if direction == "above" and current_price >= target_price:
        triggered = True

    if direction == "below" and current_price <= target_price:
        triggered = True

    return {
        "success": True,
        "triggered": triggered,
        "current_price": current_price,
        "target_price": target_price,
        "direction": direction,
        "message": (
            "🚨 Price alert triggered!"
            if triggered
            else "⏳ Price alert not triggered yet"
        )
    }
