"""
services/weather/weather_api.py
--------------------------------
Fetch real-time weather data from OpenWeatherMap.
"""

import requests

try:
    from config import OPENWEATHER_API_KEY, DEFAULT_WEATHER_CITY
except ImportError:
    import os
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    DEFAULT_WEATHER_CITY = "Pune"

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
TIMEOUT  = 5


def get_weather(city: str = None) -> dict:
    city = city or DEFAULT_WEATHER_CITY

    if not city or not isinstance(city, str):
        return {"success": False, "error": "Invalid city name"}

    if not OPENWEATHER_API_KEY:
        return {"success": False, "error": "No OPENWEATHER_API_KEY configured in .env"}

    params = {"q": city.strip(), "appid": OPENWEATHER_API_KEY, "units": "metric"}

    try:
        response = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return {
            "success"    : True,
            "city"       : data.get("name"),
            "country"    : data["sys"].get("country"),
            "temperature": data["main"].get("temp"),
            "feels_like" : data["main"].get("feels_like"),
            "humidity"   : data["main"].get("humidity"),
            "pressure"   : data["main"].get("pressure"),
            "weather"    : data["weather"][0].get("description"),
            "wind_speed" : data["wind"].get("speed"),
            "visibility" : data.get("visibility", 0),
        }
    except requests.HTTPError:
        return {"success": False, "error": "City not found or API error"}
    except requests.Timeout:
        return {"success": False, "error": "Weather service timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}
