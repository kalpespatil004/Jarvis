"""
weather_api.py
----------------
Fetch real-time weather data using OpenWeatherMap API
"""

import requests


# ===================== CONFIG =====================
API_KEY = "YOUR_OPENWEATHER_API_KEY"   # 🔑 Replace with your API key
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
TIMEOUT = 5


# ===================== MAIN FUNCTION =====================
def get_weather(city: str) -> dict:
    """
    Fetch current weather for a given city.

    Args:
        city (str): City name (e.g., "Pune", "Mumbai")

    Returns:
        dict: Parsed weather information or error message
    """

    if not city or not isinstance(city, str):
        return {
            "success": False,
            "error": "Invalid city name"
        }

    params = {
        "q": city.strip(),
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "city": data.get("name"),
            "country": data["sys"].get("country"),
            "temperature": data["main"].get("temp"),
            "feels_like": data["main"].get("feels_like"),
            "humidity": data["main"].get("humidity"),
            "pressure": data["main"].get("pressure"),
            "weather": data["weather"][0].get("description"),
            "wind_speed": data["wind"].get("speed"),
            "visibility": data.get("visibility", 0),
        }

    except requests.exceptions.HTTPError:
        return {
            "success": False,
            "error": "City not found or API error"
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Weather service timeout"
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
