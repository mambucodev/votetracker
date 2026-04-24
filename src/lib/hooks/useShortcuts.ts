import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { redo, setCurrentTerm, undo } from "../ipc";
import { useApp } from "../store";
import { useTheme } from "@/theme/ThemeProvider";

const ROUTES = [
  "/",
  "/votes",
  "/subjects",
  "/simulator",
  "/calendar",
  "/report-card",
  "/statistics",
  "/settings",
];

export function useShortcuts() {
  const navigate = useNavigate();
  const { toggle } = useTheme();

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      // Skip typing into inputs
      const t = e.target as HTMLElement | null;
      const tag = t?.tagName?.toLowerCase();
      const typing =
        tag === "input" || tag === "textarea" || t?.isContentEditable;

      const mod = e.ctrlKey || e.metaKey;
      const key = e.key.toLowerCase();

      if (!typing && e.key === "?") {
        window.dispatchEvent(new CustomEvent("vt:shortcuts-help"));
        e.preventDefault();
        return;
      }

      if (mod && e.key >= "1" && e.key <= "8") {
        navigate(ROUTES[parseInt(e.key, 10) - 1]);
        e.preventDefault();
        return;
      }

      // Bare "1" / "2" — switch term (ignored while typing or with modifiers).
      if (!typing && !mod && (e.key === "1" || e.key === "2")) {
        const t = e.key === "1" ? 1 : 2;
        useApp.getState().setTerm(t);
        setCurrentTerm(t).catch(() => {});
        e.preventDefault();
        return;
      }

      if (!typing && e.key === "PageDown") {
        const idx = ROUTES.indexOf(window.location.pathname);
        navigate(ROUTES[(idx + 1) % ROUTES.length] ?? "/");
        e.preventDefault();
      }
      if (!typing && e.key === "PageUp") {
        const idx = ROUTES.indexOf(window.location.pathname);
        navigate(ROUTES[(idx - 1 + ROUTES.length) % ROUTES.length] ?? "/");
        e.preventDefault();
      }

      if (mod && !e.shiftKey && key === "z") {
        undo().catch(() => {});
        e.preventDefault();
        return;
      }
      if (
        (mod && e.shiftKey && key === "z") ||
        (mod && key === "y")
      ) {
        redo().catch(() => {});
        e.preventDefault();
        return;
      }

      if (mod && e.shiftKey && key === "t") {
        toggle();
        e.preventDefault();
        return;
      }

      // Ctrl+N — new vote (works anywhere)
      if (mod && !e.shiftKey && key === "n") {
        window.dispatchEvent(new CustomEvent("vt:new-vote"));
        e.preventDefault();
        return;
      }

      // Ctrl+I — import JSON (route to settings, then dispatch)
      if (mod && !e.shiftKey && key === "i") {
        if (window.location.pathname !== "/settings") navigate("/settings");
        window.dispatchEvent(new CustomEvent("vt:import-json"));
        e.preventDefault();
        return;
      }

      // Ctrl+E — export JSON (route to settings, then dispatch)
      if (mod && !e.shiftKey && key === "e") {
        if (window.location.pathname !== "/settings") navigate("/settings");
        window.dispatchEvent(new CustomEvent("vt:export-json"));
        e.preventDefault();
        return;
      }

      // Ctrl+R — sync now (preventDefault to override webview reload)
      if (mod && !e.shiftKey && key === "r") {
        window.dispatchEvent(new CustomEvent("vt:sync-now"));
        e.preventDefault();
        return;
      }
    }

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [navigate, toggle]);
}
