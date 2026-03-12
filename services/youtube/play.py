"""
play.py
--------
Play a YouTube video in the browser
"""

import webbrowser
import urllib.parse


def play_video(video: str, open_browser: bool = True) -> dict:
    """
    Play a YouTube video using URL or video ID.

    Args:
        video (str): Full YouTube URL or video ID
        open_browser (bool): Open browser or not

    Returns:
        dict: Play status
    """

    if not video or not isinstance(video, str):
        return {
            "success": False,
            "error": "Invalid video input"
        }

    # If full URL is provided
    if video.startswith("http"):
        video_url = video
    else:
        # Treat input as video ID
        encoded_id = urllib.parse.quote_plus(video.strip())
        video_url = f"https://www.youtube.com/watch?v={encoded_id}"

    try:
        if open_browser:
            webbrowser.open(video_url)

        return {
            "success": True,
            "video": video,
            "url": video_url,
            "message": "▶ Playing YouTube video"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
