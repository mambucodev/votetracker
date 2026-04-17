//! Grade simulator: what grade do I need on the next vote to hit a target?
//!
//! From `database.py::calculate_needed_grade`:
//! ```
//! target = (Σ(g*w) + needed*w_new) / (Σw + w_new)
//! →  needed = (target*(Σw + w_new) − Σ(g*w)) / w_new
//! ```
//! Returns `None` if already at or above target. Caps the answer at 10.0.

pub fn calculate_needed_grade(
    current_votes: &[(f64, f64)],
    target_avg: f64,
    new_weight: f64,
) -> Option<f64> {
    let weight = if new_weight > 0.0 { new_weight } else { 1.0 };

    // If no prior votes, the needed grade IS the target.
    let total_weighted: f64 = current_votes
        .iter()
        .filter(|(g, _)| *g > 0.0)
        .map(|(g, w)| g * if *w > 0.0 { *w } else { 1.0 })
        .sum();
    let total_weight: f64 = current_votes
        .iter()
        .filter(|(g, _)| *g > 0.0)
        .map(|(_, w)| if *w > 0.0 { *w } else { 1.0 })
        .sum();

    if total_weight == 0.0 {
        return Some(target_avg.min(10.0).max(0.0));
    }

    let current_avg = total_weighted / total_weight;
    if current_avg >= target_avg {
        return None;
    }

    let needed = (target_avg * (total_weight + weight) - total_weighted) / weight;
    Some(needed.min(10.0))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn already_at_target_returns_none() {
        let votes = vec![(8.0, 1.0), (8.0, 1.0)];
        assert_eq!(calculate_needed_grade(&votes, 7.0, 1.0), None);
    }

    #[test]
    fn classic_case() {
        // Two 6s; to reach 7 on the 3rd weight-1 vote: need 9.
        let votes = vec![(6.0, 1.0), (6.0, 1.0)];
        let got = calculate_needed_grade(&votes, 7.0, 1.0).unwrap();
        assert!((got - 9.0).abs() < 1e-9);
    }

    #[test]
    fn caps_at_ten() {
        // Huge gap between current and target → needed > 10 → capped.
        let votes = vec![(4.0, 1.0)];
        let got = calculate_needed_grade(&votes, 9.0, 1.0).unwrap();
        assert_eq!(got, 10.0);
    }

    #[test]
    fn no_prior_votes_returns_target() {
        let got = calculate_needed_grade(&[], 6.5, 1.0).unwrap();
        assert_eq!(got, 6.5);
    }

    #[test]
    fn weight_of_new_vote_changes_answer() {
        // Two 6s, new vote weighted 2: need (7*5 - 12) / 2 = 11.5 → capped at 10.
        let votes = vec![(6.0, 1.0), (6.0, 1.0)];
        let got = calculate_needed_grade(&votes, 7.0, 2.0).unwrap();
        assert_eq!(got, 10.0);
    }
}
