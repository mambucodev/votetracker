import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type ThemePref = "system" | "light" | "dark";
type Resolved = "light" | "dark";

interface ThemeCtx {
  preference: ThemePref;
  resolved: Resolved;
  setPreference: (p: ThemePref) => void;
  toggle: () => void;
}

const Ctx = createContext<ThemeCtx | null>(null);
const STORAGE_KEY = "votetracker.theme";

function systemScheme(): Resolved {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function applyTheme(resolved: Resolved) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", resolved);
  document
    .querySelector('meta[name="color-scheme"]')
    ?.setAttribute("content", resolved === "dark" ? "dark light" : "light dark");
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePref>(() => {
    if (typeof localStorage === "undefined") return "system";
    const stored = localStorage.getItem(STORAGE_KEY) as ThemePref | null;
    return stored ?? "system";
  });

  const [system, setSystem] = useState<Resolved>(systemScheme);

  // Listen for OS-level theme changes.
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) =>
      setSystem(e.matches ? "dark" : "light");
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const resolved: Resolved = preference === "system" ? system : preference;

  useEffect(() => {
    applyTheme(resolved);
  }, [resolved]);

  const setPreference = useCallback((p: ThemePref) => {
    setPreferenceState(p);
    try {
      localStorage.setItem(STORAGE_KEY, p);
    } catch {
      /* ignore */
    }
  }, []);

  const toggle = useCallback(() => {
    setPreferenceState((prev) => {
      const next: ThemePref =
        prev === "system"
          ? systemScheme() === "dark"
            ? "light"
            : "dark"
          : prev === "dark"
            ? "light"
            : "dark";
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const value = useMemo<ThemeCtx>(
    () => ({ preference, resolved, setPreference, toggle }),
    [preference, resolved, setPreference, toggle],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTheme(): ThemeCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
