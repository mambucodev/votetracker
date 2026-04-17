import { NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  ClipboardList,
  BookOpen,
  Calculator,
  CalendarDays,
  FileText,
  BarChart3,
  Settings as SettingsIcon,
  Sun,
  Moon,
} from "lucide-react";
import { activeYear, listYears, setActiveYear } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useTheme } from "@/theme/ThemeProvider";
import type { SchoolYear } from "@/lib/types";
import { tr } from "@/lib/i18n";
import "./Sidebar.scss";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/votes", label: "Votes", icon: ClipboardList },
  { to: "/subjects", label: "Subjects", icon: BookOpen },
  { to: "/simulator", label: "Simulator", icon: Calculator },
  { to: "/calendar", label: "Calendar", icon: CalendarDays },
  { to: "/report-card", label: "Report Card", icon: FileText },
  { to: "/statistics", label: "Statistics", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

export function Sidebar() {
  const [years, setYears] = useState<SchoolYear[]>([]);
  const { year, setYear } = useApp();
  const { resolved, toggle } = useTheme();

  useEffect(() => {
    (async () => {
      const list = await listYears();
      setYears(list);
      setYear(await activeYear());
    })().catch(console.error);
  }, [setYear]);

  async function onYearChange(id: number) {
    await setActiveYear(id);
    const next = years.find((y) => y.id === id);
    if (next) setYear(next);
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark" />
        <div>
          <div className="brand-name">VoteTracker</div>
          <div className="brand-version">v3.0</div>
        </div>
      </div>

      <nav className="nav">
        {NAV.map((item) => {
          const IconComponent = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
            >
              <IconComponent size={16} strokeWidth={1.75} />
              <span>{tr(item.label)}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <label className="year-select">
          <span>{tr("School Years")}</span>
          <select
            value={year?.id ?? ""}
            onChange={(e) => onYearChange(Number(e.target.value))}
          >
            {years.map((y) => (
              <option key={y.id} value={y.id}>
                {y.name}
              </option>
            ))}
          </select>
        </label>
        <button
          className="theme-toggle"
          onClick={toggle}
          title={tr("Theme")}
          aria-label="Toggle theme"
        >
          {resolved === "dark" ? <Moon size={14} /> : <Sun size={14} />}
        </button>
      </div>
    </aside>
  );
}
