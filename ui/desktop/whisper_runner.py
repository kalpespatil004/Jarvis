from __future__ import annotations

import sys

from ui.desktop.voice_input import WHISPER_ERROR_PREFIX, WHISPER_RESULT_PREFIX


def main() -> int:
    try:
        from body.listen_whisper import listen

        text = listen(duration=5) or ""
        print(f"{WHISPER_RESULT_PREFIX}{text}", flush=True)
        return 0
    except BaseException as exc:
        print(f"{WHISPER_ERROR_PREFIX}{exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
