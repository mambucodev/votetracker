import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { redo, undo } from "../ipc";
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

      if (mod && !e.shiftKey && e.key.toLowerCase() === "z") {
        undo().catch(() => {});
        e.preventDefault();
      }
      if (
        (mod && e.shiftKey && e.key.toLowerCase() === "z") ||
        (mod && e.key.toLowerCase() === "y")
      ) {
        redo().catch(() => {});
        e.preventDefault();
      }

      if (mod && e.shiftKey && e.key.toLowerCase() === "t") {
        toggle();
        e.preventDefault();
      }
    }

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [navigate, toggle]);
}
