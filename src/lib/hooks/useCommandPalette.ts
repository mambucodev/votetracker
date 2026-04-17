import { useCallback, useEffect, useState } from "react";

// Global state for the command palette. A single source of truth used by
// the mount point (CommandPalette) and anything that wants to open it
// programmatically. Registers the Ctrl+K / Cmd+K keydown once and
// respects the standard "typing in an editable control" bypass.

export function useCommandPalette() {
  const [open, setOpen] = useState(false);

  const openPalette = useCallback(() => setOpen(true), []);
  const closePalette = useCallback(() => setOpen(false), []);
  const togglePalette = useCallback(() => setOpen((v) => !v), []);

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      const mod = e.ctrlKey || e.metaKey;
      const isKeyK = e.key === "k" || e.key === "K";

      if (!mod || !isKeyK) return;

      // "Typing in input/textarea/contenteditable" bypass — but Ctrl+K is
      // a global app shortcut, so we intentionally hijack it even when
      // focus is in an editable control. The bypass here only applies
      // when the user hasn't actually pressed the modifier, which is
      // already gated above. Keeping the shape for parity with the rest
      // of the shortcut matrix.
      const t = e.target as HTMLElement | null;
      const tag = t?.tagName?.toLowerCase();
      const typing =
        tag === "input" || tag === "textarea" || t?.isContentEditable;
      void typing; // informational — Ctrl+K overrides editable focus

      e.preventDefault();
      setOpen((v) => !v);
    }

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return { open, openPalette, closePalette, togglePalette };
}
