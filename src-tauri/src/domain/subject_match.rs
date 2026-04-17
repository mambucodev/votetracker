//! Fuzzy subject matcher — port of
//! `legacy-python/src/votetracker/subject_matcher.py`.
//!
//! The confidence ladder is identical to the Python table:
//!   1.00  — exact normalized match
//!   0.90  — substring containment either direction
//!   0.85  — both names hit the same keyword group
//!   0.80  — VT is canonical name, source hits canonical's keyword group
//!   ≤0.70 — Jaccard word overlap * 0.7
//! Anything ≤ 0.60 is "no match".

use once_cell::sync::Lazy;
use serde::Serialize;
use std::collections::{HashMap, HashSet};

pub const MIN_CONFIDENCE: f64 = 0.6;

/// Canonical subject → Italian/English keyword list. Ordering is preserved
/// so iteration behavior matches the Python dict.
static SUBJECT_KEYWORDS: Lazy<Vec<(&'static str, &'static [&'static str])>> =
    Lazy::new(|| {
        vec![
            ("Math", &["matematica", "math", "algebra", "geometria"] as &[_]),
            ("Italian", &["italiano", "italian", "lingua italiana"]),
            (
                "English",
                &["inglese", "english", "lingua inglese", "lingua e cultura inglese"],
            ),
            ("History", &["storia", "history"]),
            ("Philosophy", &["filosofia", "philosophy"]),
            ("Physics", &["fisica", "physics"]),
            ("Science", &["scienze", "science", "scienze naturali"]),
            ("Chemistry", &["chimica", "chemistry"]),
            ("Biology", &["biologia", "biology"]),
            ("Latin", &["latino", "latin", "lingua latina"]),
            ("Greek", &["greco", "greek", "lingua greca"]),
            ("Art", &["arte", "art", "storia dell'arte", "disegno"]),
            (
                "Physical Education",
                &[
                    "educazione fisica",
                    "physical education",
                    "ed. fisica",
                    "scienze motorie",
                ],
            ),
            (
                "Computer Science",
                &["informatica", "computer science", "info"],
            ),
            ("Religion", &["religione", "religion", "irc"]),
            ("Geography", &["geografia", "geography"]),
            ("Spanish", &["spagnolo", "spanish", "lingua spagnola"]),
            ("French", &["francese", "french", "lingua francese"]),
            ("German", &["tedesco", "german", "lingua tedesca"]),
        ]
    });

pub fn normalize(subject: &str) -> String {
    subject.trim().to_lowercase()
}

/// Best VT subject match for a source (provider-side) subject name.
/// Returns `None` if the best score is ≤ `MIN_CONFIDENCE`.
pub fn find_best_match<'a>(
    source_subject: &str,
    vt_subjects: &'a [String],
) -> Option<(&'a str, f64)> {
    let cv_norm = normalize(source_subject);
    let mut best: Option<(&str, f64)> = None;

    for vt in vt_subjects {
        let vt_norm = normalize(vt);
        let mut score: f64 = 0.0;

        if cv_norm == vt_norm {
            return Some((vt.as_str(), 1.0));
        }

        if cv_norm.contains(&vt_norm) || vt_norm.contains(&cv_norm) {
            score = 0.9;
        }

        // 0.85 — both names hit the same keyword group.
        for (_, kws) in SUBJECT_KEYWORDS.iter() {
            let cv_in = kws.iter().any(|kw| cv_norm.contains(kw));
            let vt_in = kws.iter().any(|kw| vt_norm.contains(kw));
            if cv_in && vt_in {
                score = score.max(0.85);
                break;
            }
        }

        // 0.80 — VT is canonical, source hits canonical's keyword group.
        for (canonical, kws) in SUBJECT_KEYWORDS.iter() {
            if normalize(vt) == normalize(canonical)
                && kws.iter().any(|kw| cv_norm.contains(kw))
            {
                score = score.max(0.8);
                break;
            }
        }

        // 0.7 * Jaccard on word sets.
        let cv_words: HashSet<&str> = cv_norm.split_whitespace().collect();
        let vt_words: HashSet<&str> = vt_norm.split_whitespace().collect();
        if !cv_words.is_empty() && !vt_words.is_empty() {
            let overlap = cv_words.intersection(&vt_words).count() as f64;
            let total = cv_words.union(&vt_words).count() as f64;
            if total > 0.0 {
                score = score.max((overlap / total) * 0.7);
            }
        }

        if score > best.map(|b| b.1).unwrap_or(0.0) {
            best = Some((vt.as_str(), score));
        }
    }

    match best {
        Some((_, s)) if s > MIN_CONFIDENCE => best,
        _ => None,
    }
}

/// Try to map a raw source subject onto a canonical VT subject name via
/// the keyword dictionary, independent of any existing subjects.
pub fn suggest_canonical(source_subject: &str) -> Option<&'static str> {
    let cv_norm = normalize(source_subject);
    for (canonical, kws) in SUBJECT_KEYWORDS.iter() {
        if kws.iter().any(|kw| cv_norm.contains(kw)) {
            return Some(*canonical);
        }
    }
    None
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum MappingAction {
    Map,
    Create,
    Manual,
}

#[derive(Debug, Clone, Serialize)]
pub struct AutoSuggestion {
    pub suggested_match: Option<String>,
    pub confidence: f64,
    pub suggested_new: Option<String>,
    pub action: MappingAction,
}

pub fn auto_suggestion(source_subject: &str, vt_subjects: &[String]) -> AutoSuggestion {
    let mut out = AutoSuggestion {
        suggested_match: None,
        confidence: 0.0,
        suggested_new: None,
        action: MappingAction::Manual,
    };

    let mut confidence = 0.0;
    if let Some((name, c)) = find_best_match(source_subject, vt_subjects) {
        out.suggested_match = Some(name.to_string());
        out.confidence = c;
        confidence = c;
        out.action = if c > 0.8 {
            MappingAction::Map
        } else {
            MappingAction::Manual
        };
    }

    if out.suggested_match.is_none() || confidence < 0.8 {
        if let Some(canonical) = suggest_canonical(source_subject) {
            out.suggested_new = Some(canonical.to_string());
            if out.suggested_match.is_none() || confidence < 0.7 {
                out.action = MappingAction::Create;
            }
        }
    }

    out
}

/// Build a provider-agnostic mapping proposal in bulk. Useful for the
/// SubjectMappingDialog seed.
pub fn propose_mappings(
    source_subjects: &[String],
    vt_subjects: &[String],
) -> HashMap<String, AutoSuggestion> {
    let mut out = HashMap::with_capacity(source_subjects.len());
    for s in source_subjects {
        out.insert(s.clone(), auto_suggestion(s, vt_subjects));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn v<const N: usize>(names: [&str; N]) -> Vec<String> {
        names.into_iter().map(String::from).collect()
    }

    #[test]
    fn exact_match_scores_one() {
        let subjects = v(["Math", "Italian"]);
        let m = find_best_match("Math", &subjects).unwrap();
        assert_eq!(m.0, "Math");
        assert_eq!(m.1, 1.0);
    }

    #[test]
    fn matematica_maps_to_math_via_keywords() {
        let subjects = v(["Math", "Italian"]);
        let m = find_best_match("MATEMATICA", &subjects).unwrap();
        assert_eq!(m.0, "Math");
        // canonical-name keyword branch → 0.8 floor
        assert!(m.1 >= 0.8);
    }

    #[test]
    fn substring_scores_point_nine() {
        let subjects = v(["Math"]);
        let m = find_best_match("Mathematics", &subjects).unwrap();
        assert_eq!(m.0, "Math");
        assert!(m.1 >= 0.9);
    }

    #[test]
    fn no_match_when_below_threshold() {
        let subjects = v(["Math", "Italian"]);
        // `Cooking` has no keyword relation and no overlap with existing subjects.
        assert!(find_best_match("Cooking", &subjects).is_none());
    }

    #[test]
    fn suggest_canonical_for_italian_subjects() {
        // The Python implementation iterates the keyword dict in insertion order
        // and returns on the FIRST hit, so ambiguous inputs favor whichever
        // canonical comes first. We port this behavior verbatim — fixing these
        // quirks is tracked as tech debt.
        assert_eq!(suggest_canonical("EDUCAZIONE FISICA"), Some("Physics"));
        assert_eq!(suggest_canonical("STORIA DELL'ARTE"), Some("History"));
        assert_eq!(suggest_canonical("IRC"), Some("Religion"));

        // Unambiguous cases still work as expected.
        assert_eq!(suggest_canonical("INFORMATICA"), Some("Computer Science"));
        assert_eq!(suggest_canonical("RELIGIONE"), Some("Religion"));
    }

    #[test]
    fn auto_suggestion_dispatches_action() {
        let subjects = v(["Math"]);

        // Map: existing VT subject matches with high confidence.
        let s = auto_suggestion("MATEMATICA", &subjects);
        assert_eq!(s.suggested_match.as_deref(), Some("Math"));
        assert_eq!(s.action, MappingAction::Map);

        // Create: no existing but canonical keyword hit.
        let s = auto_suggestion("STORIA", &subjects);
        assert_eq!(s.suggested_new.as_deref(), Some("History"));
        assert_eq!(s.action, MappingAction::Create);

        // Manual: nothing matches at all.
        let s = auto_suggestion("Zzz Alien Dialect", &subjects);
        assert_eq!(s.action, MappingAction::Manual);
    }
}
