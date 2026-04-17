import { useState } from "react";
import { Plus } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { Button } from "@/components/primitives/Button";
import { AddSubjectDialog } from "@/components/dialogs/AddSubjectDialog";
import { listSubjects, listVotes } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useDataRefresh } from "@/lib/hooks/useDataRefresh";
import { formatGrade, gradeColor } from "@/lib/format";
import { tr } from "@/lib/i18n";
import type { Vote } from "@/lib/types";
import "./Subjects.scss";

function average(vs: Vote[]) {
  const valid = vs.filter((v) => v.grade > 0);
  if (!valid.length) return 0;
  const s = valid.reduce((a, v) => a + v.grade * v.weight, 0);
  const w = valid.reduce((a, v) => a + v.weight, 0);
  return w ? s / w : 0;
}

export default function Subjects() {
  const { year, term } = useApp();
  const [subjects, setSubjects] = useState<string[]>([]);
  const [votes, setVotes] = useState<Vote[]>([]);
  const [dialog, setDialog] = useState<{ open: boolean; editing: string | null }>({
    open: false,
    editing: null,
  });

  useDataRefresh(() => {
    listSubjects().then(setSubjects).catch(console.error);
    listVotes({ schoolYearId: year?.id, term }).then(setVotes).catch(console.error);
  });

  const rows = subjects.map((s) => {
    const mine = votes.filter((v) => v.subject === s);
    return {
      name: s,
      avg: average(mine),
      written: mine.filter((v) => v.type === "Written").length,
      oral: mine.filter((v) => v.type === "Oral").length,
      practical: mine.filter((v) => v.type === "Practical").length,
      count: mine.length,
    };
  });

  return (
    <>
      <TopBar
        title="Subjects"
        right={
          <Button
            variant="primary"
            size="sm"
            onClick={() => setDialog({ open: true, editing: null })}
          >
            <Plus size={14} strokeWidth={2} /> {tr("Add subject")}
          </Button>
        }
      />
      <section className="page-content">
        <div className="subject-cards">
          {rows.map((s) => (
            <button
              key={s.name}
              className="subject-card clickable"
              onClick={() => setDialog({ open: true, editing: s.name })}
            >
              <div className="sc-title">
                <span className="dot" style={{ background: gradeColor(s.avg) }} />
                <span>{s.name}</span>
              </div>
              <div className="sc-avg" style={{ color: gradeColor(s.avg) }}>
                {formatGrade(s.avg)}
              </div>
              <div className="sc-count">
                {s.written} W · {s.oral} O · {s.practical} P
              </div>
            </button>
          ))}
        </div>
      </section>

      <AddSubjectDialog
        open={dialog.open}
        editing={dialog.editing}
        onClose={() => setDialog({ open: false, editing: null })}
      />
    </>
  );
}
