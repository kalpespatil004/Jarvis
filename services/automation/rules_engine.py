"""
rules_engine.py
----------------
Rule-based automation engine
"""

from typing import Callable, Dict, Any, List


def apply_rules(
    rules: List[Callable[[Dict[str, Any]], bool]],
    context: Dict[str, Any]
) -> dict:
    """
    Apply a list of rules on given context.

    Args:
        rules (list): List of rule functions
        context (dict): Data to evaluate rules against

    Returns:
        dict: Rule evaluation results
    """

    if not isinstance(rules, list):
        return {
            "success": False,
            "error": "Rules must be a list"
        }

    if not isinstance(context, dict):
        return {
            "success": False,
            "error": "Context must be a dictionary"
        }

    results = []

    for idx, rule in enumerate(rules, start=1):
        if not callable(rule):
            results.append({
                "rule": idx,
                "success": False,
                "error": "Rule is not callable"
            })
            continue

        try:
            matched = rule(context)
            results.append({
                "rule": idx,
                "matched": bool(matched)
            })
        except Exception as e:
            results.append({
                "rule": idx,
                "success": False,
                "error": str(e)
            })

    return {
        "success": True,
        "rules_evaluated": len(rules),
        "results": results
    }
