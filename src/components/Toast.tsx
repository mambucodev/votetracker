// Global toast stack — pinned bottom-right. Subscribes to the
// `sync-status` and `data-imported` backend events and surfaces them
// as toasts. Also renders any toast pushed via the `toast.*` helpers
// from `@/lib/hooks/useToast`.
//
// Backend events listened to here:
//   - "sync-status"    (tagged union — started/progress/done/failed)
//   - "data-imported"  ({ new, updated, skipped })

import { useEffect } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  X,
} from "lucide-react";
import { on } from "../lib/ipc";
import { EVENTS, type SyncStatusPayload } from "../lib/types";
import { useToast, type Toast } from "../lib/hooks/useToast";
import "./Toast.scss";

interface DataImportedPayload {
  new: number;
  updated: number;
  skipped: number;
}

const AUTO_DISMISS_MS = 4000;

function ToastIcon({ kind }: { kind: Toast["kind"] }) {
  switch (kind) {
    case "success":
      return <CheckCircle2 size={18} className="toast-icon" />;
    case "error":
    case "warn":
      return <AlertCircle size={18} className="toast-icon" />;
    case "progress":
      return (
        <Loader2 size={18} className="toast-icon toast-spin" />
      );
    case "info":
    default:
      return <CheckCircle2 size={18} className="toast-icon" />;
  }
}

function ToastItem({ t }: { t: Toast }) {
  const dismiss = useToast((s) => s.dismiss);

  useEffect(() => {
    if (t.sticky) return;
    const h = window.setTimeout(() => dismiss(t.id), AUTO_DISMISS_MS);
    return () => window.clearTimeout(h);
  }, [t.id, t.sticky, dismiss]);

  return (
    <div className={`toast toast--${t.kind}`} role="status">
      <ToastIcon kind={t.kind} />
      <div className="toast-message">{t.message}</div>
      <button
        type="button"
        className="toast-close"
        aria-label="Dismiss"
        onClick={() => dismiss(t.id)}
      >
        <X size={14} />
      </button>
    </div>
  );
}

/**
 * Single mount point for the toast stack. Subscribes to the two backend
 * events on mount and renders any toast in the Zustand store.
 */
export function ToastStack() {
  const toasts = useToast((s) => s.toasts);
  const push = useToast((s) => s.push);
  const dismiss = useToast((s) => s.dismiss);

  useEffect(() => {
    // Track the live progress toast per provider so "progress" updates
    // replace the previous one instead of stacking.
    const progressByProvider = new Map<string, number>();

    const clearProgress = (providerId: string) => {
      const prev = progressByProvider.get(providerId);
      if (prev !== undefined) {
        dismiss(prev);
        progressByProvider.delete(providerId);
      }
    };

    const u1 = on<SyncStatusPayload>(EVENTS.SYNC_STATUS, (p) => {
      switch (p.kind) {
        case "started": {
          clearProgress(p.provider_id);
          const id = push({
            kind: "progress",
            message: `Syncing ${p.provider_id}…`,
            sticky: true,
          });
          progressByProvider.set(p.provider_id, id);
          break;
        }
        case "progress": {
          clearProgress(p.provider_id);
          const id = push({
            kind: "progress",
            message: p.message,
            sticky: true,
          });
          progressByProvider.set(p.provider_id, id);
          break;
        }
        case "done": {
          clearProgress(p.provider_id);
          push({
            kind: "success",
            message: `${p.new_count} new, ${p.updated_count} updated (${p.skipped_count} skipped)`,
          });
          break;
        }
        case "failed": {
          clearProgress(p.provider_id);
          push({
            kind: "error",
            message: `Sync failed: ${p.message}`,
            sticky: true,
          });
          break;
        }
      }
    });

    const u2 = on<DataImportedPayload>(EVENTS.DATA_IMPORTED, (p) => {
      push({
        kind: "success",
        message: `${p.new} new, ${p.updated} updated (${p.skipped} skipped)`,
      });
    });

    return () => {
      u1.then((f) => f()).catch(() => undefined);
      u2.then((f) => f()).catch(() => undefined);
    };
  }, [push, dismiss]);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-stack" aria-live="polite" aria-atomic="false">
      {toasts.map((t) => (
        <ToastItem key={t.id} t={t} />
      ))}
    </div>
  );
}
