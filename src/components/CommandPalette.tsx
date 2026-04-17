import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";
import { invoke } from "@tauri-apps/api/core";
import {
  BarChart3,
  BookOpen,
  Calculator,
  Calendar,
  FileText,
  FolderOpen,
  LayoutDashboard,
  ListChecks,
  Moon,
  Plus,
  RefreshCw,
  Search,
  Settings as SettingsIcon,
} from "lucide-react";
import { listSubjects } from "@/lib/ipc";
import { useCommandPalette } from "@/lib/hooks/useCommandPalette";
import "./CommandPalette.scss";

type Group = "Pages" | "Subjects" | "Actions";

interface Item {
  id: string;
  group: Group;
  label: string;
  hint?: string;
  icon: ReactNode;
  run: () => void;
}

const PAGES: Array<{
  label: string;
  to: string;
  icon: ReactNode;
}> = [
  { label: "Dashboard", to: "/", icon: <LayoutDashboard size={16} /> },
  { label: "Votes", to: "/votes", icon: <ListChecks size={16} /> },
  { label: "Subjects", to: "/subjects", icon: <BookOpen size={16} /> },
  { label: "Simulator", to: "/simulator", icon: <Calculator size={16} /> },
  { label: "Calendar", to: "/calendar", icon: <Calendar size={16} /> },
  { label: "Report Card", to: "/report-card", icon: <FileText size={16} /> },
  { label: "Statistics", to: "/statistics", icon: <BarChart3 size={16} /> },
  { label: "Settings", to: "/settings", icon: <SettingsIcon size={16} /> },
];

export function CommandPalette() {
  const { open, closePalette } = useCommandPalette();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);
  const [subjects, setSubjects] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Reset state and focus the input every time the palette opens.
  useEffect(() => {
    if (!open) return;
    setQuery("");
    setCursor(0);
    const t = window.setTimeout(() => inputRef.current?.focus(), 0);
    listSubjects()
      .then(setSubjects)
      .catch(() => setSubjects([]));
    return () => window.clearTimeout(t);
  }, [open]);

  // Close on Esc.
  useEffect(() => {
    if (!open) return;
    function onKey(e: globalThis.KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        closePalette();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, closePalette]);

  const items: Item[] = useMemo(() => {
    const pageItems: Item[] = PAGES.map((p) => ({
      id: `page:${p.to}`,
      group: "Pages",
      label: p.label,
      icon: p.icon,
      run: () => navigate(p.to),
    }));

    const subjectItems: Item[] = subjects.map((name) => ({
      id: `subject:${name}`,
      group: "Subjects",
      label: name,
      hint: "Open in Votes",
      icon: <BookOpen size={16} />,
      run: () => navigate(`/votes?subject=${encodeURIComponent(name)}`),
    }));

    const actionItems: Item[] = [
      {
        id: "action:new-vote",
        group: "Actions",
        label: "New vote",
        hint: "Ctrl+N",
        icon: <Plus size={16} />,
        run: () =>
          window.dispatchEvent(new CustomEvent("vt:new-vote")),
      },
      {
        id: "action:sync-now",
        group: "Actions",
        label: "Sync now",
        hint: "Ctrl+R",
        icon: <RefreshCw size={16} />,
        run: () =>
          window.dispatchEvent(new CustomEvent("vt:sync-now")),
      },
      {
        id: "action:toggle-theme",
        group: "Actions",
        label: "Toggle theme",
        hint: "Ctrl+Shift+T",
        icon: <Moon size={16} />,
        run: () =>
          window.dispatchEvent(new CustomEvent("vt:toggle-theme")),
      },
      {
        id: "action:open-data-dir",
        group: "Actions",
        label: "Open data folder",
        icon: <FolderOpen size={16} />,
        run: () => {
          invoke("open_data_dir").catch(() => {
            /* ignore — backend may log */
          });
        },
      },
      {
        id: "action:export-report-card",
        group: "Actions",
        label: "Export report card",
        icon: <FileText size={16} />,
        run: () => navigate("/report-card"),
      },
    ];

    return [...pageItems, ...subjectItems, ...actionItems];
  }, [subjects, navigate]);

  const filtered: Item[] = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((it) => it.label.toLowerCase().includes(q));
  }, [items, query]);

  // Group contiguous items by their group for rendering. We keep input
  // order, so the order is Pages → Subjects → Actions when nothing is
  // filtered out.
  const grouped: Array<{ group: Group; items: Item[] }> = useMemo(() => {
    const out: Array<{ group: Group; items: Item[] }> = [];
    for (const it of filtered) {
      const last = out[out.length - 1];
      if (last && last.group === it.group) {
        last.items.push(it);
      } else {
        out.push({ group: it.group, items: [it] });
      }
    }
    return out;
  }, [filtered]);

  // Clamp cursor when filter changes.
  useEffect(() => {
    setCursor((c) => Math.min(Math.max(0, c), Math.max(0, filtered.length - 1)));
  }, [filtered.length]);

  function activate(index: number) {
    const item = filtered[index];
    if (!item) return;
    closePalette();
    // Defer so state updates flush before route change / side-effects.
    queueMicrotask(() => item.run());
  }

  function onInputKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setCursor((c) => Math.min(filtered.length - 1, c + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setCursor((c) => Math.max(0, c - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      activate(cursor);
    }
  }

  // Scroll active item into view when cursor moves.
  useEffect(() => {
    const root = listRef.current;
    if (!root) return;
    const el = root.querySelector<HTMLElement>(
      ".command-palette__item--active",
    );
    el?.scrollIntoView({ block: "nearest" });
  }, [cursor, filtered.length]);

  if (!open) return null;

  // Flat index so hovering/clicking an item knows its absolute position
  // in `filtered` (needed because rendering is grouped).
  let flatIndex = -1;

  return (
    <div className="command-palette-backdrop" onMouseDown={closePalette}>
      <div
        className="command-palette"
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="command-palette__input-wrap">
          <Search size={16} />
          <input
            ref={inputRef}
            className="command-palette__input"
            placeholder="Search pages, subjects, actions..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setCursor(0);
            }}
            onKeyDown={onInputKeyDown}
            aria-label="Command palette search"
          />
        </div>

        <div className="command-palette__list" ref={listRef}>
          {filtered.length === 0 && (
            <div className="command-palette__empty">No results</div>
          )}

          {grouped.map(({ group, items: groupItems }) => (
            <div key={group}>
              <div className="command-palette__group-title">{group}</div>
              {groupItems.map((it) => {
                flatIndex += 1;
                const active = flatIndex === cursor;
                const myIndex = flatIndex;
                return (
                  <button
                    key={it.id}
                    type="button"
                    className={
                      "command-palette__item" +
                      (active ? " command-palette__item--active" : "")
                    }
                    onMouseEnter={() => setCursor(myIndex)}
                    onClick={() => activate(myIndex)}
                  >
                    {it.icon}
                    <span className="command-palette__item-label">
                      {it.label}
                    </span>
                    {it.hint && (
                      <span className="command-palette__item-hint">
                        {it.hint}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
