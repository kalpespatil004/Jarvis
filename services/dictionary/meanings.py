"""
meanings.py
------------
Format dictionary meanings into readable output
"""


def format_meanings(data: dict) -> str:
    """
    Format dictionary lookup result.

    Args:
        data (dict): Output from lookup_word()

    Returns:
        str: Formatted meanings
    """

    if not data or not data.get("success"):
        return f"❌ Error: {data.get('error', 'Unknown error')}"

    lines = []
    lines.append(f"📖 Word: {data.get('word')}")

    if data.get("phonetic"):
        lines.append(f"🔊 Pronunciation: {data['phonetic']}")

    lines.append("\nMeanings:")

    for idx, meaning in enumerate(data.get("meanings", []), start=1):
        lines.append(
            f"{idx}. ({meaning['part_of_speech']}) {meaning['definition']}"
        )
        if meaning.get("example"):
            lines.append(f"   👉 Example: {meaning['example']}")

    return "\n".join(lines)
