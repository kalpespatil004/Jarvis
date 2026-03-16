"""
services/news/news_api.py
--------------------------
Fetch latest news using NewsAPI.
"""

import requests

try:
    from config import NEWS_API_KEY, DEFAULT_NEWS_COUNTRY
except ImportError:
    import os
    NEWS_API_KEY         = os.getenv("NEWS_API_KEY", "")
    DEFAULT_NEWS_COUNTRY = "in"

BASE_URL = "https://newsapi.org/v2/top-headlines"
TIMEOUT  = 5


def get_news(category: str = "general", country: str = None, limit: int = 5) -> dict:
    country = country or DEFAULT_NEWS_COUNTRY

    if not NEWS_API_KEY:
        return {"success": False, "error": "No NEWS_API_KEY configured in .env"}

    params = {
        "apiKey"  : NEWS_API_KEY,
        "category": category,
        "country" : country,
        "pageSize": limit
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()

        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title"    : article.get("title"),
                "source"   : article["source"].get("name"),
                "url"      : article.get("url"),
                "published": article.get("publishedAt")
            })

        return {
            "success" : True,
            "count"   : len(articles),
            "category": category,
            "news"    : articles
        }
    except requests.HTTPError:
        return {"success": False, "error": "Invalid request or API limit exceeded"}
    except requests.Timeout:
        return {"success": False, "error": "News service timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}
