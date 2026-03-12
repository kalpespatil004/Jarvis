import requests


# ---------------------------
# GET CURRENT LOCATION (IP-BASED)
# ---------------------------

def get_location():
    """
    Get current latitude and longitude using IP-based API
    """
    try:
        response = requests.get("https://ipinfo.io")
        data = response.json()

        loc = data.get("loc")
        city = data.get("city")
        region = data.get("region")
        country = data.get("country")

        if loc:
            latitude, longitude = loc.split(",")
            return f"📍 Your Location:\nCity: {city}\nRegion: {region}\nCountry: {country}\nLatitude: {latitude}\nLongitude: {longitude}"

        return "❌ Could not fetch location"

    except Exception as e:
        return f"❌ Error fetching location: {e}"


# ---------------------------
# GET GOOGLE MAPS LINK
# ---------------------------

def get_maps_link():
    """
    Return Google Maps link for current location
    """
    try:
        response = requests.get("https://ipinfo.io")
        data = response.json()
        loc = data.get("loc")
        if loc:
            return f"🗺 Google Maps Link: https://www.google.com/maps?q={loc}"
        return "❌ Could not fetch location"

    except Exception as e:
        return f"❌ Error fetching map link: {e}"
