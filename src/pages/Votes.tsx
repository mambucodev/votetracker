import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { Button } from "@/components/primitives/Button";
import { Select } from "@/components/primitives/Field";
import { AddVoteDialog } from "@/components/dialogs/AddVoteDialog";
import { deleteVote, listSubjects, listVotes } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useDataRefresh } from "@/lib/hooks/useDataRefresh";
import { formatDate, formatGrade, gradeColor } from "@/lib/format";
import { tr } from "@/lib/i18n";
import type { Vote } from "@/lib/types";
import "./Votes.scss";

export default function Votes() {
  const { year, term } = useApp();
  const newVoteIntent = useApp((s) => s.newVoteIntent);
  const consumeNewVote = useApp((s) => s.consumeNewVote);
  const [votes, setVotes] = useState<Vote[]>([]);
  const [subjects, setSubjects] = useState<string[]>([]);
  const [filterSubject, setFilterSubject] = useState("");
  const [dialog, setDialog] = useState<{ open: boolean; editing: Vote | null }>({
    open: false,
    editing: null,
  });
  const [selected, setSelected] = useState<number | null>(null);

  useDataRefresh(() => {
    listVotes({
      schoolYearId: year?.id,
      term,
      subject: filterSubject || undefined,
    })
      .then(setVotes)
      .catch(console.error);
    listSubjects().then(setSubjects).catch(console.error);
  });

  useEffect(() => {
    // refetch when filter changes
    listVotes({
      schoolYearId: year?.id,
      term,
      subject: filterSubject || undefined,
    }).then(setVotes);
  }, [filterSubject, year?.id, term]);

  // Ctrl+N is routed through the global shortcut handler → useGlobalActions
  // → newVoteIntent. Open the dialog and clear the flag so a later
  // re-mount doesn't re-open it.
  useEffect(() => {
    if (newVoteIntent) {
      setDialog({ open: true, editing: null });
      consumeNewVote();
    }
  }, [newVoteIntent, consumeNewVote]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea" || tag === "select") return;
      if (selected != null && e.key === "Delete") {
        deleteVote(selected).catch(console.error);
        setSelected(null);
      }
      if (selected != null && e.key === "Enter") {
        const v = votes.find((x) => x.id === selected);
        if (v) setDialog({ open: true, editing: v });
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected, votes]);

  return (
    <>
      <TopBar
        title="Votes"
        right={
          <Button
            variant="primary"
            size="sm"
            onClick={() => setDialog({ open: true, editing: null })}
          >
            <Plus size={14} strokeWidth={2} /> {tr("Add vote")}
          </Button>
        }
      />
      <section className="page-content">
        <div className="filters">
          <Select
            value={filterSubject}
            onChange={(e) => setFilterSubject(e.target.value)}
          >
            <option value="">{tr("Subjects")} — all</option>
            {subjects.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
          <span className="count muted">{votes.length} votes</span>
        </div>

        <div className="vote-table" role="table">
          <div className="vt-head" role="row">
            <div role="columnheader">{tr("Date")}</div>
            <div role="columnheader">{tr("Subject")}</div>
            <div role="columnheader">{tr("Description")}</div>
            <div role="columnheader">{tr("Type")}</div>
            <div role="columnheader" className="r">
              {tr("Grade")}
            </div>
            <div role="columnheader" className="r">
              {tr("Weight")}
            </div>
          </div>
          {votes.length === 0 && (
            <div className="muted empty">{tr("No grades yet")}</div>
          )}
          {votes.map((v) => (
            <div
              key={v.id}
              role="row"
              className={`vt-row ${selected === v.id ? "selected" : ""}`}
              onClick={() => setSelected(v.id)}
              onDoubleClick={() =>
                setDialog({ open: true, editing: v })
              }
            >
              <div>{formatDate(v.date)}</div>
              <div>{v.subject}</div>
              <div className="muted">{v.description ?? ""}</div>
              <div className="type-badge" data-type={v.type}>
                {tr(v.type)}
              </div>
              <div className="r" style={{ color: gradeColor(v.grade) }}>
                <strong>{formatGrade(v.grade)}</strong>
              </div>
              <div className="r muted">{v.weight}×</div>
            </div>
          ))}
        </div>
      </section>

      <AddVoteDialog
        open={dialog.open}
        editing={dialog.editing}
        onClose={() => setDialog({ open: false, editing: null })}
      />
    </>
  );
}
