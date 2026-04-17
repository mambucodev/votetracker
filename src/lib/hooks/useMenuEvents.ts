// Subscribes to every `menu://<id>` event emitted by the native menu in
// `src-tauri/src/menu.rs` and re-dispatches it as the matching `vt:*`
// window event (so React components listen to a single surface).
//
// Undo/redo are handled here directly via the IPC wrappers.
// `open-data-folder` invokes the Tauri command.
// Navigation items are mapped to the corresponding route.

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import { redo, undo } from "../ipc";

type Dispatch =
  | { kind: "event"; name: string }
  | { kind: "navigate"; to: string }
  | { kind: "undo" }
  | { kind: "redo" }
  | { kind: "invoke"; cmd: string };

const TABLE: Record<string, Dispatch> = {
  "new-vote": { kind: "event", name: "vt:new-vote" },
  "import-json": { kind: "event", name: "vt:import-json" },
  "export-json": { kind: "event", name: "vt:export-json" },
  "export-pdf": { kind: "event", name: "vt:export-pdf" },
  undo: { kind: "undo" },
  redo: { kind: "redo" },
  "nav-dashboard": { kind: "navigate", to: "/" },
  "nav-votes": { kind: "navigate", to: "/votes" },
  "nav-subjects": { kind: "navigate", to: "/subjects" },
  "nav-simulator": { kind: "navigate", to: "/simulator" },
  "nav-calendar": { kind: "navigate", to: "/calendar" },
  "nav-report-card": { kind: "navigate", to: "/report-card" },
  "nav-statistics": { kind: "navigate", to: "/statistics" },
  "nav-settings": { kind: "navigate", to: "/settings" },
  "toggle-theme": { kind: "event", name: "vt:toggle-theme" },
  "sync-now": { kind: "event", name: "vt:sync-now" },
  shortcuts: { kind: "event", name: "vt:shortcuts-help" },
  "open-data-folder": { kind: "invoke", cmd: "open_data_dir" },
  "sync-configure": { kind: "navigate", to: "/settings" },
};

export function useMenuEvents() {
  const navigate = useNavigate();

  useEffect(() => {
    const unlisteners: UnlistenFn[] = [];
    let cancelled = false;

    (async () => {
      for (const [id, d] of Object.entries(TABLE)) {
        const un = await listen(`menu://${id}`, () => {
          switch (d.kind) {
            case "event":
              window.dispatchEvent(new CustomEvent(d.name));
              break;
            case "navigate":
              navigate(d.to);
              break;
            case "undo":
              undo().catch(() => {});
              break;
            case "redo":
              redo().catch(() => {});
              break;
            case "invoke":
              invoke(d.cmd).catch(() => {});
              break;
          }
        });
        if (cancelled) {
          un();
        } else {
          unlisteners.push(un);
        }
      }
    })().catch(console.error);

    return () => {
      cancelled = true;
      for (const un of unlisteners) un();
    };
  }, [navigate]);
}
