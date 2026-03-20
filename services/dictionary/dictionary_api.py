"""
dictionary_api.py
------------------
Fetch word meanings using a free Dictionary API
"""

import requests


# ===================== CONFIG =====================
BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en"
TIMEOUT = 5


def lookup_word(word: str) -> dict:
    """
    Look up a word in the dictionary.

    Args:
        word (str): Word to search

    Returns:
        dict: Word meaning data or error
    """

    if not word or not isinstance(word, str):
        return {
            "success": False,
            "error": "Invalid word"
        }

    try:
        response = requests.get(
            f"{BASE_URL}/{word.strip()}",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        meanings = []

        for meaning in data[0].get("meanings", []):
            part_of_speech = meaning.get("partOfSpeech")
            for definition in meaning.get("definitions", []):
                meanings.append({
                    "part_of_speech": part_of_speech,
                    "definition": definition.get("definition"),
                    "example": definition.get("example")
                })

        return {
            "success": True,
            "word": data[0].get("word"),
            "phonetic": data[0].get("phonetic"),
            "meanings": meanings
        }

    except requests.exceptions.HTTPError:
        return {
            "success": False,
            "error": "Word not found"
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Dictionary service timeout"
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }
