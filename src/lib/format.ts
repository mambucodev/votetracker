// Formatting helpers mirroring `legacy-python/src/votetracker/utils.py`.

export function gradeColor(avg: number): string {
  if (avg < 5.5) return "var(--grade-insufficient)";
  if (avg < 6.0) return "var(--grade-warning)";
  if (avg < 8.0) return "var(--grade-good)";
  return "var(--grade-excellent)";
}

export function formatGrade(grade: number): string {
  // Italian-style with 2 decimals; plus/minus (stored as 0) collapses to em-dash.
  if (grade <= 0) return "—";
  return grade.toFixed(2).replace(/\.?0+$/, "");
}

/** Italian rounding — ≥ 0.5 → up, else down. Mirrors `round_report_card`. */
export function roundReportCard(avg: number): number {
  if (avg <= 0) return 0;
  const intPart = Math.trunc(avg);
  const decimal = avg - intPart;
  return decimal >= 0.5 ? intPart + 1 : intPart;
}

/** Human-readable date from YYYY-MM-DD. Defaults to current-locale short form. */
export function formatDate(iso: string, locale?: string): string {
  if (!iso) return "";
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(locale, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}
