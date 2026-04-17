//! Fuzzy subject matcher — scaffold.
//!
//! Full port of `legacy-python/src/votetracker/subject_matcher.py` lands in M2.
//! Today this module only exposes the confidence-threshold constant so
//! other modules can depend on its eventual surface area.

/// Results below this score are treated as "no match"; identical to the
/// Python threshold so behavior stays consistent cross-platform.
pub const MIN_CONFIDENCE: f64 = 0.6;
