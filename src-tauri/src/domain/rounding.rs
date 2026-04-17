//! Italian report-card rounding: decimals ≥ 0.5 round up, < 0.5 round down.
//!
//! Port of `legacy-python/src/votetracker/utils.py::round_report_card`:
//!
//! ```python
//! def round_report_card(average: float) -> int:
//!     if average <= 0:
//!         return 0
//!     decimal = average - int(average)
//!     return int(average) + 1 if decimal >= 0.5 else int(average)
//! ```

pub fn round_report_card(avg: f64) -> i32 {
    if avg <= 0.0 {
        return 0;
    }
    let int_part = avg.trunc() as i32;
    let decimal = avg - (int_part as f64);
    if decimal >= 0.5 {
        int_part + 1
    } else {
        int_part
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn boundary_cases() {
        assert_eq!(round_report_card(0.0), 0);
        assert_eq!(round_report_card(-1.0), 0);
        assert_eq!(round_report_card(4.49), 4);
        assert_eq!(round_report_card(4.50), 5);
        assert_eq!(round_report_card(5.50), 6);
        assert_eq!(round_report_card(7.4999), 7);
        assert_eq!(round_report_card(9.9), 10);
        assert_eq!(round_report_card(10.0), 10);
    }
}
