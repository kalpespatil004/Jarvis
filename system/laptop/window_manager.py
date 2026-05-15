from __future__ import annotations

from typing import Any

import pyautogui
import pygetwindow as gw


# ---------------------------
# ACTION PAYLOADS / TARGETS
# ---------------------------

def _action_payload(
    *,
    success: bool,
    entity_type: str = "window",
    entity_id: str | None = None,
    entity_label: str | None = None,
    action: str,
    error: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "success": success,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_label": entity_label,
        "action": action,
    }
    if error:
        payload["error"] = error
    return payload


def _window_payload(window: Any, *, success: bool, action: str, error: str | None = None) -> dict[str, Any]:
    title = str(getattr(window, "title", "") or "").strip() or None
    return _action_payload(
        success=success,
        entity_id=title,
        entity_label=title,
        action=action,
        error=error,
    )


def _target_label(target: dict[str, Any] | str | None) -> str | None:
    if target is None:
        return None
    if isinstance(target, str):
        return target.strip() or None
    for key in ("entity_label", "entity_id", "name", "app", "title"):
        value = target.get(key)
        if value:
            return str(value).strip() or None
    return None


def _resolve_window(target: dict[str, Any] | str | None = None):
    label = _target_label(target)
    if label:
        windows = gw.getWindowsWithTitle(label)
        if windows:
            return windows[0]
    return get_active_window()


# ---------------------------
# GET ACTIVE WINDOW
# ---------------------------

def get_active_window():
    """
    Get currently active window
    """
    try:
        return gw.getActiveWindow()
    except Exception:
        return None


# ---------------------------
# MINIMIZE WINDOW
# ---------------------------

def minimize_window(target: dict[str, Any] | str | None = None) -> dict[str, Any]:
    """
    Minimize a target window, or the active window when no target is provided.
    """
    try:
        window = _resolve_window(target)
        if window:
            window.minimize()
            return _window_payload(window, success=True, action="minimize")
        label = _target_label(target)
        return _action_payload(
            success=False,
            entity_id=label,
            entity_label=label,
            action="minimize",
            error="No matching active window found" if label else "No active window found",
        )
    except Exception as e:
        label = _target_label(target)
        return _action_payload(
            success=False,
            entity_id=label,
            entity_label=label,
            action="minimize",
            error=str(e),
        )


# ---------------------------
# MAXIMIZE WINDOW
# ---------------------------

def maximize_window(target: dict[str, Any] | str | None = None) -> dict[str, Any]:
    """
    Maximize a target window, or the active window when no target is provided.
    """
    try:
        window = _resolve_window(target)
        if window:
            window.maximize()
            return _window_payload(window, success=True, action="maximize")
        label = _target_label(target)
        return _action_payload(
            success=False,
            entity_id=label,
            entity_label=label,
            action="maximize",
            error="No matching active window found" if label else "No active window found",
        )
    except Exception as e:
        label = _target_label(target)
        return _action_payload(
            success=False,
            entity_id=label,
            entity_label=label,
            action="maximize",
            error=str(e),
        )


# ---------------------------
# RESTORE WINDOW
# ---------------------------

def restore_window() -> dict[str, Any]:
    """
    Restore minimized window
    """
    try:
        window = get_active_window()
        if window:
            window.restore()
            return _window_payload(window, success=True, action="restore")
        return _action_payload(success=False, action="restore", error="No active window found")
    except Exception as e:
        return _action_payload(success=False, action="restore", error=str(e))


# ---------------------------
# CLOSE WINDOW
# ---------------------------

def close_window() -> dict[str, Any]:
    """
    Close active window
    """
    try:
        window = get_active_window()
        pyautogui.hotkey("alt", "f4")
        if window:
            return _window_payload(window, success=True, action="close")
        return _action_payload(success=True, action="close")
    except Exception as e:
        return _action_payload(success=False, action="close", error=str(e))


# ---------------------------
# FOCUS WINDOW BY NAME
# ---------------------------

def focus_window(app_name: str | None = None, target: dict[str, Any] | str | None = None) -> dict[str, Any]:
    """
    Focus a window using an explicit app name, target entity, or active window.
    """
    try:
        resolved_target = target if target is not None else app_name
        window = _resolve_window(resolved_target)
        if window:
            window.activate()
            return _window_payload(window, success=True, action="focus")
        label = _target_label(resolved_target)
        return _action_payload(
            success=False,
            entity_id=label,
            entity_label=label,
            action="focus",
            error=f"No window found with name '{label}'" if label else "No active window found",
        )
    except Exception as e:
        label = _target_label(target if target is not None else app_name)
        return _action_payload(
            success=False,
            entity_id=label,
            entity_label=label,
            action="focus",
            error=str(e),
        )


# ---------------------------
# MOVE WINDOW
# ---------------------------

def move_window(x=100, y=100) -> dict[str, Any]:
    """
    Move active window
    """
    try:
        window = get_active_window()
        if window:
            window.moveTo(x, y)
            payload = _window_payload(window, success=True, action="move")
            payload["position"] = {"x": x, "y": y}
            return payload
        return _action_payload(success=False, action="move", error="No active window found")
    except Exception as e:
        return _action_payload(success=False, action="move", error=str(e))


# ---------------------------
# RESIZE WINDOW
# ---------------------------

def resize_window(width=800, height=600) -> dict[str, Any]:
    """
    Resize active window
    """
    try:
        window = get_active_window()
        if window:
            window.resizeTo(width, height)
            payload = _window_payload(window, success=True, action="resize")
            payload["size"] = {"width": width, "height": height}
            return payload
        return _action_payload(success=False, action="resize", error="No active window found")
    except Exception as e:
        return _action_payload(success=False, action="resize", error=str(e))


if __name__ == "__main__":
    import time
    time.sleep(5)
    print(get_active_window())
    time.sleep(5)
    print(maximize_window())
    time.sleep(5)
    print(minimize_window())
    time.sleep(5)
    print(restore_window())
    time.sleep(5)
    print(focus_window("Chrome"))
    time.sleep(5)
    print(move_window(100, 100))
    time.sleep(5)
    print(resize_window(800, 600))
    time.sleep(5)
    print(close_window())
