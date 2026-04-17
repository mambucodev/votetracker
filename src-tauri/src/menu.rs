//! Native menu bar. Built once at app start and attached to all windows.
//!
//! Each item emits a `menu://<name>` Tauri event that the React router
//! consumes. Accelerators mirror the shortcut matrix in docs/REWRITE_SPEC.md.

use tauri::menu::{AboutMetadata, Menu, MenuBuilder, MenuItemBuilder, PredefinedMenuItem, SubmenuBuilder};
use tauri::{AppHandle, Emitter, Runtime};

pub fn build<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<Menu<R>> {
    let file = SubmenuBuilder::new(app, "File")
        .item(
            &MenuItemBuilder::with_id("new-vote", "New Vote")
                .accelerator("CmdOrCtrl+N")
                .build(app)?,
        )
        .separator()
        .item(
            &MenuItemBuilder::with_id("import-json", "Import JSON…")
                .accelerator("CmdOrCtrl+I")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("export-json", "Export JSON…")
                .accelerator("CmdOrCtrl+E")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("export-pdf", "Export Report Card PDF")
                .build(app)?,
        )
        .separator()
        .item(&PredefinedMenuItem::close_window(app, None)?)
        .build()?;

    let edit = SubmenuBuilder::new(app, "Edit")
        .item(
            &MenuItemBuilder::with_id("undo", "Undo")
                .accelerator("CmdOrCtrl+Z")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("redo", "Redo")
                .accelerator("CmdOrCtrl+Shift+Z")
                .build(app)?,
        )
        .separator()
        .item(&PredefinedMenuItem::cut(app, None)?)
        .item(&PredefinedMenuItem::copy(app, None)?)
        .item(&PredefinedMenuItem::paste(app, None)?)
        .item(&PredefinedMenuItem::select_all(app, None)?)
        .build()?;

    let view = SubmenuBuilder::new(app, "View")
        .item(
            &MenuItemBuilder::with_id("nav-dashboard", "Dashboard")
                .accelerator("CmdOrCtrl+1")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("nav-votes", "Votes")
                .accelerator("CmdOrCtrl+2")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("nav-subjects", "Subjects")
                .accelerator("CmdOrCtrl+3")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("nav-simulator", "Simulator")
                .accelerator("CmdOrCtrl+4")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("nav-calendar", "Calendar")
                .accelerator("CmdOrCtrl+5")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("nav-report-card", "Report Card")
                .accelerator("CmdOrCtrl+6")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("nav-statistics", "Statistics")
                .accelerator("CmdOrCtrl+7")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("nav-settings", "Settings")
                .accelerator("CmdOrCtrl+8")
                .build(app)?,
        )
        .separator()
        .item(
            &MenuItemBuilder::with_id("toggle-theme", "Toggle Theme")
                .accelerator("CmdOrCtrl+Shift+T")
                .build(app)?,
        )
        .build()?;

    let sync = SubmenuBuilder::new(app, "Sync")
        .item(
            &MenuItemBuilder::with_id("sync-now", "Sync Now")
                .accelerator("CmdOrCtrl+R")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("sync-configure", "Configure Providers…")
                .build(app)?,
        )
        .build()?;

    let help = SubmenuBuilder::new(app, "Help")
        .item(
            &MenuItemBuilder::with_id("shortcuts", "Keyboard Shortcuts")
                .accelerator("?")
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("open-data-folder", "Open Data Folder")
                .build(app)?,
        )
        .separator()
        .item(&PredefinedMenuItem::about(
            app,
            Some("About VoteTracker"),
            Some(AboutMetadata {
                name: Some("VoteTracker".into()),
                version: Some(env!("CARGO_PKG_VERSION").into()),
                ..Default::default()
            }),
        )?)
        .build()?;

    MenuBuilder::new(app)
        .items(&[&file, &edit, &view, &sync, &help])
        .build()
}

/// Forward every menu click to the frontend as a `menu://{id}` event.
pub fn bind<R: Runtime>(app: &AppHandle<R>) {
    app.on_menu_event(|app, event| {
        let id = event.id().as_ref().to_string();
        let _ = app.emit(&format!("menu://{id}"), ());
    });
}
