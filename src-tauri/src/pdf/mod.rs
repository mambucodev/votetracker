//! Report-card PDF export — pure-Rust via `printpdf`.
//!
//! Layout mirrors `legacy-python/src/votetracker/pages/report_card.py`:
//! A4 portrait, header with school year + term + timestamp, table of
//! subjects with the rounded final grade (optionally split into
//! Written / Oral averages), footer credit.

pub mod report_card;
