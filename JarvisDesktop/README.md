# JARVIS Desktop

A production-oriented Tauri v2 desktop shell for the existing JARVIS FastAPI backend. The frontend contains no AI logic: it launches or connects to the Python sidecar, waits for FastAPI health, and communicates by REST.

## Development

```bash
npm install
npm run tauri:dev
```

During development, if a sidecar is unavailable, the Rust backend command starts `python -m uvicorn api.main:app --host 127.0.0.1 --port 8000` from the repository root.

## Production

1. Package the existing Python FastAPI service as `python/backend.exe` for Windows or `python/backend` for Linux/macOS.
2. Run `npm run tauri:build`.
3. Windows installer targets are configured for MSI and NSIS with a desktop shortcut-capable installer profile.

Runtime user data should be kept under `%LOCALAPPDATA%/Jarvis` by the backend and any future store integrations. Do not write mutable data into Program Files.
