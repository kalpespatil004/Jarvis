"""
crypto_api.py
--------------
Fetch real-time cryptocurrency prices using CoinGecko API
"""

import requests


# ===================== CONFIG =====================
BASE_URL = "https://api.coingecko.com/api/v3/simple/price"
TIMEOUT = 5

# Supported coins (extendable)
SUPPORTED_COINS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "dogecoin": "DOGE",
    "litecoin": "LTC",
    "ripple": "XRP"
}

SUPPORTED_CURRENCIES = ["usd", "inr", "eur"]


# ===================== MAIN FUNCTION =====================
def get_crypto_price(symbol: str = "bitcoin", currency: str = "inr") -> dict:
    """
    Fetch live crypto price.

    Args:
        symbol (str): bitcoin, ethereum, etc.
        currency (str): inr, usd, eur

    Returns:
        dict: Crypto price data or error
    """

    symbol = symbol.lower()
    currency = currency.lower()

    if symbol not in SUPPORTED_COINS:
        return {
            "success": False,
            "error": f"Unsupported coin: {symbol}",
            "supported_coins": list(SUPPORTED_COINS.keys())
        }

    if currency not in SUPPORTED_CURRENCIES:
        return {
            "success": False,
            "error": f"Unsupported currency: {currency}",
            "supported_currencies": SUPPORTED_CURRENCIES
        }

    params = {
        "ids": symbol,
        "vs_currencies": currency
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
            "coin": symbol,
            "symbol": SUPPORTED_COINS[symbol],
            "currency": currency.upper(),
            "price": data[symbol][currency]
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Crypto service timeout"
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
