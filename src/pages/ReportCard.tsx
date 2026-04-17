import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { save } from "@tauri-apps/plugin-dialog";
import { TopBar } from "@/components/TopBar";
import { Button } from "@/components/primitives/Button";
import { listVotes } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useDataRefresh } from "@/lib/hooks/useDataRefresh";
import { formatGrade, roundReportCard } from "@/lib/format";
import { tr } from "@/lib/i18n";
import type { Vote } from "@/lib/types";
import "./ReportCard.scss";

function avg(vs: Vote[]) {
  const valid = vs.filter((v) => v.grade > 0);
  if (!valid.length) return 0;
  const s = valid.reduce((a, v) => a + v.grade * v.weight, 0);
  const w = valid.reduce((a, v) => a + v.weight, 0);
  return w ? s / w : 0;
}

export default function ReportCard() {
  const { year, term } = useApp();
  const [votes, setVotes] = useState<Vote[]>([]);
  const [split, setSplit] = useState(false);

  useDataRefresh(() => {
    listVotes({ schoolYearId: year?.id, term }).then(setVotes).catch(console.error);
  });

  const bySubject = new Map<string, Vote[]>();
  votes.forEach((v) => {
    if (!bySubject.has(v.subject)) bySubject.set(v.subject, []);
    bySubject.get(v.subject)!.push(v);
  });

  const rows = [...bySubject.entries()]
    .map(([subject, vs]) => {
      const all = avg(vs);
      const w = vs.filter((v) => v.type === "Written");
      const o = vs.filter((v) => v.type === "Oral");
      return {
        subject,
        average: all,
        writtenAvg: avg(w),
        oralAvg: avg(o),
        rounded: roundReportCard(all),
      };
    })
    .sort((a, b) => a.subject.localeCompare(b.subject));

  async function exportPdf() {
    const path = await save({
      defaultPath: `report-card-${year?.name ?? ""}-term${term}.pdf`,
      filters: [{ name: "PDF", extensions: ["pdf"] }],
    });
    if (!path) return;
    try {
      await invoke("export_report_card_pdf", {
        path,
        term,
        schoolYearId: year?.id ?? null,
        split,
      });
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <>
      <TopBar
        title="Report Card"
        right={
          <>
            <label className="split-toggle">
              <input
                type="checkbox"
                checked={split}
                onChange={(e) => setSplit(e.target.checked)}
              />
              {tr("Split Written / Oral")}
            </label>
            <Button variant="primary" size="sm" onClick={exportPdf}>
              {tr("Export PDF")}
            </Button>
          </>
        }
      />
      <section className="page-content report-card">
        <div className="rc-table">
          <div className="rc-head">
            <div>{tr("Subject")}</div>
            {split && <div className="r">{tr("Written")}</div>}
            {split && <div className="r">{tr("Oral")}</div>}
            <div className="r">{tr("Grade")}</div>
            <div className="r">Final</div>
          </div>
          {rows.map((r) => (
            <div key={r.subject} className="rc-row">
              <div>{r.subject}</div>
              {split && <div className="r">{formatGrade(r.writtenAvg)}</div>}
              {split && <div className="r">{formatGrade(r.oralAvg)}</div>}
              <div className="r">{formatGrade(r.average)}</div>
              <div className="r final">{r.rounded}</div>
            </div>
          ))}
        </div>
        <p className="muted small">{tr("Rounding: ≥ 0.5 rounds up")}</p>
      </section>
    </>
  );
}
