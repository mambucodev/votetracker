import { NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import { activeYear, listYears, setActiveYear } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useTheme } from "@/theme/ThemeProvider";
import type { SchoolYear } from "@/lib/types";
import { tr } from "@/lib/i18n";
import "./Sidebar.scss";

const NAV = [
  { to: "/", label: "Dashboard" },
  { to: "/votes", label: "Votes" },
  { to: "/subjects", label: "Subjects" },
  { to: "/simulator", label: "Simulator" },
  { to: "/calendar", label: "Calendar" },
  { to: "/report-card", label: "Report Card" },
  { to: "/statistics", label: "Statistics" },
  { to: "/settings", label: "Settings" },
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
          <div className="brand-version">3.0.0-dev</div>
        </div>
      </div>

      <nav className="nav">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            {tr(item.label)}
          </NavLink>
        ))}
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
          {resolved === "dark" ? "☾" : "☀"}
        </button>
      </div>
    </aside>
  );
}
