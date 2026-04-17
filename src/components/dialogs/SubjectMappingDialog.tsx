import { useEffect, useState } from "react";
import { Modal } from "../primitives/Modal";
import { Button } from "../primitives/Button";
import { Select } from "../primitives/Field";
import {
  listSubjects,
  saveProviderMapping,
  subjectMappingSuggestion,
} from "@/lib/ipc";
import { tr } from "@/lib/i18n";
import type { AutoSuggestion } from "@/lib/types";
import "./SubjectMappingDialog.scss";

interface Props {
  open: boolean;
  onClose: () => void;
  providerId: string;
  sourceSubjects: string[];
}

interface Row {
  source: string;
  target: string; // empty string represents "Create new"
  confidence: number;
  suggestion: AutoSuggestion | null;
}

const CREATE_NEW = "__create_new__";

export function SubjectMappingDialog({
  open,
  onClose,
  providerId,
  sourceSubjects,
}: Props) {
  const [rows, setRows] = useState<Row[]>([]);
  const [vtSubjects, setVtSubjects] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    (async () => {
      setError(null);
      try {
        const subs = await listSubjects();
        if (cancelled) return;
        setVtSubjects(subs);

        const seeded: Row[] = await Promise.all(
          sourceSubjects.map(async (src) => {
            try {
              const s = await subjectMappingSuggestion(src);
              const target = s.suggested_match ?? "";
              return {
                source: src,
                target,
                confidence: s.confidence ?? 0,
                suggestion: s,
              };
            } catch {
              return {
                source: src,
                target: "",
                confidence: 0,
                suggestion: null,
              };
            }
          }),
        );
        if (cancelled) return;
        setRows(seeded);
      } catch (e) {
        if (!cancelled) setError(String(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, providerId, sourceSubjects]);

  function updateTarget(idx: number, value: string) {
    setRows((prev) => {
      const next = prev.slice();
      next[idx] = {
        ...next[idx],
        target: value === CREATE_NEW ? "" : value,
      };
      return next;
    });
  }

  function confidenceLabel(conf: number): string {
    if (conf >= 0.85) return tr("High");
    if (conf >= 0.7) return tr("Medium");
    if (conf > 0) return tr("Low");
    return tr("None");
  }

  function confidenceClass(conf: number): string {
    if (conf >= 0.85) return "conf-high";
    if (conf >= 0.7) return "conf-medium";
    if (conf > 0) return "conf-low";
    return "conf-none";
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      for (const r of rows) {
        const target = r.target.trim();
        if (!target) continue; // skip "Create new" / empty rows
        await saveProviderMapping(providerId, r.source, target);
      }
      onClose();
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  }

  const isEmpty = sourceSubjects.length === 0;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={tr("Configure Subject Mapping")}
      width={640}
      footer={
        <>
          <div style={{ flex: 1 }} />
          <Button variant="ghost" onClick={onClose}>
            {tr("Cancel")}
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
            disabled={saving || isEmpty}
          >
            {saving ? tr("Saving…") : tr("Save")}
          </Button>
        </>
      }
    >
      <div className="subject-mapping">
        {isEmpty ? (
          <div className="subject-mapping__hint">
            {tr(
              "No source subjects yet — run a sync first, then come back to map them.",
            )}
          </div>
        ) : (
          <>
            <div className="subject-mapping__header">
              <span>{tr("Source")}</span>
              <span>{tr("VoteTracker subject")}</span>
              <span>{tr("Confidence")}</span>
            </div>
            <div className="subject-mapping__rows">
              {rows.map((r, idx) => (
                <div key={r.source} className="subject-mapping__row">
                  <div className="subject-mapping__source" title={r.source}>
                    {r.source}
                  </div>
                  <Select
                    value={r.target === "" ? CREATE_NEW : r.target}
                    onChange={(e) => updateTarget(idx, e.target.value)}
                  >
                    {vtSubjects.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                    <option value={CREATE_NEW}>
                      {tr("— Create new —")}
                    </option>
                  </Select>
                  <span
                    className={`subject-mapping__chip ${confidenceClass(r.confidence)}`}
                  >
                    {confidenceLabel(r.confidence)}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}
        {error && <div className="subject-mapping__error">{error}</div>}
      </div>
    </Modal>
  );
}
