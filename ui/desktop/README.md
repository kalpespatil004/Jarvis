# Desktop Avatar Video UI

This desktop UI uses real avatar videos from `assets/avatar/` and overlays subtitles on the video.

## Required avatar videos

Put these files in `assets/avatar/` (or `assets/avtar/`):

- `idle.mp4` (or `ideal.mp4` fallback)
- `listening.mp4` (or `listnimg.mp4` fallback)
- `thinking.mp4`
- `speaking.mp4`

## Run

```bash
python -m ui.desktop.app
# or compatibility alias:
python -m desktop.ui.app
```

## Behavior

- Window size is fixed to avatar video resolution (+ small controls strip at bottom).
- Avatar video occupies almost entire window.
- Avatar video audio is disabled entirely (no MP4 audio output is attached).
- Bottom panel includes only:
  - input box
  - `Listen` button
  - `Send` button
- Subtitles are shown on top of video near the bottom (forced overlay layer):
  - `You: <message>`
  - `Jarvis: <response>`
- State videos switch automatically for:
  - `idle`
  - `listening`
  - `thinking`
  - `speaking`

## Voice notes

- If microphone dependency is missing, app still opens and `Listen` shows a clear error.
- If TTS fails, subtitle shows a voice output error instead of crashing.

## Install hints

```bash
pip install -r requirement.txt
```

If needed:

```bash
pip install pyqt6 SpeechRecognition pyaudio
```

- If your screen stays black but file exists, check subtitle for `Video error:` (codec/backend issue).

- Desktop mode no longer loads voice-only dependencies (Vosk/TTS) at startup; these are imported lazily in voice loop paths.
