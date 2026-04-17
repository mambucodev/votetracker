import { useEffect, useState } from "react";
import { Route, Routes, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Votes from "./pages/Votes";
import Subjects from "./pages/Subjects";
import Simulator from "./pages/Simulator";
import CalendarPage from "./pages/Calendar";
import ReportCard from "./pages/ReportCard";
import Statistics from "./pages/Statistics";
import Settings from "./pages/Settings";
import Onboarding from "./pages/Onboarding";
import { useShortcuts } from "./lib/hooks/useShortcuts";
import { useMenuEvents } from "./lib/hooks/useMenuEvents";
import { ShortcutsHelpDialog } from "./components/dialogs/ShortcutsHelpDialog";
import { CommandPalette } from "./components/CommandPalette";
import { getSetting, setSetting } from "./lib/ipc";
import { setLang, type Lang } from "./lib/i18n";
import "./styles/app.scss";

export default function App() {
  useShortcuts();
  useMenuEvents();
  const [onboardNeeded, setOnboardNeeded] = useState<boolean | null>(null);

  useEffect(() => {
    (async () => {
      const done = await getSetting("onboarding_complete");
      setOnboardNeeded(done !== "1");

      const lang = await getSetting("language");
      if (lang) setLang(lang as Lang);
      else {
        const fallback = navigator.language?.toLowerCase().startsWith("it")
          ? "it"
          : "en";
        setLang(fallback);
        await setSetting("language", fallback);
      }
    })().catch(console.error);
  }, []);

  if (onboardNeeded === null) return null;
  if (onboardNeeded) {
    return <Onboarding onDone={() => setOnboardNeeded(false)} />;
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/votes" element={<Votes />} />
          <Route path="/subjects" element={<Subjects />} />
          <Route path="/simulator" element={<Simulator />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/report-card" element={<ReportCard />} />
          <Route path="/statistics" element={<Statistics />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <ShortcutsHelpDialog />
      <CommandPalette />
    </div>
  );
}
