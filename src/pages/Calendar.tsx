import { Fragment, useMemo, useState, type CSSProperties } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
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

/** Weighted average of a day's votes, excluding grades ≤ 0 (mirrors `calc_average`). */
function dayAverage(votes: Vote[]): number {
  let sum = 0;
  let wSum = 0;
  for (const v of votes) {
    if (v.grade <= 0) continue;
    const w = v.weight || 1;
    sum += v.grade * w;
    wSum += w;
  }
  return wSum > 0 ? sum / wSum : 0;
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

  // Compute which row the selected cell sits in so we can splice a full-width
  // `.cal-expand` strip right after that row.
  const selectedRowIndex = useMemo(() => {
    if (!selected) return -1;
    for (let r = 0; r < matrix.length; r++) {
      for (const d of matrix[r]) {
        if (iso(d) === selected) return r;
      }
    }
    return -1;
  }, [selected, matrix]);

  const selectedVotes = selected ? byDate.get(selected) ?? [] : [];

  return (
    <>
      <TopBar
        title="Calendar"
        right={
          <div className="cal-nav">
            <Button variant="ghost" size="sm" onClick={() => shift(-1)} aria-label="Previous month">
              <ChevronLeft size={16} />
            </Button>
            <span className="cal-month">{monthName}</span>
            <Button variant="ghost" size="sm" onClick={() => shift(1)} aria-label="Next month">
              <ChevronRight size={16} />
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
          {matrix.map((row, rowIdx) => (
            <Fragment key={`row-${rowIdx}`}>
              {row.map((d) => {
                const k = iso(d);
                const dayVotes = byDate.get(k) ?? [];
                const inMonth = d.getMonth() === current.month;
                const tintPct = Math.min(35, dayVotes.length * 10);
                const avg = dayAverage(dayVotes);
                const tintStyle =
                  dayVotes.length > 0 && avg > 0
                    ? ({
                        "--cell-grade-color": gradeColor(avg),
                        "--cell-tint-pct": `${tintPct}%`,
                      } as CSSProperties)
                    : undefined;
                return (
                  <button
                    key={k}
                    className={`cal-cell ${inMonth ? "" : "dim"} ${selected === k ? "selected" : ""}`}
                    style={tintStyle}
                    onClick={() => setSelected((s) => (s === k ? null : k))}
                  >
                    <div className="cal-date">{d.getDate()}</div>
                    <div className="cal-dots">
                      {dayVotes.slice(0, 5).map((v, i) => (
                        <span
                          key={i}
                          className="dot"
                          style={{ background: gradeColor(v.grade) }}
                        />
                      ))}
                      {dayVotes.length > 5 && <span className="more">+{dayVotes.length - 5}</span>}
                    </div>
                  </button>
                );
              })}
              {selectedRowIndex === rowIdx && selected && (
                <div
                  key={`expand-${selected}`}
                  className="cal-expand open"
                  role="region"
                  aria-label={`Grades for ${selected}`}
                >
                  <div className="cal-expand-inner">
                    <div className="cal-expand-head">
                      <span className="cal-expand-date">{selected}</span>
                      {selectedVotes.length === 0 && <span className="muted">—</span>}
                    </div>
                    <div className="cal-expand-list">
                      {selectedVotes.map((v) => (
                        <div key={v.id ?? `${v.subject}-${v.grade}`} className="cal-expand-chip">
                          <span className="chip-subject">{v.subject}</span>
                          <span
                            className="chip-grade"
                            style={{ color: gradeColor(v.grade) }}
                          >
                            <strong>{formatGrade(v.grade)}</strong>
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </Fragment>
          ))}
        </div>
      </section>
    </>
  );
}
