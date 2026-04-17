import { useState } from "react";
import { listVotes } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useDataRefresh } from "@/lib/hooks/useDataRefresh";
import { formatDate, formatGrade, gradeColor } from "@/lib/format";
import { tr } from "@/lib/i18n";
import { TopBar } from "@/components/TopBar";
import type { Vote } from "@/lib/types";
import "./Dashboard.scss";

function average(votes: Vote[]): number {
  const valid = votes.filter((v) => v.grade > 0);
  if (!valid.length) return 0;
  const s = valid.reduce((a, v) => a + v.grade * v.weight, 0);
  const w = valid.reduce((a, v) => a + v.weight, 0);
  return w > 0 ? s / w : 0;
}

export default function Dashboard() {
  const { year, term } = useApp();
  const [votes, setVotes] = useState<Vote[]>([]);

  useDataRefresh(() => {
    listVotes({ schoolYearId: year?.id, term }).then(setVotes).catch(console.error);
  });

  const bySubject = new Map<string, Vote[]>();
  votes.forEach((v) => {
    if (!bySubject.has(v.subject)) bySubject.set(v.subject, []);
    bySubject.get(v.subject)!.push(v);
  });

  const overallAvg = average(votes);
  const subjAvgs = [...bySubject.entries()]
    .map(([s, vs]) => ({ subject: s, avg: average(vs), count: vs.length }))
    .sort((a, b) => b.avg - a.avg);
  const failing = subjAvgs.filter((s) => s.avg > 0 && s.avg < 6).length;
  const recent = [...votes]
    .sort((a, b) => (a.date > b.date ? -1 : a.date < b.date ? 1 : 0))
    .slice(0, 6);

  return (
    <>
      <TopBar title="Dashboard" />
      <section className="page-content dashboard">
        <div className="stat-grid">
          <StatCard
            label={tr("Overall Average")}
            value={formatGrade(overallAvg)}
            color={gradeColor(overallAvg)}
          />
          <StatCard
            label={tr("Failing")}
            value={`${failing}`}
            color={failing > 0 ? "var(--grade-insufficient)" : "var(--grade-excellent)"}
          />
          <StatCard label={tr("Total Votes")} value={`${votes.length}`} />
          <StatCard label={tr("Subjects")} value={`${subjAvgs.length}`} />
        </div>

        <div className="dashboard-split">
          <div className="subject-cards">
            {subjAvgs.length === 0 && <EmptyState />}
            {subjAvgs.map((s) => (
              <div key={s.subject} className="subject-card">
                <div className="sc-title">
                  <span className="dot" style={{ background: gradeColor(s.avg) }} />
                  <span>{s.subject}</span>
                </div>
                <div className="sc-avg" style={{ color: gradeColor(s.avg) }}>
                  {formatGrade(s.avg)}
                </div>
                <div className="sc-count">{s.count} {s.count === 1 ? "vote" : "votes"}</div>
              </div>
            ))}
          </div>

          <aside className="recent">
            <div className="section-title">{tr("Recent Grades")}</div>
            {recent.length === 0 && <div className="muted">{tr("No grades yet")}</div>}
            {recent.map((v) => (
              <div key={v.id} className="recent-row">
                <span className="r-subject">{v.subject}</span>
                <span className="r-grade" style={{ color: gradeColor(v.grade) }}>
                  {formatGrade(v.grade)}
                </span>
                <span className="r-type">{tr(v.type)}</span>
                <span className="r-date">{formatDate(v.date)}</span>
              </div>
            ))}
          </aside>
        </div>
      </section>
    </>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={color ? { color } : undefined}>
        {value}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="es-title">{tr("No grades yet")}</div>
      <div className="es-body muted">
        Add your first vote from the Votes page (Ctrl+N).
      </div>
    </div>
  );
}
