"""
music_services.py
------------------
YouTube Music integration for Jarvis.

Features:
- Play music by name / mood / artist / genre / playlist
- Actually opens YouTube Music and focuses browser
- Stop / Pause / Resume / Next / Previous via keyboard media keys
- Mood-to-query smart mapping
"""

import webbrowser
import urllib.parse
import time

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None


# =========================
# MOOD → SEARCH QUERY MAP
# =========================
MOOD_MAP = {
    # Sleep / Relax
    "sleeping":      "relaxing sleep music no ads",
    "sleep":         "deep sleep music calm",
    "relax":         "relaxing chill music lofi",
    "relaxing":      "relaxing music ambient",
    "calm":          "calm peaceful music instrumental",
    "chill":         "lofi chill beats to relax",
    "peaceful":      "peaceful meditation music",
    "meditation":    "meditation music calm focus",

    # Focus / Study
    "focus":         "focus music study deep concentration",
    "study":         "lofi hip hop study beats",
    "studying":      "lofi beats study music",
    "concentration": "concentration music brain power",
    "work":          "background music for work focus",
    "coding":        "coding music lofi programming beats",
    "productive":    "productive background music",

    # Energy / Workout
    "workout":       "workout gym motivation music",
    "gym":           "gym pump up music energy",
    "energy":        "high energy pump up songs",
    "morning":       "morning motivation music positive",
    "running":       "running music high energy beats",
    "dance":         "dance music hits",
    "party":         "party music playlist 2024",

    # Mood / Emotion
    "happy":         "happy upbeat feel good songs",
    "sad":           "sad emotional songs",
    "romantic":      "romantic love songs playlist",
    "love":          "love songs romantic playlist",
    "angry":         "angry aggressive metal music",
    "nostalgic":     "nostalgic 90s 2000s hits",
    "lonely":        "lonely sad songs playlist",
    "motivated":     "motivational songs workout",

    # Genre
    "lofi":          "lofi hip hop beats",
    "jazz":          "smooth jazz music",
    "classical":     "classical music instrumental",
    "pop":           "top pop songs 2024",
    "rock":          "best rock songs playlist",
    "rap":           "best rap hip hop playlist",
    "bollywood":     "bollywood hits songs",
    "punjabi":       "punjabi songs latest hits",
    "devotional":    "devotional songs morning",
    "instrumental":  "instrumental background music",
    "acoustic":      "acoustic guitar music relaxing",
    "edm":           "edm electronic dance music",

    # Time of day
    "night":         "night time chill music",
    "evening":       "evening relaxing music chill",
    "afternoon":     "afternoon chill background music",
}


# =========================
# BROWSER / WINDOW CONTROL
# =========================
_YOUTUBE_MUSIC_URL = "https://music.youtube.com"
_browser_opened = False


def _build_search_url(query: str) -> str:
    encoded = urllib.parse.quote_plus(query.strip())
    return f"https://music.youtube.com/search?q={encoded}"


def _focus_youtube_music() -> bool:
    """
    Try to focus an already-open YouTube Music browser window.
    Returns True if found and focused, False otherwise.
    """
    if not gw:
        return False
    try:
        windows = gw.getAllTitles()
        for title in windows:
            if "youtube music" in title.lower() or "music.youtube" in title.lower():
                win = gw.getWindowsWithTitle(title)
                if win:
                    win[0].activate()
                    time.sleep(0.5)
                    return True
    except Exception:
        pass
    return False


def _open_and_play(url: str):
    """
    Open URL in browser and wait for it to load.
    """
    global _browser_opened
    webbrowser.open(url)
    _browser_opened = True
    time.sleep(3)  # Wait for browser/tab to load


def _send_key(key: str) -> bool:
    """
    Send a keyboard key safely.
    """
    if not pyautogui:
        return False
    try:
        pyautogui.press(key)
        return True
    except Exception:
        return False


# =========================
# PLAY MUSIC
# =========================
def play_music_response(query: str = "") -> str:
    """
    Main play function. Detects mood, artist, or song from query.
    Opens YouTube Music and plays automatically.

    Args:
        query (str): Raw user text e.g. "play chill music for sleeping"

    Returns:
        str: Response message
    """
    global _browser_opened

    query_lower = query.lower()

    # 1. Mood detection
    mood_query = None
    detected_mood = None
    for mood, search in MOOD_MAP.items():
        if mood in query_lower:
            mood_query = search
            detected_mood = mood
            break

    if mood_query:
        url = _build_search_url(mood_query)
        _open_and_play(url)
        return f"🎵 Playing {detected_mood} music for you, sir."

    # 2. Artist detection — "play songs by X" or "play X songs"
    import re
    artist_match = re.search(
        r"\b(?:play|put on)\b.*?\b(?:by|songs by|music by)\s+(.+)", query_lower
    )
    if artist_match:
        artist = artist_match.group(1).strip()
        url = _build_search_url(f"{artist} songs")
        _open_and_play(url)
        return f"🎵 Playing {artist} songs, sir."

    # 3. Specific song/query — clean filler words
    fillers = [
        "play", "music", "song", "songs", "please", "jarvis",
        "put on", "start", "me", "for", "i want", "i need",
        "can you", "could you", "some", "a", "the", "on youtube"
    ]
    clean = query_lower
    for filler in fillers:
        clean = clean.replace(filler, "")
    clean = clean.strip()

    if clean:
        url = _build_search_url(clean)
        _open_and_play(url)
        return f"🎵 Playing '{clean}' on YouTube Music, sir."

    # 4. Fallback — open YouTube Music home
    _open_and_play(_YOUTUBE_MUSIC_URL)
    return "🎵 Opening YouTube Music, sir."


# =========================
# STOP / PAUSE MUSIC
# =========================
def stop_music_response() -> str:
    """
    Pause/stop currently playing music.
    Focuses YouTube Music window first, then sends pause key.

    Returns:
        str: Response message
    """
    # Focus YouTube Music window
    focused = _focus_youtube_music()

    if focused:
        # Send space to pause (works in YouTube Music)
        time.sleep(0.3)
        if _send_key("space"):
            return "⏸ Music paused, sir."

    # Try media key as fallback (works system-wide)
    if _send_key("playpause"):
        return "⏸ Music paused, sir."

    return "❌ Could not pause music. Please pause it manually."


# =========================
# RESUME MUSIC
# =========================
def resume_music_response() -> str:
    """
    Resume paused music.

    Returns:
        str: Response message
    """
    focused = _focus_youtube_music()

    if focused:
        time.sleep(0.3)
        if _send_key("space"):
            return "▶ Music resumed, sir."

    if _send_key("playpause"):
        return "▶ Music resumed, sir."

    return "❌ Could not resume music."


# =========================
# NEXT TRACK
# =========================
def next_track_response() -> str:
    """
    Skip to next track.

    Returns:
        str: Response message
    """
    focused = _focus_youtube_music()

    if focused:
        time.sleep(0.3)
        # YouTube Music next button shortcut: Shift + N
        if pyautogui:
            try:
                pyautogui.hotkey("shift", "n")
                return "⏭ Skipped to next track, sir."
            except Exception:
                pass

    if _send_key("nexttrack"):
        return "⏭ Skipped to next track, sir."

    return "❌ Could not skip track."


# =========================
# PREVIOUS TRACK
# =========================
def previous_track_response() -> str:
    """
    Go to previous track.

    Returns:
        str: Response message
    """
    focused = _focus_youtube_music()

    if focused:
        time.sleep(0.3)
        # YouTube Music previous: Shift + P
        if pyautogui:
            try:
                pyautogui.hotkey("shift", "p")
                return "⏮ Playing previous track, sir."
            except Exception:
                pass

    if _send_key("prevtrack"):
        return "⏮ Playing previous track, sir."

    return "❌ Could not go to previous track."


# =========================
# PLAY BY MOOD
# =========================
def play_music_by_mood(mood: str) -> str:
    """
    Play music by mood keyword directly.

    Args:
        mood (str): e.g. "happy", "chill", "sad"

    Returns:
        str: Response message
    """
    mood = mood.lower().strip()
    query = MOOD_MAP.get(mood)

    if not query:
        # Partial match
        for key in MOOD_MAP:
            if mood in key or key in mood:
                query = MOOD_MAP[key]
                mood = key
                break

    if not query:
        query = f"{mood} music"

    url = _build_search_url(query)
    _open_and_play(url)
    return f"🎵 Playing {mood} music for you, sir."


# =========================
# PLAY ARTIST
# =========================
def play_artist(artist: str) -> str:
    """
    Play songs by a specific artist.

    Args:
        artist (str): Artist name

    Returns:
        str: Response message
    """
    if not artist or not artist.strip():
        return "Please tell me which artist to play, sir."

    url = _build_search_url(f"{artist.strip()} songs")
    _open_and_play(url)
    return f"🎵 Playing {artist} songs, sir."


# =========================
# PLAY PLAYLIST / GENRE
# =========================
def play_playlist(genre: str) -> str:
    """
    Play a playlist by genre or keyword.

    Args:
        genre (str): e.g. "lofi", "jazz", "bollywood"

    Returns:
        str: Response message
    """
    if not genre or not genre.strip():
        return "Please tell me which genre or playlist to play, sir."

    query = MOOD_MAP.get(genre.lower().strip(), f"{genre} playlist")
    url = _build_search_url(query)
    _open_and_play(url)
    return f"🎵 Playing {genre} playlist, sir."