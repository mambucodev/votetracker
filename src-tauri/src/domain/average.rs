//! Weighted average with Italian `+/-` exclusion.
//!
//! Port of `legacy-python/src/votetracker/utils.py::calc_average`:
//!
//! ```python
//! def calc_average(votes):
//!     valid = [v for v in votes if v.get("grade", 0) > 0]
//!     if not valid:
//!         return 0.0
//!     total = sum(v["grade"] * v.get("weight", 1.0) for v in valid)
//!     weights = sum(v.get("weight", 1.0) for v in valid)
//!     return total / weights if weights > 0 else 0.0
//! ```
//!
//! `+` / `−` marks are stored as `grade = 0.0` and must not skew averages.

use crate::domain::types::Vote;

pub fn calc_average(votes: &[Vote]) -> f64 {
    let mut sum = 0.0;
    let mut weights = 0.0;
    for v in votes {
        if v.grade <= 0.0 {
            continue;
        }
        let w = if v.weight > 0.0 { v.weight } else { 1.0 };
        sum += v.grade * w;
        weights += w;
    }
    if weights > 0.0 {
        sum / weights
    } else {
        0.0
    }
}

/// Same shape as the Python helper but for arbitrary `(grade, weight)` pairs —
/// useful in the simulator and in statistics where we don't have full `Vote`s.
pub fn calc_average_pairs(pairs: &[(f64, f64)]) -> f64 {
    let mut sum = 0.0;
    let mut weights = 0.0;
    for &(g, w) in pairs {
        if g <= 0.0 {
            continue;
        }
        let w = if w > 0.0 { w } else { 1.0 };
        sum += g * w;
        weights += w;
    }
    if weights > 0.0 {
        sum / weights
    } else {
        0.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::types::GradeType;

    fn v(grade: f64, weight: f64) -> Vote {
        Vote {
            id: None,
            subject: "Math".into(),
            grade,
            kind: GradeType::Written,
            term: 1,
            date: "2026-01-01".into(),
            description: None,
            weight,
            school_year_id: None,
        }
    }

    #[test]
    fn empty_is_zero() {
        assert_eq!(calc_average(&[]), 0.0);
    }

    #[test]
    fn excludes_zero_grade_marks() {
        let votes = vec![v(8.0, 1.0), v(0.0, 1.0), v(6.0, 1.0)];
        assert_eq!(calc_average(&votes), 7.0);
    }

    #[test]
    fn weighted_average() {
        // (8*2 + 6*1) / (2+1) = 22/3 ≈ 7.333…
        let votes = vec![v(8.0, 2.0), v(6.0, 1.0)];
        assert!((calc_average(&votes) - 22.0 / 3.0).abs() < 1e-9);
    }

    #[test]
    fn all_weights_zero_falls_back_to_one() {
        let votes = vec![v(8.0, 0.0), v(6.0, 0.0)];
        assert_eq!(calc_average(&votes), 7.0);
    }

    #[test]
    fn pairs_mirror_vote_behavior() {
        assert_eq!(
            calc_average_pairs(&[(8.0, 2.0), (6.0, 1.0), (0.0, 1.0)]),
            22.0 / 3.0
        );
    }
}
