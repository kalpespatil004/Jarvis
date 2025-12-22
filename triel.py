from TTS.api import TTS
import sounddevice as sd
import soundfile as sf
import tempfile, os, time

# load model once
tts = TTS("tts_models/en/vctk/vits")

# how many speakers you want to test
SPEAKER_COUNT = 10   # change to 20, 30 if you want chaos

# test sentence (keep it same for fair comparison)
TEXT = "Hello sir. Systems are now online."

out = os.path.join(tempfile.gettempdir(), "voice_test.wav")

for i, speaker in enumerate(tts.speakers[:SPEAKER_COUNT]):
    print(f"\n[{i}] Speaker: {speaker}")

    tts.tts_to_file(
        text=TEXT,
        speaker=speaker,
        file_path=out
    )

    data, sr = sf.read(out)
    sd.play(data, sr)
    sd.wait()

    time.sleep(0.6)  # small pause so your brain resets
