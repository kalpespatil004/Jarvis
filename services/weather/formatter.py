"""
services/weather/formatter.py
------------------------------
Format weather API response into human-readable text.
"""


def format_weather(data: dict) -> str:
    if not data.get("success"):
        return f"❌ Weather error: {data.get('error', 'Unknown error')}"

    city    = data.get("city", "Unknown")
    country = data.get("country", "")
    temp    = data.get("temperature", "N/A")
    feels   = data.get("feels_like", "N/A")
    humidity= data.get("humidity", "N/A")
    wind    = data.get("wind_speed", "N/A")
    desc    = data.get("weather", "N/A").title()
    vis     = data.get("visibility", 0)
    vis_km  = f"{vis / 1000:.1f} km" if vis else "N/A"

    return (
        f"🌤 Weather in {city}, {country}:\n"
        f"  Condition  : {desc}\n"
        f"  Temperature: {temp}°C  (feels like {feels}°C)\n"
        f"  Humidity   : {humidity}%\n"
        f"  Wind Speed : {wind} m/s\n"
        f"  Visibility : {vis_km}"
    )
