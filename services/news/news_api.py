"""
news_api.py
-----------
Fetch latest news using NewsAPI
"""

import requests


# ===================== CONFIG =====================
API_KEY = "YOUR_NEWS_API_KEY"   # 🔑 Replace with your NewsAPI key
BASE_URL = "https://newsapi.org/v2/top-headlines"
TIMEOUT = 5


# ===================== MAIN FUNCTION =====================
def get_news(category: str = "general", country: str = "in", limit: int = 5) -> dict:
    """
    Fetch top headlines.

    Args:
        category (str): business, sports, technology, etc.
        country (str): Country code (default: in)
        limit (int): Number of headlines

    Returns:
        dict: News data or error
    """

    params = {
        "apiKey": API_KEY,
        "category": category,
        "country": country,
        "pageSize": limit
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title"),
                "source": article["source"].get("name"),
                "url": article.get("url"),
                "published": article.get("publishedAt")
            })

        return {
            "success": True,
            "count": len(articles),
            "category": category,
            "news": articles
        }

    except requests.exceptions.HTTPError:
        return {
            "success": False,
            "error": "Invalid request or API limit exceeded"
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "News service timeout"
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
