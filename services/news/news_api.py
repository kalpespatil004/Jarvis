"""
news_api.py
-----------
Fetch latest news using NewsAPI
"""

import requests


# ===================== CONFIG =====================
API_KEY = "6fb9bba564e04e59a252aac69203301c"   # 🔑 Replace with your NewsAPI key
BASE_URL = "https://newsapi.org/v2/top-headlines"
TIMEOUT = 5


# ===================== MAIN FUNCTION =====================
def get_news(category: str = "general", country: str = "us", limit: int = 2) -> dict:
    """
    Fetch top headlines.

    Args:
        category (str): business, sports, technology, etc.
        country (str): Country code
        limit (int): Number of headlines

    Returns:
        dict: News data with formatted output
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
        formatted_news = []
        titles = []

        for i, article in enumerate(data.get("articles", []), start=1):
            news_item = {
                "title": article.get("title", "No Title"),
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", ""),
                "published": article.get("publishedAt", "")
            }

            articles.append(news_item)
            titles.append(news_item["title"])

            formatted_news.append(
                f"{i}. {news_item['title']}\n"
                f"Source : {news_item['source']}\n"
                f"Published : {news_item['published']}"
            )

        return {
            "success": True,
            "count": len(articles),
            "category": category,
            "news": articles,                          # Raw data
            "titles": titles,                          # List of titles only
            "titles_formatted": "\n".join(titles),     # Title-only string
            "formatted": "\n\n".join(formatted_news)   # Full clean text
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


if __name__ == "__main__":
    news_data = get_news()
    if news_data["success"]:
        print(news_data["titles_formatted"])
    else:
        print(news_data["error"])