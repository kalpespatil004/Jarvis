import os
import tempfile
import sounddevice as sd
import soundfile as sf
from TTS.api import TTS

# Load model ONCE at startup (important for speed)
_tts = TTS("tts_models/en/vctk/vits")
_JARVIS_SPEAKER = "p230"   # your chosen voice

def speak(text: str, verbose: bool = True):
    """
    Offline TTS using Coqui TTS.
    Fixed male Jarvis voice: p230
    """

    if not text or not text.strip():
        return

    if verbose:
        print(f"Jarvis: {text}")

    # temp wav file
    out_path = os.path.join(
        tempfile.gettempdir(),
        "jarvis_voice.wav"
    )

    # generate speech
    _tts.tts_to_file(
        text=text,
        speaker=_JARVIS_SPEAKER,
        file_path=out_path
    )

    # play audio
    data, sr = sf.read(out_path)
    sd.play(data, sr)
    sd.wait()


speak("Good evening, sir. All systems are online.")