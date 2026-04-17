import { useMemo, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { Button } from "@/components/primitives/Button";
import { listVotes } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useDataRefresh } from "@/lib/hooks/useDataRefresh";
import { formatGrade, gradeColor } from "@/lib/format";
import type { Vote } from "@/lib/types";
import "./Calendar.scss";

function monthMatrix(year: number, month: number): Date[][] {
  const first = new Date(year, month, 1);
  const startWeekday = (first.getDay() + 6) % 7; // Monday = 0
  const firstCell = new Date(year, month, 1 - startWeekday);
  const weeks: Date[][] = [];
  for (let w = 0; w < 6; w++) {
    const row: Date[] = [];
    for (let d = 0; d < 7; d++) {
      row.push(new Date(firstCell.getFullYear(), firstCell.getMonth(), firstCell.getDate() + w * 7 + d));
    }
    weeks.push(row);
  }
  return weeks;
}

function iso(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default function CalendarPage() {
  const { year, term } = useApp();
  const [votes, setVotes] = useState<Vote[]>([]);
  const today = new Date();
  const [current, setCurrent] = useState({ year: today.getFullYear(), month: today.getMonth() });
  const [selected, setSelected] = useState<string | null>(null);

  useDataRefresh(() => {
    listVotes({ schoolYearId: year?.id, term }).then(setVotes).catch(console.error);
  });

  const byDate = useMemo(() => {
    const m = new Map<string, Vote[]>();
    for (const v of votes) {
      if (!v.date) continue;
      if (!m.has(v.date)) m.set(v.date, []);
      m.get(v.date)!.push(v);
    }
    return m;
  }, [votes]);

  const matrix = monthMatrix(current.year, current.month);
  const monthName = new Date(current.year, current.month, 1).toLocaleDateString(
    undefined,
    { month: "long", year: "numeric" },
  );

  function shift(delta: number) {
    const next = new Date(current.year, current.month + delta, 1);
    setCurrent({ year: next.getFullYear(), month: next.getMonth() });
  }

  const selectedVotes = selected ? byDate.get(selected) ?? [] : [];

  return (
    <>
      <TopBar
        title="Calendar"
        right={
          <div className="cal-nav">
            <Button variant="ghost" size="sm" onClick={() => shift(-1)}>
              ‹
            </Button>
            <span className="cal-month">{monthName}</span>
            <Button variant="ghost" size="sm" onClick={() => shift(1)}>
              ›
            </Button>
          </div>
        }
      />
      <section className="page-content calendar">
        <div className="cal-grid">
          {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => (
            <div key={d} className="cal-head">
              {d}
            </div>
          ))}
          {matrix.flat().map((d) => {
            const k = iso(d);
            const votes = byDate.get(k) ?? [];
            const inMonth = d.getMonth() === current.month;
            return (
              <button
                key={k}
                className={`cal-cell ${inMonth ? "" : "dim"} ${selected === k ? "selected" : ""}`}
                onClick={() => setSelected(k)}
              >
                <div className="cal-date">{d.getDate()}</div>
                <div className="cal-dots">
                  {votes.slice(0, 5).map((v, i) => (
                    <span
                      key={i}
                      className="dot"
                      style={{ background: gradeColor(v.grade) }}
                    />
                  ))}
                  {votes.length > 5 && <span className="more">+{votes.length - 5}</span>}
                </div>
              </button>
            );
          })}
        </div>

        {selected && (
          <aside className="cal-drawer">
            <div className="drawer-title">{selected}</div>
            {selectedVotes.length === 0 && <div className="muted">—</div>}
            {selectedVotes.map((v) => (
              <div key={v.id} className="drawer-row">
                <span>{v.subject}</span>
                <span style={{ color: gradeColor(v.grade) }}>
                  <strong>{formatGrade(v.grade)}</strong>
                </span>
              </div>
            ))}
          </aside>
        )}
      </section>
    </>
  );
}
