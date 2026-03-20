"""Music control helpers."""

from __future__ import annotations

import os

from brain.response_picker import get_response


def play_music_response() -> str:
    music_dir = os.path.join(os.path.expanduser("~"), "Music")
    if not os.path.exists(music_dir):
        return "Music folder not found."

    try:
        os.startfile(music_dir)  # type: ignore[attr-defined]
        return get_response("play_music")
    except Exception:
        return "Unable to play music."


def stop_music_response() -> str:
    players = ["wmplayer.exe", "vlc.exe"]
    for player in players:
        os.system(f"taskkill /im {player} /f >nul 2>&1")
    return get_response("stop_music")
