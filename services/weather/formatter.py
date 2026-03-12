"""
formatter.py
-------------
Convert raw weather data into human-readable text
"""


def format_weather(weather: dict) -> str:
    """
    Format weather dictionary into readable output.

    Args:
        weather (dict): Output from get_weather()

    Returns:
        str: Formatted weather string
    """

    if not weather or not weather.get("success"):
        return f"❌ Error: {weather.get('error', 'Unknown error')}"

    return (
        f"🌤 Weather Report\n"
        f"-----------------\n"
        f"📍 Location : {weather['city']}, {weather['country']}\n"
        f"🌡 Temperature : {weather['temperature']}°C\n"
        f"🤗 Feels Like : {weather['feels_like']}°C\n"
        f"☁ Condition : {weather['weather'].capitalize()}\n"
        f"💧 Humidity : {weather['humidity']}%\n"
        f"🌬 Wind Speed : {weather['wind_speed']} m/s\n"
        f"🔎 Visibility : {weather['visibility']} meters\n"
        f"⚖ Pressure : {weather['pressure']} hPa"
    )
