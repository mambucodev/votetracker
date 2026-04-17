import { useEffect, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { Field, NumberInput, Select } from "@/components/primitives/Field";
import { calculateNeededGrade, listSubjects, listVotes } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useDataRefresh } from "@/lib/hooks/useDataRefresh";
import { formatGrade, gradeColor } from "@/lib/format";
import { tr } from "@/lib/i18n";
import type { Vote } from "@/lib/types";
import "./Simulator.scss";

function avg(vs: Vote[], typeFilter?: "Written" | "Oral") {
  const valid = vs.filter(
    (v) => v.grade > 0 && (!typeFilter || v.type === typeFilter),
  );
  if (!valid.length) return 0;
  const s = valid.reduce((a, v) => a + v.grade * v.weight, 0);
  const w = valid.reduce((a, v) => a + v.weight, 0);
  return w ? s / w : 0;
}

export default function Simulator() {
  const { year, term } = useApp();
  const [subjects, setSubjects] = useState<string[]>([]);
  const [subject, setSubject] = useState("");
  const [target, setTarget] = useState(6);
  const [weight, setWeight] = useState(1);
  const [votes, setVotes] = useState<Vote[]>([]);
  const [needed, setNeeded] = useState<number | null>(null);

  useDataRefresh(() => {
    listSubjects().then(setSubjects).catch(console.error);
    listVotes({ schoolYearId: year?.id, term }).then(setVotes).catch(console.error);
  });

  useEffect(() => {
    calculateNeededGrade({
      subject: subject || undefined,
      targetAvg: target,
      newWeight: weight,
      schoolYearId: year?.id,
      term,
    })
      .then(setNeeded)
      .catch(console.error);
  }, [subject, target, weight, year?.id, term, votes.length]);

  const mine = subject
    ? votes.filter((v) => v.subject === subject)
    : votes;
  const current = avg(mine);

  // Replicate the backend formula locally so we can distinguish a real
  // needed-10 from a capped > 10 (out-of-reach) result. The backend clamps
  // to 10 before returning, which loses that information.
  const totalWeighted = mine.reduce(
    (a, v) => a + (v.grade > 0 ? v.grade * v.weight : 0),
    0,
  );
  const totalWeight = mine.reduce(
    (a, v) => a + (v.grade > 0 ? v.weight : 0),
    0,
  );
  const rawNeeded =
    totalWeight === 0
      ? target
      : (target * (totalWeight + weight) - totalWeighted) / weight;
  const outOfReach = needed != null && rawNeeded > 10;

  const projected = needed != null
    ? (totalWeighted + needed * weight) / (totalWeight + weight)
    : current;

  return (
    <>
      <TopBar title="Simulator" />
      <section className="page-content simulator">
        <div className="sim-inputs">
          <Field label={tr("Subject")}>
            <Select value={subject} onChange={(e) => setSubject(e.target.value)}>
              <option value="">Overall</option>
              {subjects.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </Field>
          <Field label={tr("Target Average")}>
            <NumberInput
              value={target}
              min={1}
              max={10}
              step={0.5}
              onChange={(e) => setTarget(parseFloat(e.target.value))}
            />
          </Field>
          <Field label={tr("Weight")}>
            <NumberInput
              value={weight}
              min={0.5}
              max={5}
              step={0.5}
              onChange={(e) => setWeight(parseFloat(e.target.value))}
            />
          </Field>
        </div>

        <div className="sim-results">
          <ResultCard label={tr("Current Average")} value={formatGrade(current)} color={gradeColor(current)} />
          <ResultCard
            label={tr("Needed Grade")}
            value={
              needed == null
                ? "—"
                : outOfReach
                  ? tr("Out of reach")
                  : formatGrade(needed)
            }
            color={
              needed == null
                ? "var(--text-subtle)"
                : outOfReach
                  ? "var(--grade-insufficient)"
                  : gradeColor(needed)
            }
            emphasis
          />
          <ResultCard
            label={tr("Projected Average")}
            value={formatGrade(projected)}
            color={gradeColor(projected)}
          />
        </div>

        {needed == null && current >= target && (
          <div className="sim-note">{tr("Already at or above target")}</div>
        )}
      </section>
    </>
  );
}

function ResultCard({
  label,
  value,
  color,
  emphasis,
}: {
  label: string;
  value: string;
  color?: string;
  emphasis?: boolean;
}) {
  return (
    <div className={`result-card ${emphasis ? "emphasis" : ""}`}>
      <div className="rc-label">{label}</div>
      <div className="rc-value" style={color ? { color } : undefined}>
        {value}
      </div>
    </div>
  );
}
