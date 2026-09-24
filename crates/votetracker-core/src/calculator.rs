use crate::models::{GradeDistribution, GradeStatistics, Vote};

/// Calculates the weighted average of grades, strictly ignoring grades <= 0.0.
/// Non-numeric +/- marks (grade <= 0.0) must never affect averages.
pub fn calculate_weighted_average(votes: &[Vote]) -> Option<f64> {
    let numeric_votes: Vec<&Vote> = votes.iter().filter(|v| v.grade > 0.0).collect();
    if numeric_votes.is_empty() {
        return None;
    }

    let total_weighted: f64 = numeric_votes.iter().map(|v| v.grade * v.weight).sum();
    let total_weight: f64 = numeric_votes.iter().map(|v| v.weight).sum();

    if total_weight > 0.0 {
        Some(total_weighted / total_weight)
    } else {
        None
    }
}

/// Counts failing grades (< 6.0), strictly excluding non-numeric marks (<= 0.0).
pub fn count_failing(votes: &[Vote]) -> usize {
    votes.iter().filter(|v| v.grade > 0.0 && v.grade < 6.0).count()
}

/// Calculates the grade needed on an upcoming assignment with `weight_new`
/// to reach `target_avg`.
///
/// Formula: (target_avg * (total_weight + weight_new) - total_weighted) / weight_new
pub fn calculate_needed_grade(
    current_votes: &[Vote],
    target_avg: f64,
    weight_new: f64,
) -> Option<f64> {
    if weight_new <= 0.0 {
        return None;
    }

    let numeric_votes: Vec<&Vote> = current_votes.iter().filter(|v| v.grade > 0.0).collect();
    let total_weighted: f64 = numeric_votes.iter().map(|v| v.grade * v.weight).sum();
    let total_weight: f64 = numeric_votes.iter().map(|v| v.weight).sum();

    let needed = (target_avg * (total_weight + weight_new) - total_weighted) / weight_new;
    Some(needed)
}

/// Simulates a scenario with current votes plus hypothetical `(grade, weight)` pairs.
/// Hypothetical grades <= 0.0 are ignored.
pub fn simulate_scenario(
    current_votes: &[Vote],
    hypothetical_grades: &[(f64, f64)],
) -> Option<f64> {
    let mut total_weighted = 0.0;
    let mut total_weight = 0.0;

    for v in current_votes.iter().filter(|v| v.grade > 0.0) {
        total_weighted += v.grade * v.weight;
        total_weight += v.weight;
    }

    for &(grade, weight) in hypothetical_grades {
        if grade > 0.0 && weight > 0.0 {
            total_weighted += grade * weight;
            total_weight += weight;
        }
    }

    if total_weight > 0.0 {
        Some(total_weighted / total_weight)
    } else {
        None
    }
}

/// Calculates full grade statistics for a slice of votes.
pub fn calculate_statistics(votes: &[Vote]) -> GradeStatistics {
    let numeric_votes: Vec<&Vote> = votes.iter().filter(|v| v.grade > 0.0).collect();
    let total_votes = votes.len();
    let numeric_count = numeric_votes.len();

    if numeric_count == 0 {
        return GradeStatistics {
            average: None,
            total_votes,
            numeric_votes_count: 0,
            failing_count: 0,
            min_grade: None,
            max_grade: None,
            passing_rate: 0.0,
        };
    }

    let total_weighted: f64 = numeric_votes.iter().map(|v| v.grade * v.weight).sum();
    let total_weight: f64 = numeric_votes.iter().map(|v| v.weight).sum();
    let average = if total_weight > 0.0 {
        Some(total_weighted / total_weight)
    } else {
        None
    };

    let failing_count = numeric_votes.iter().filter(|v| v.grade < 6.0).count();
    let passing_count = numeric_count - failing_count;
    let passing_rate = (passing_count as f64 / numeric_count as f64) * 100.0;

    let min_grade = numeric_votes
        .iter()
        .map(|v| v.grade)
        .fold(f64::INFINITY, f64::min);
    let max_grade = numeric_votes
        .iter()
        .map(|v| v.grade)
        .fold(f64::NEG_INFINITY, f64::max);

    GradeStatistics {
        average,
        total_votes,
        numeric_votes_count: numeric_count,
        failing_count,
        min_grade: Some(min_grade),
        max_grade: Some(max_grade),
        passing_rate,
    }
}

/// Groups grades into standard performance tiers.
pub fn grade_distribution(votes: &[Vote]) -> GradeDistribution {
    let mut dist = GradeDistribution {
        failing: 0,
        sufficient: 0,
        good: 0,
        distinct: 0,
        excellent: 0,
        non_numeric: 0,
    };

    for v in votes {
        if v.grade <= 0.0 {
            dist.non_numeric += 1;
        } else if v.grade < 6.0 {
            dist.failing += 1;
        } else if v.grade < 7.0 {
            dist.sufficient += 1;
        } else if v.grade < 8.0 {
            dist.good += 1;
        } else if v.grade < 9.0 {
            dist.distinct += 1;
        } else {
            dist.excellent += 1;
        }
    }

    dist
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_vote(grade: f64, weight: f64) -> Vote {
        Vote {
            id: 1,
            subject_id: 1,
            grade,
            weight,
            vote_date: "2026-01-15".to_string(),
            term: 1,
            notes: String::new(),
            vote_type: "Scritto".to_string(),
            created_at: None,
            school_year_id: 1,
        }
    }

    #[test]
    fn test_zero_grade_invariants() {
        let votes = vec![
            make_vote(8.0, 1.0),
            make_vote(6.0, 1.0),
            make_vote(0.0, 1.0),  // +/- mark
            make_vote(-1.0, 1.0), // invalid mark
        ];

        let avg = calculate_weighted_average(&votes).unwrap();
        assert_eq!(avg, 7.0);

        let failing = count_failing(&votes);
        assert_eq!(failing, 0, "Zero grades must never count as failing");

        let stats = calculate_statistics(&votes);
        assert_eq!(stats.total_votes, 4);
        assert_eq!(stats.numeric_votes_count, 2);
        assert_eq!(stats.failing_count, 0);
        assert_eq!(stats.min_grade, Some(6.0));
        assert_eq!(stats.max_grade, Some(8.0));
        assert_eq!(stats.passing_rate, 100.0);
    }

    #[test]
    fn test_needed_grade_calculation() {
        let votes = vec![make_vote(5.0, 1.0), make_vote(6.0, 1.0)];
        // Current avg: 5.5 (sum=11, weight=2). Want 6.0 with weight 1.0.
        // needed = (6.0 * 3 - 11) / 1.0 = 7.0
        let needed = calculate_needed_grade(&votes, 6.0, 1.0).unwrap();
        assert!((needed - 7.0).abs() < 1e-6);
    }

    #[test]
    fn test_simulate_scenario() {
        let votes = vec![make_vote(6.0, 1.0)];
        let hypothetical = vec![(8.0, 1.0), (10.0, 1.0), (0.0, 1.0)];
        // Total sum = 6 + 8 + 10 = 24. Total weight = 3. Avg = 8.0
        let sim_avg = simulate_scenario(&votes, &hypothetical).unwrap();
        assert_eq!(sim_avg, 8.0);
    }
}
