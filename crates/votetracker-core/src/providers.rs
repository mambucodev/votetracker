use std::collections::HashMap;

use crate::db::{Database, DbError};
use crate::models::NewVote;

#[derive(Debug, Clone, PartialEq)]
pub struct RawGrade {
    pub subject: String,
    pub grade: f64,
    pub date: String,
    pub vote_type: String,
    pub notes: String,
    pub weight: f64,
    pub term: i32,
}

#[derive(Debug, Default, Clone, PartialEq)]
pub struct SyncSummary {
    pub added: usize,
    pub updated: usize,
    pub skipped: usize,
    pub unmapped_subjects: Vec<String>,
}

/// Syncs a list of raw grades imported from an electronic register into the database,
/// strictly following the import duplicate resolution rules:
/// 1. Match by (subject_id, date, type).
/// 2. If matched but grade, weight, or description differs: UPDATE.
/// 3. If exact match: SKIP.
/// 4. If not found: ADD.
pub fn sync_raw_grades(
    db: &mut Database,
    grades: &[RawGrade],
    subject_mapping: &HashMap<String, i64>,
    school_year_id: i64,
) -> Result<SyncSummary, DbError> {
    let mut summary = SyncSummary::default();

    for raw in grades {
        let subject_id = match subject_mapping.get(&raw.subject) {
            Some(&id) => id,
            None => {
                if !summary.unmapped_subjects.contains(&raw.subject) {
                    summary.unmapped_subjects.push(raw.subject.clone());
                }
                continue;
            }
        };

        let existing = db.find_vote_by_metadata(
            subject_id,
            &raw.date,
            &raw.vote_type,
            school_year_id,
        )?;

        match existing {
            Some(mut existing_vote) => {
                let grade_differs = (existing_vote.grade - raw.grade).abs() > 1e-4;
                let weight_differs = (existing_vote.weight - raw.weight).abs() > 1e-4;
                let notes_differ = existing_vote.notes != raw.notes;

                if grade_differs || weight_differs || notes_differ {
                    existing_vote.grade = raw.grade;
                    existing_vote.weight = raw.weight;
                    existing_vote.notes = raw.notes.clone();
                    existing_vote.term = raw.term;

                    db.update_vote(&existing_vote)?;
                    summary.updated += 1;
                } else {
                    summary.skipped += 1;
                }
            }
            None => {
                let new_vote = NewVote {
                    subject_id,
                    grade: raw.grade,
                    weight: raw.weight,
                    vote_date: raw.date.clone(),
                    term: raw.term,
                    notes: raw.notes.clone(),
                    vote_type: raw.vote_type.clone(),
                    school_year_id,
                };
                db.add_vote(&new_vote)?;
                summary.added += 1;
            }
        }
    }

    Ok(summary)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sync_duplicate_detection_rules() {
        let mut db = Database::new::<&str>(None).unwrap();
        let subjects = db.get_subjects().unwrap();
        let it_id = subjects[0].id;
        let year_id = db.get_active_school_year().unwrap().unwrap().id;

        let mut mapping = HashMap::new();
        mapping.insert("ITALIANO".to_string(), it_id);

        let grades = vec![
            RawGrade {
                subject: "ITALIANO".to_string(),
                grade: 8.0,
                date: "2026-03-10".to_string(),
                vote_type: "Scritto".to_string(),
                notes: "Tema".to_string(),
                weight: 1.0,
                term: 2,
            },
        ];

        // 1. Initial import -> ADD
        let res1 = sync_raw_grades(&mut db, &grades, &mapping, year_id).unwrap();
        assert_eq!(res1.added, 1);
        assert_eq!(res1.updated, 0);
        assert_eq!(res1.skipped, 0);

        // 2. Exact same import -> SKIP
        let res2 = sync_raw_grades(&mut db, &grades, &mapping, year_id).unwrap();
        assert_eq!(res2.added, 0);
        assert_eq!(res2.updated, 0);
        assert_eq!(res2.skipped, 1);

        // 3. Changed grade -> UPDATE
        let updated_grades = vec![
            RawGrade {
                subject: "ITALIANO".to_string(),
                grade: 8.5, // teacher updated grade
                date: "2026-03-10".to_string(),
                vote_type: "Scritto".to_string(),
                notes: "Tema".to_string(),
                weight: 1.0,
                term: 2,
            },
        ];

        let res3 = sync_raw_grades(&mut db, &updated_grades, &mapping, year_id).unwrap();
        assert_eq!(res3.added, 0);
        assert_eq!(res3.updated, 1);
        assert_eq!(res3.skipped, 0);

        let vote = db.find_vote_by_metadata(it_id, "2026-03-10", "Scritto", year_id).unwrap().unwrap();
        assert_eq!(vote.grade, 8.5);
    }
}
