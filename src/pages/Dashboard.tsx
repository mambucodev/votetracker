import { useState } from "react";
import { Line, LineChart, ResponsiveContainer } from "recharts";
import { AlertCircle, TrendingDown, TrendingUp } from "lucide-react";
import { listVotes } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useDataRefresh } from "@/lib/hooks/useDataRefresh";
import { formatGrade, gradeColor } from "@/lib/format";
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

interface TrendPoint {
  date: string;
  avg: number;
}

/** Build a cumulative weighted-avg series from the given votes, sorted by date. */
function cumulativeTrend(votes: Vote[]): TrendPoint[] {
  const dated = [...votes]
    .filter((v) => v.date && v.grade > 0)
    .sort((a, b) => (a.date < b.date ? -1 : 1));
  const out: TrendPoint[] = [];
  let cumS = 0;
  let cumW = 0;
  for (const v of dated) {
    cumS += v.grade * v.weight;
    cumW += v.weight;
    out.push({ date: v.date, avg: cumS / cumW });
  }
  return out;
}

/** Average grade in the last N days from the ref date. Returns null if no data. */
function avgInWindow(votes: Vote[], refDate: Date, days: number): number | null {
  const cutoff = new Date(refDate);
  cutoff.setDate(cutoff.getDate() - days);
  const iso = (d: Date) => d.toISOString().slice(0, 10);
  const windowed = votes.filter((v) => {
    if (!v.date || v.grade <= 0) return false;
    return v.date > iso(cutoff) && v.date <= iso(refDate);
  });
  const a = average(windowed);
  return a > 0 ? a : null;
}

function relativeTime(iso: string): string {
  if (!iso) return "";
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  const ms = Date.now() - d.getTime();
  const day = 86_400_000;
  const days = Math.floor(ms / day);
  if (days <= 0) return tr("today");
  if (days === 1) return tr("yesterday");
  if (days < 7) return `${days}${tr("d ago")}`;
  if (days < 30) return `${Math.floor(days / 7)}${tr("w ago")}`;
  if (days < 365) return `${Math.floor(days / 30)}${tr("mo ago")}`;
  return `${Math.floor(days / 365)}${tr("y ago")}`;
}

function initialFor(subject: string): string {
  const s = subject.trim();
  return s ? s.charAt(0).toUpperCase() : "?";
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
    .map(([s, vs]) => ({ subject: s, avg: average(vs), count: vs.length, votes: vs }))
    .sort((a, b) => b.avg - a.avg);
  const failing = subjAvgs.filter((s) => s.avg > 0 && s.avg < 6).length;
  const recent = [...votes]
    .sort((a, b) => (a.date > b.date ? -1 : a.date < b.date ? 1 : 0))
    .slice(0, 6);

  const trend = cumulativeTrend(votes);
  // Delta: avg of last 30 days vs 30 days before that.
  const now = new Date();
  const curMonth = avgInWindow(votes, now, 30);
  const prevMonthRef = new Date(now);
  prevMonthRef.setDate(prevMonthRef.getDate() - 30);
  const prevMonth = avgInWindow(votes, prevMonthRef, 30);
  const hasDelta = curMonth !== null && prevMonth !== null;
  const delta = hasDelta ? curMonth - prevMonth : 0;
  const deltaSign = delta >= 0 ? "+" : "−";
  const deltaLabel = hasDelta
    ? `${deltaSign}${Math.abs(delta).toFixed(2)} ${tr("vs last month")}`
    : `— ${tr("vs last month")}`;
  const DeltaIcon = delta >= 0 ? TrendingUp : TrendingDown;
  const deltaClass = !hasDelta
    ? "delta-neutral"
    : delta >= 0
      ? "delta-up"
      : "delta-down";

  return (
    <>
      <TopBar title="Dashboard" />
      <section className="page-content dashboard">
        {/* Hero card */}
        <div className="hero-card">
          <div className="hero-left">
            <div className="hero-label">{tr("Overall Average")}</div>
            <div className="hero-value" style={{ color: gradeColor(overallAvg) }}>
              {formatGrade(overallAvg)}
            </div>
            <div className={`hero-delta ${deltaClass}`}>
              {hasDelta && <DeltaIcon size={14} strokeWidth={2.25} />}
              <span>{deltaLabel}</span>
            </div>
          </div>
          <div className="hero-spark">
            {trend.length >= 2 ? (
              <ResponsiveContainer width="100%" height={70}>
                <LineChart data={trend} margin={{ top: 6, right: 4, bottom: 6, left: 4 }}>
                  <defs>
                    <linearGradient id="hero-spark-grad" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="var(--accent-500)" />
                      <stop offset="100%" stopColor="var(--accent-300)" />
                    </linearGradient>
                  </defs>
                  <Line
                    type="monotone"
                    dataKey="avg"
                    stroke="url(#hero-spark-grad)"
                    strokeWidth={2.25}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="spark-empty muted">{tr("Not enough data yet")}</div>
            )}
          </div>
        </div>

        {/* 3-stat row */}
        <div className="mini-stat-grid">
          <MiniStat
            label={tr("Failing")}
            value={`${failing}`}
            icon={failing > 0 ? <AlertCircle size={14} /> : null}
            tone={failing > 0 ? "danger" : "ok"}
          />
          <MiniStat label={tr("Total Votes")} value={`${votes.length}`} />
          <MiniStat label={tr("Subjects")} value={`${subjAvgs.length}`} />
        </div>

        {/* Subjects grid + right rail */}
        <div className="dashboard-split">
          <div className="subject-cards">
            {subjAvgs.length === 0 && <EmptyState />}
            {subjAvgs.map((s) => {
              const subjTrend = cumulativeTrend(s.votes);
              return (
                <div key={s.subject} className="subject-card">
                  <div className="sc-title">
                    <span className="dot" style={{ background: gradeColor(s.avg) }} />
                    <span>{s.subject}</span>
                  </div>
                  <div className="sc-avg" style={{ color: gradeColor(s.avg) }}>
                    {formatGrade(s.avg)}
                  </div>
                  <div className="sc-count">
                    {s.count} {s.count === 1 ? tr("vote") : tr("votes")}
                  </div>
                  <div className="sc-spark">
                    {subjTrend.length >= 2 ? (
                      <ResponsiveContainer width="100%" height={36}>
                        <LineChart
                          data={subjTrend}
                          margin={{ top: 2, right: 0, bottom: 2, left: 0 }}
                        >
                          <Line
                            type="monotone"
                            dataKey="avg"
                            stroke="var(--chart-accent)"
                            strokeOpacity={0.65}
                            strokeWidth={1.5}
                            dot={false}
                            isAnimationActive={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="sc-spark-placeholder" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <aside className="recent">
            <div className="section-title">{tr("Recent Grades")}</div>
            {recent.length === 0 && <div className="muted">{tr("No grades yet")}</div>}
            {recent.map((v) => (
              <div key={v.id} className="recent-row">
                <span
                  className="r-avatar"
                  style={{ background: gradeColor(v.grade) }}
                  aria-hidden="true"
                >
                  {initialFor(v.subject)}
                </span>
                <span className="r-main">
                  <span className="r-subject">{v.subject}</span>
                  <span className="r-type">{tr(v.type)}</span>
                </span>
                <span className="r-chip" style={{ background: gradeColor(v.grade) }}>
                  {formatGrade(v.grade)}
                </span>
                <span className="r-when">{relativeTime(v.date)}</span>
              </div>
            ))}
          </aside>
        </div>
      </section>
    </>
  );
}

function MiniStat({
  label,
  value,
  icon,
  tone,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
  tone?: "ok" | "danger";
}) {
  return (
    <div className={`mini-stat${tone === "danger" ? " is-danger" : ""}`}>
      <div className="ms-label">{label}</div>
      <div className="ms-value">
        {icon}
        <span>{value}</span>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="es-title">{tr("No grades yet")}</div>
      <div className="es-body muted">
        {tr("Add your first vote from the Votes page")}
      </div>
    </div>
  );
}
