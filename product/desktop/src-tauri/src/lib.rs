// The desktop app is a native window around the static web app in ../dist.
// It needs no Rust commands: data, routing and the checklist store all live in the page.
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running Market Window Dossier");
}
