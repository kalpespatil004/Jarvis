use serde::Serialize;
use std::{process::Command, sync::Mutex};
use sysinfo::System;
use tauri::State;
use tauri_plugin_shell::{process::CommandChild, ShellExt};

struct BackendProcess(Mutex<Option<CommandChild>>);

#[derive(Serialize)]
struct SystemMetrics { cpu_usage: f32, ram_usage: u64, total_ram: u64 }

#[tauri::command]
fn system_metrics() -> SystemMetrics {
    let mut sys = System::new_all();
    sys.refresh_all();
    SystemMetrics { cpu_usage: sys.global_cpu_usage(), ram_usage: sys.used_memory(), total_ram: sys.total_memory() }
}

#[tauri::command]
async fn launch_backend(app: tauri::AppHandle, state: State<'_, BackendProcess>) -> Result<(), String> {
    let mut guard = state.0.lock().map_err(|_| "backend lock poisoned".to_string())?;
    if guard.is_some() { return Ok(()); }

    if let Ok((_, child)) = app.shell().sidecar("backend").map_err(|e| e.to_string())?.spawn() {
        *guard = Some(child);
        return Ok(());
    }

    #[cfg(debug_assertions)]
    {
        Command::new("python")
            .args(["-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"])
            .current_dir("../..")
            .spawn()
            .map_err(|e| format!("failed to launch development backend: {e}"))?;
        return Ok(());
    }

    #[allow(unreachable_code)]
    Err("backend sidecar could not be launched".to_string())
}

#[tauri::command]
fn stop_backend(state: State<'_, BackendProcess>) -> Result<(), String> {
    let mut guard = state.0.lock().map_err(|_| "backend lock poisoned".to_string())?;
    if let Some(child) = guard.take() { let _ = child.kill(); }
    Ok(())
}

pub fn run() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .invoke_handler(tauri::generate_handler![launch_backend, stop_backend, system_metrics])
        .run(tauri::generate_context!())
        .expect("error while running JARVIS desktop");
}
