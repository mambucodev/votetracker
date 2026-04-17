import { useEffect, useState } from "react";
import { Modal } from "../primitives/Modal";
import { Button } from "../primitives/Button";
import { Field, NumberInput, Select, TextInput } from "../primitives/Field";
import { listSubjects, addVote, updateVote } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { tr } from "@/lib/i18n";
import type { GradeType, Vote } from "@/lib/types";

interface Props {
  open: boolean;
  onClose: () => void;
  editing?: Vote | null;
}

export function AddVoteDialog({ open, onClose, editing }: Props) {
  const { year, term } = useApp();
  const [subjects, setSubjects] = useState<string[]>([]);
  const [subject, setSubject] = useState("");
  const [grade, setGrade] = useState(6.0);
  const [kind, setKind] = useState<GradeType>("Written");
  const [t, setT] = useState<1 | 2>(term);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [description, setDescription] = useState("");
  const [weight, setWeight] = useState(1);

  useEffect(() => {
    if (!open) return;
    listSubjects().then(setSubjects).catch(console.error);
    if (editing) {
      setSubject(editing.subject);
      setGrade(editing.grade);
      setKind(editing.type);
      setT(editing.term as 1 | 2);
      setDate(editing.date);
      setDescription(editing.description ?? "");
      setWeight(editing.weight);
    } else {
      setSubject("");
      setGrade(6.0);
      setKind("Written");
      setT(term);
      setDate(new Date().toISOString().slice(0, 10));
      setDescription("");
      setWeight(1);
    }
  }, [open, editing, term]);

  async function save() {
    if (!subject.trim()) return;
    const payload: Vote = {
      id: editing?.id ?? null,
      subject: subject.trim(),
      grade,
      type: kind,
      term: t,
      date,
      description: description || null,
      weight,
      school_year_id: year?.id ?? null,
    };
    try {
      if (editing?.id != null) {
        await updateVote(editing.id, payload);
      } else {
        await addVote(payload);
      }
      onClose();
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={editing ? tr("Edit vote") : tr("New vote")}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            {tr("Cancel")}
          </Button>
          <Button variant="primary" onClick={save}>
            {tr("Save")}
          </Button>
        </>
      }
    >
      <Field label={tr("Subject")}>
        <TextInput
          list="vote-subjects"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="Math"
          autoFocus
        />
        <datalist id="vote-subjects">
          {subjects.map((s) => (
            <option key={s} value={s} />
          ))}
        </datalist>
      </Field>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Field label={tr("Grade")}>
          <NumberInput
            value={grade}
            step={0.25}
            min={0}
            max={10}
            onChange={(e) => setGrade(parseFloat(e.target.value))}
          />
        </Field>
        <Field label={tr("Weight")}>
          <NumberInput
            value={weight}
            step={0.5}
            min={0.5}
            max={5}
            onChange={(e) => setWeight(parseFloat(e.target.value))}
          />
        </Field>
        <Field label={tr("Type")}>
          <Select value={kind} onChange={(e) => setKind(e.target.value as GradeType)}>
            <option value="Written">{tr("Written")}</option>
            <option value="Oral">{tr("Oral")}</option>
            <option value="Practical">{tr("Practical")}</option>
          </Select>
        </Field>
        <Field label={tr("Term")}>
          <Select value={t} onChange={(e) => setT(Number(e.target.value) as 1 | 2)}>
            <option value={1}>1</option>
            <option value={2}>2</option>
          </Select>
        </Field>
      </div>

      <Field label={tr("Date")}>
        <TextInput type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </Field>
      <Field label={tr("Description")}>
        <TextInput
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder=""
        />
      </Field>
    </Modal>
  );
}
