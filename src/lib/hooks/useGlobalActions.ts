// Central listener for the `vt:*` CustomEvents emitted by both the
// keyboard shortcut handler (`useShortcuts`) and the native-menu event
// router (`useMenuEvents`). This is the single source of truth for
// what "New vote", "Import JSON", "Export JSON", "Export PDF" and
// "Sync now" actually do — without it, those events fire into the
// void and the keybinds appear broken.

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { invoke } from "@tauri-apps/api/core";
import { open as openDialog, save } from "@tauri-apps/plugin-dialog";
import { readTextFile, writeTextFile } from "@tauri-apps/plugin-fs";
import {
  getSetting,
  listSubjects,
  listVotes,
} from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useToast } from "@/lib/hooks/useToast";

interface ProviderInfo {
  id: string;
  name: string;
  fields: { name: string }[];
}

async function importJson(push: (t: { kind: "success" | "error"; message: string }) => void) {
  try {
    const path = await openDialog({
      multiple: false,
      filters: [{ name: "JSON", extensions: ["json"] }],
    });
    if (!path || Array.isArray(path)) return;
    const content = await readTextFile(path);
    const parsed = JSON.parse(content);
    const list = Array.isArray(parsed)
      ? parsed
      : (parsed.votes ?? parsed.voti ?? []);
    const result = await invoke<{
      new_count: number;
      updated_count: number;
      skipped_count: number;
    }>("import_votes_json", { records: list });
    push({
      kind: "success",
      message: `${result.new_count} new, ${result.updated_count} updated (${result.skipped_count} skipped)`,
    });
  } catch (e) {
    push({ kind: "error", message: `Import failed: ${e}` });
  }
}

async function exportJson(push: (t: { kind: "success" | "error"; message: string }) => void) {
  try {
    const path = await save({
      defaultPath: "votetracker-export.json",
      filters: [{ name: "JSON", extensions: ["json"] }],
    });
    if (!path) return;
    const votes = await listVotes({});
    const subjects = await listSubjects();
    const doc = {
      version: "3.0",
      subjects,
      votes: votes.map((v) => ({
        subject: v.subject,
        grade: v.grade,
        type: v.type,
        term: v.term,
        date: v.date,
        description: v.description,
        weight: v.weight,
      })),
    };
    await writeTextFile(path, JSON.stringify(doc, null, 2));
    push({ kind: "success", message: "Export complete" });
  } catch (e) {
    push({ kind: "error", message: `Export failed: ${e}` });
  }
}

async function syncAll(push: (t: { kind: "success" | "error"; message: string }) => void) {
  try {
    const providers = await invoke<ProviderInfo[]>("list_providers");
    let triggered = 0;
    for (const p of providers) {
      // Only sync providers with at least one credential saved — skip
      // the rest silently (matches the behavior of startup auto-sync).
      let configured = false;
      for (const f of p.fields) {
        const v = await getSetting(`${p.id}_${f.name}`);
        if (v) {
          configured = true;
          break;
        }
      }
      if (!configured) continue;
      // Fire-and-forget — backend emits sync-status toasts itself.
      invoke("trigger_sync_now", { providerId: p.id }).catch(() => {});
      triggered += 1;
    }
    if (triggered === 0) {
      push({
        kind: "error",
        message: "No provider configured — open Settings to set credentials",
      });
    }
  } catch (e) {
    push({ kind: "error", message: `Sync failed: ${e}` });
  }
}

export function useGlobalActions() {
  const navigate = useNavigate();
  const requestNewVote = useApp((s) => s.requestNewVote);
  const requestExportPdf = useApp((s) => s.requestExportPdf);
  const toastPush = useToast((s) => s.push);

  useEffect(() => {
    const push = (t: { kind: "success" | "error"; message: string }) =>
      toastPush(t);

    const onNewVote = () => {
      if (window.location.pathname !== "/votes") navigate("/votes");
      requestNewVote();
    };
    const onImport = () => {
      void importJson(push);
    };
    const onExport = () => {
      void exportJson(push);
    };
    const onExportPdf = () => {
      if (window.location.pathname !== "/report-card") navigate("/report-card");
      requestExportPdf();
    };
    const onSync = () => {
      void syncAll(push);
    };

    window.addEventListener("vt:new-vote", onNewVote);
    window.addEventListener("vt:import-json", onImport);
    window.addEventListener("vt:export-json", onExport);
    window.addEventListener("vt:export-pdf", onExportPdf);
    window.addEventListener("vt:sync-now", onSync);
    return () => {
      window.removeEventListener("vt:new-vote", onNewVote);
      window.removeEventListener("vt:import-json", onImport);
      window.removeEventListener("vt:export-json", onExport);
      window.removeEventListener("vt:export-pdf", onExportPdf);
      window.removeEventListener("vt:sync-now", onSync);
    };
  }, [navigate, requestNewVote, requestExportPdf, toastPush]);
}
