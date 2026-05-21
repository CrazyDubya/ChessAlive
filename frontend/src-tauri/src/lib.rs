// Lib.rs for Tauri v2
// This file may be needed for Tauri v2 apps

fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
