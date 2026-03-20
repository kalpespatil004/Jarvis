"""
triggers.py
------------
Trigger evaluation logic (IF this THEN that)
"""

from typing import Callable, Any


def evaluate_trigger(
    condition: bool,
    action: Callable[[], Any]
) -> dict:
    """
    Evaluate a trigger and execute action if condition is true.

    Args:
        condition (bool): Trigger condition
        action (callable): Function to execute if triggered

    Returns:
        dict: Trigger result
    """

    if not isinstance(condition, bool):
        return {
            "success": False,
            "error": "Condition must be boolean"
        }

    if not callable(action):
        return {
            "success": False,
            "error": "Action must be callable"
        }

    if condition:
        try:
            result = action()
            return {
                "success": True,
                "triggered": True,
                "result": result,
                "message": "✅ Trigger activated"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Action failed: {str(e)}"
            }

    return {
        "success": True,
        "triggered": False,
        "message": "⏳ Trigger not activated"
    }
