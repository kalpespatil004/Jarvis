# Desktop Anime-Style UI: How to use in your project

This folder now contains a starter desktop UI where Jarvis has:

- a chat panel,
- an avatar panel,
- state transitions (`idle`, `thinking`, `speaking`),
- and non-blocking message processing with a worker thread.

## 1) Install dependencies

From the project root:

```bash
pip install -r requirement.txt
```

If PyQt install fails on your machine, install these directly:

```bash
pip install pyqt6 PyQt6-Qt6 PyQt6-sip
```

## 2) Start the desktop UI

From project root (`/workspace/Jarvis`):

```bash
python -m ui.desktop.app
```

You should see:

- left panel: avatar face + state text,
- right panel: chat log + input.

## 3) How message flow works

1. You type a message and press Enter / Send.
2. UI immediately appends your text.
3. UI state changes to `thinking`.
4. `process_text(...)` runs in `BrainWorker` on `QThread`.
5. Response is appended to chat.
6. Avatar changes to `speaking` briefly, then returns to `idle`.
7. Jarvis response is sent to `speak(...)` for voice playback.

## 4) Where to customize the avatar

Open `ui/desktop/main_window.py` and edit `self.avatar_map`:

- replace emoticons with your own text markers,
- or change the avatar widget to use `QPixmap` images for each state.

Good next step for anime style:

- add PNG assets (for example `idle.png`, `thinking.png`, `speaking1.png`, `speaking2.png`),
- swap image frames in `_animate_speaking`.

## 5) Connect real speech events (recommended)

Right now, speaking is timed in UI. For better realism, emit explicit events from TTS:

- `on_speak_start` -> set state `speaking`,
- `on_speak_end` -> set state `idle`.

Then your avatar motion matches actual audio playback.

## 6) Common issues

- **`ModuleNotFoundError: No module named 'PyQt6'`**  
  Install Qt dependencies with pip.

- **UI opens but no answers appear**  
  Verify `brain/process_text(...)` path and your model/API configs are working.

- **UI shows response but no voice output**  
  Make sure `sounddevice`, `soundfile`, and `TTS` are installed, and your system audio output device works.

- **UI freezes**  
  Keep long-running work off main thread (current worker-thread setup already does this).
