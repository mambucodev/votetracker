import { Routes, Route, Navigate } from "react-router-dom";
import "./styles/app.scss";

function Placeholder({ title }: { title: string }) {
  return (
    <section className="placeholder">
      <h1>{title}</h1>
      <p className="muted">
        This page is being rebuilt. See{" "}
        <code>docs/REWRITE_SPEC.md</code> for the feature spec and{" "}
        <code>legacy-python/src/votetracker/pages/</code> for the reference
        implementation.
      </p>
    </section>
  );
}

export default function App() {
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="brand">
          <span className="brand-mark" />
          <span className="brand-name">VoteTracker</span>
          <span className="brand-version">3.0.0-dev</span>
        </div>
        <nav className="nav">
          <a href="/" className="nav-item active">Dashboard</a>
          <a href="/votes" className="nav-item">Votes</a>
          <a href="/subjects" className="nav-item">Subjects</a>
          <a href="/simulator" className="nav-item">Simulator</a>
          <a href="/calendar" className="nav-item">Calendar</a>
          <a href="/report-card" className="nav-item">Report Card</a>
          <a href="/statistics" className="nav-item">Statistics</a>
          <a href="/settings" className="nav-item">Settings</a>
        </nav>
      </aside>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Placeholder title="Dashboard" />} />
          <Route path="/votes" element={<Placeholder title="Votes" />} />
          <Route path="/subjects" element={<Placeholder title="Subjects" />} />
          <Route path="/simulator" element={<Placeholder title="Simulator" />} />
          <Route path="/calendar" element={<Placeholder title="Calendar" />} />
          <Route path="/report-card" element={<Placeholder title="Report Card" />} />
          <Route path="/statistics" element={<Placeholder title="Statistics" />} />
          <Route path="/settings" element={<Placeholder title="Settings" />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
