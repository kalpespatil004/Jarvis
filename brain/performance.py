from __future__ import annotations


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    return f"{seconds:.2f}s"


def log_stage(stage: str, seconds: float) -> None:
    print(f"[{stage}] {format_duration(seconds)}")
