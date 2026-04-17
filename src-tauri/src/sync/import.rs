//! Import engine — new / updated / skipped triage.
//!
//! Port of the Python dedup logic (see docs/REWRITE_SPEC.md §4.2).

use super::RawGrade;
use crate::db::{settings, subjects, votes, Database};
use crate::domain::types::Vote;
use serde::Serialize;

#[derive(Debug, Clone, Copy, Default, Serialize)]
pub struct ImportSummary {
    pub new_count: u32,
    pub updated_count: u32,
    pub skipped_count: u32,
}

pub fn import_all(
    db: &Database,
    provider_id: &str,
    raw: &[RawGrade],
    school_year_id: Option<i64>,
) -> anyhow::Result<ImportSummary> {
    let conn = db.pool().get()?;
    let mut summary = ImportSummary::default();

    for r in raw {
        // Map source-subject → VT subject (fall back to raw name).
        let subject = settings::get_mapping(&conn, provider_id, &r.subject)?
            .unwrap_or_else(|| r.subject.clone());

        // Ensure subject exists in DB (otherwise vote insert would fail).
        subjects::add(&conn, &subject)?;

        // Match by (subject, date, kind) only — ignore grade.
        match votes::find_by_metadata(&conn, &subject, &r.date, r.kind, school_year_id)? {
            Some(existing) => {
                // Exact match (including grade + description + weight) → skip.
                if (existing.grade - r.grade).abs() < 1e-9
                    && (existing.weight - r.weight).abs() < 1e-9
                    && existing.description.as_deref().unwrap_or("")
                        == r.description.as_deref().unwrap_or("")
                {
                    summary.skipped_count += 1;
                } else {
                    // Update in place.
                    let mut updated = existing.clone();
                    updated.grade = r.grade;
                    updated.description = r.description.clone();
                    updated.weight = r.weight;
                    updated.term = r.term;
                    votes::update(&conn, existing.id.unwrap(), &updated)?;
                    summary.updated_count += 1;
                }
            }
            None => {
                let v = Vote {
                    id: None,
                    subject: subject.clone(),
                    grade: r.grade,
                    kind: r.kind,
                    term: r.term,
                    date: r.date.clone(),
                    description: r.description.clone(),
                    weight: r.weight,
                    school_year_id,
                };
                votes::add(&conn, &v)?;
                summary.new_count += 1;
            }
        }
    }

    Ok(summary)
}
