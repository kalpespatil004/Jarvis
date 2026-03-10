"""
search.py
----------
YouTube search utility
"""

import webbrowser
import urllib.parse


def search_youtube(query: str, open_browser: bool = True) -> dict:
    """
    Search YouTube for a query.

    Args:
        query (str): Search text
        open_browser (bool): Open browser or not

    Returns:
        dict: Search result info
    """

    if not query or not isinstance(query, str):
        return {
            "success": False,
            "error": "Invalid search query"
        }

    encoded_query = urllib.parse.quote_plus(query.strip())
    search_url = f"https://www.youtube.com/results?search_query={encoded_query}"

    try:
        if open_browser:
            webbrowser.open(search_url)

        return {
            "success": True,
            "query": query,
            "url": search_url,
            "message": f"🔍 Searching YouTube for '{query}'"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
