import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { TopBar } from "@/components/TopBar";
import { listVotes } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useDataRefresh } from "@/lib/hooks/useDataRefresh";
import { gradeColor } from "@/lib/format";
import type { Vote } from "@/lib/types";
import "./Statistics.scss";

function avg(vs: Vote[]) {
  const valid = vs.filter((v) => v.grade > 0);
  if (!valid.length) return 0;
  const s = valid.reduce((a, v) => a + v.grade * v.weight, 0);
  const w = valid.reduce((a, v) => a + v.weight, 0);
  return w ? s / w : 0;
}

export default function Statistics() {
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

  const barData = [...bySubject.entries()]
    .map(([subject, vs]) => ({ subject, avg: Number(avg(vs).toFixed(2)) }))
    .sort((a, b) => b.avg - a.avg);

  // Histogram — 0.5-wide bins between 1 and 10.
  const bins: { bin: string; count: number }[] = [];
  for (let lo = 1; lo < 10; lo += 0.5) {
    bins.push({ bin: lo.toFixed(1), count: 0 });
  }
  votes.forEach((v) => {
    if (v.grade < 1 || v.grade > 10) return;
    const idx = Math.min(Math.floor((v.grade - 1) / 0.5), bins.length - 1);
    if (idx >= 0) bins[idx].count++;
  });

  // Trend — by date (sorted asc) using cumulative avg.
  const dated = [...votes]
    .filter((v) => v.date && v.grade > 0)
    .sort((a, b) => (a.date < b.date ? -1 : 1));
  const trend: { date: string; avg: number }[] = [];
  let cumS = 0, cumW = 0;
  for (const v of dated) {
    cumS += v.grade * v.weight;
    cumW += v.weight;
    trend.push({ date: v.date, avg: Number((cumS / cumW).toFixed(2)) });
  }

  return (
    <>
      <TopBar title="Statistics" />
      <section className="page-content stats">
        <div className="chart-card">
          <h3>Subject averages</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={barData} layout="vertical">
              <defs>
                <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#d97757" />
                  <stop offset="100%" stopColor="#f2bf9b" />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="var(--chart-grid)" />
              <XAxis type="number" domain={[0, 10]} stroke="var(--chart-axis)" fontSize={11} />
              <YAxis type="category" dataKey="subject" stroke="var(--chart-axis)" fontSize={11} width={110} />
              <Tooltip />
              <Bar dataKey="avg" radius={[0, 6, 6, 0]}>
                {barData.map((d, i) => (
                  <Cell key={i} fill={gradeColor(d.avg).startsWith("var") ? "url(#accent)" : gradeColor(d.avg)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={bins}>
              <CartesianGrid stroke="var(--chart-grid)" />
              <XAxis dataKey="bin" stroke="var(--chart-axis)" fontSize={11} />
              <YAxis stroke="var(--chart-axis)" fontSize={11} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="url(#accent)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Trend</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trend}>
              <CartesianGrid stroke="var(--chart-grid)" />
              <XAxis dataKey="date" stroke="var(--chart-axis)" fontSize={11} />
              <YAxis domain={[0, 10]} stroke="var(--chart-axis)" fontSize={11} />
              <Tooltip />
              <Line type="monotone" dataKey="avg" stroke="#d97757" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {barData.length >= 4 && (
          <div className="chart-card">
            <h3>Subjects radar</h3>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={barData}>
                <PolarGrid stroke="var(--chart-grid)" />
                <PolarAngleAxis dataKey="subject" stroke="var(--chart-axis)" fontSize={11} />
                <PolarRadiusAxis domain={[0, 10]} stroke="var(--chart-axis)" fontSize={10} />
                <Radar
                  dataKey="avg"
                  stroke="#d97757"
                  fill="url(#accent)"
                  fillOpacity={0.4}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>
    </>
  );
}
