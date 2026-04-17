// Zustand store for the global toast stack. Other code can push toasts
// either via the hook (inside React) or via the `toast.*` helpers
// (from anywhere, including outside the React tree).

import { create } from "zustand";

export type ToastKind = "info" | "success" | "warn" | "error" | "progress";

export interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
  /** If true, the toast stays until the user dismisses it. */
  sticky?: boolean;
}

interface ToastState {
  toasts: Toast[];
  push: (t: Omit<Toast, "id">) => number;
  dismiss: (id: number) => void;
}

let nextId = 1;

export const useToast = create<ToastState>((set) => ({
  toasts: [],
  push: (t) => {
    const id = nextId++;
    set((s) => ({ toasts: [...s.toasts, { ...t, id }] }));
    return id;
  },
  dismiss: (id) =>
    set((s) => ({ toasts: s.toasts.filter((x) => x.id !== id) })),
}));

// Public helper — callable from anywhere.
export const toast = {
  info: (message: string) =>
    useToast.getState().push({ kind: "info", message }),
  success: (message: string) =>
    useToast.getState().push({ kind: "success", message }),
  warn: (message: string) =>
    useToast.getState().push({ kind: "warn", message }),
  error: (message: string) =>
    useToast.getState().push({ kind: "error", message, sticky: true }),
  progress: (message: string) =>
    useToast.getState().push({ kind: "progress", message, sticky: true }),
  dismiss: (id: number) => useToast.getState().dismiss(id),
};
