"""
services/dictionary/meanings.py
--------------------------------
Format dictionary API response into readable text.
"""


def format_meanings(data: dict) -> str:
    if not data.get("success"):
        return f"❌ Dictionary error: {data.get('error', 'Word not found')}"

    word     = data.get("word", "")
    phonetic = data.get("phonetic", "")
    meanings = data.get("meanings", [])

    if not meanings:
        return f"No meanings found for '{word}'."

    lines = [f"📖 {word.upper()} {phonetic}"]
    for i, m in enumerate(meanings[:5], 1):
        pos  = m.get("part_of_speech", "")
        defn = m.get("definition", "")
        ex   = m.get("example", "")
        lines.append(f"  {i}. [{pos}] {defn}")
        if ex:
            lines.append(f"      e.g. \"{ex}\"")

    return "\n".join(lines)
