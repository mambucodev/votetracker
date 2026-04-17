//! Pure decoders for the Axios HTML-scrape payloads.
//!
//! Axios returns grades as an HTML fragment inside a DataTables-style JSON
//! response. Values are sometimes hidden in a `title="… Valore: X,YZ"`
//! attribute and sometimes only present as Italian-style text (`7+`, `7½`,
//! `7,25`). These helpers isolate the quirky decoding rules so they can be
//! unit-tested in isolation from the network layer.
//!
//! See `docs/REWRITE_SPEC.md` §4.5.

use crate::domain::types::GradeType;
use once_cell::sync::Lazy;
use regex::Regex;

/// Extracts the numeric grade value from the HTML fragment returned by
/// `FAMILY_VOTI_ELENCO_LISTA`.
///
/// Precedence:
/// 1. `title="… Valore: X,YZ …"` on any element (authoritative).
/// 2. Fallback: parse the human-visible text (`7`, `7+`, `7-`, `7½`, `7,25`).
///
/// Returns `None` if no numeric value can be extracted.
pub fn decode_grade(voto_html: &str) -> Option<f64> {
    static TITLE_RE: Lazy<Regex> = Lazy::new(|| {
        // Match title="…" or title='…' containing "Valore: <number>".
        // The number uses Italian decimal comma or dot.
        Regex::new(r#"(?i)title\s*=\s*['"][^'"]*Valore\s*:\s*([0-9]+(?:[.,][0-9]+)?)"#).unwrap()
    });

    if let Some(caps) = TITLE_RE.captures(voto_html) {
        if let Some(m) = caps.get(1) {
            if let Some(v) = parse_italian_number(m.as_str()) {
                return Some(v);
            }
        }
    }

    // Fallback: strip HTML tags and look at the visible text.
    let text = strip_tags(voto_html);
    decode_grade_text(&text)
}

/// Decodes a plain (tag-free) grade string — `7`, `7+`, `7-`, `7½`,
/// `7 1/2`, `7,25`, `7.25`. Returns `None` if nothing parseable.
pub fn decode_grade_text(raw: &str) -> Option<f64> {
    let s = raw.trim();
    if s.is_empty() {
        return None;
    }

    // "7 1/2" or "7½" → n + 0.5
    if s.contains('½') {
        let base = s.replace('½', "").trim().to_string();
        if let Some(n) = parse_italian_number(&base) {
            return Some(n + 0.5);
        }
    }
    if let Some(idx) = s.find("1/2") {
        let base = s[..idx].trim();
        if let Some(n) = parse_italian_number(base) {
            return Some(n + 0.5);
        }
    }

    // "7+" → n + 0.25; "7-" / "7−" → n - 0.25.
    let trimmed = s.trim_end();
    if let Some(last) = trimmed.chars().last() {
        match last {
            '+' => {
                let base = trimmed[..trimmed.len() - last.len_utf8()].trim();
                if let Some(n) = parse_italian_number(base) {
                    return Some(n + 0.25);
                }
            }
            '-' | '−' => {
                let base = trimmed[..trimmed.len() - last.len_utf8()].trim();
                if let Some(n) = parse_italian_number(base) {
                    return Some(n - 0.25);
                }
            }
            _ => {}
        }
    }

    parse_italian_number(s)
}

/// Parses a number that may use Italian decimal comma (`7,25`) or dot
/// (`7.25`). Returns `None` on parse error.
fn parse_italian_number(s: &str) -> Option<f64> {
    let cleaned = s.trim().replace(',', ".");
    cleaned.parse::<f64>().ok()
}

/// Very small HTML-tag stripper — sufficient for the short fragments Axios
/// returns (typically `<span title="…">7+</span>`).
fn strip_tags(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    let mut in_tag = false;
    for ch in s.chars() {
        match ch {
            '<' => in_tag = true,
            '>' => in_tag = false,
            _ if !in_tag => out.push(ch),
            _ => {}
        }
    }
    out
}

/// Maps the Axios `tipo` string to our internal `GradeType`.
///
/// * `scritto` / `grafico` → Written
/// * `orale` → Oral
/// * `pratico` / `laboratorio` → Practical
///
/// Defaults to `Written` when the string doesn't match any known token,
/// matching the behaviour of the Python reference implementation.
pub fn decode_type(tipo: &str) -> GradeType {
    let t = tipo.to_ascii_lowercase();
    if t.contains("oral") {
        GradeType::Oral
    } else if t.contains("pratic") || t.contains("laborator") {
        GradeType::Practical
    } else {
        // "scritto", "grafico", or anything else.
        GradeType::Written
    }
}

/// Converts an Italian-format date `DD/MM/YYYY` into ISO `YYYY-MM-DD`.
/// Returns `None` if the input does not parse as three integer fields.
pub fn decode_date(giorno: &str) -> Option<String> {
    let parts: Vec<&str> = giorno.trim().split('/').collect();
    if parts.len() != 3 {
        return None;
    }
    let day: u32 = parts[0].parse().ok()?;
    let month: u32 = parts[1].parse().ok()?;
    let year: i32 = parts[2].parse().ok()?;
    if !(1..=12).contains(&month) || !(1..=31).contains(&day) {
        return None;
    }
    Some(format!("{:04}-{:02}-{:02}", year, month, day))
}

/// Maps an Axios term label (from `<option>` in the `fiFrazId` select)
/// onto VoteTracker's 1/2 convention.
///
/// Rules (matching the Python reference):
/// * Label contains `"PENTAMESTRE"` → Term 2.
/// * Label starts with `"2°"` → Term 2.
/// * Label contains `"TRIMESTRE"` but *not* `"PENTA"` → Term 1.
/// * Otherwise default to Term 1.
pub fn decode_term_label(label: &str) -> i32 {
    let up = label.to_ascii_uppercase();
    let trimmed_up = up.trim();
    if up.contains("PENTAMESTRE") {
        return 2;
    }
    if trimmed_up.starts_with("2°") {
        return 2;
    }
    if up.contains("TRIMESTRE") && !up.contains("PENTA") {
        return 1;
    }
    1
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn decode_grade_text_plain_integer() {
        assert_eq!(decode_grade_text("7"), Some(7.0));
    }

    #[test]
    fn decode_grade_text_plus() {
        assert_eq!(decode_grade_text("7+"), Some(7.25));
    }

    #[test]
    fn decode_grade_text_minus_ascii() {
        assert_eq!(decode_grade_text("7-"), Some(6.75));
    }

    #[test]
    fn decode_grade_text_minus_unicode() {
        // U+2212 MINUS SIGN sometimes appears instead of ASCII '-'.
        assert_eq!(decode_grade_text("7\u{2212}"), Some(6.75));
    }

    #[test]
    fn decode_grade_text_half_glyph() {
        assert_eq!(decode_grade_text("7½"), Some(7.5));
    }

    #[test]
    fn decode_grade_text_half_fraction() {
        assert_eq!(decode_grade_text("7 1/2"), Some(7.5));
    }

    #[test]
    fn decode_grade_text_italian_comma() {
        assert_eq!(decode_grade_text("7,25"), Some(7.25));
    }

    #[test]
    fn decode_grade_text_dot() {
        assert_eq!(decode_grade_text("7.25"), Some(7.25));
    }

    #[test]
    fn decode_grade_text_blank() {
        assert_eq!(decode_grade_text(""), None);
        assert_eq!(decode_grade_text("   "), None);
    }

    #[test]
    fn decode_grade_title_wins_over_text() {
        // Visible "7+" would be 7.25, but title authoritative says 7,30.
        let html = r#"<span title="Voto: 7+ ... Valore: 7,30">7+</span>"#;
        assert_eq!(decode_grade(html), Some(7.30));
    }

    #[test]
    fn decode_grade_title_with_dot() {
        let html = r#"<span title='Valore: 6.5'>6½</span>"#;
        assert_eq!(decode_grade(html), Some(6.5));
    }

    #[test]
    fn decode_grade_falls_back_to_text_when_no_title() {
        let html = "<span>7+</span>";
        assert_eq!(decode_grade(html), Some(7.25));
    }

    #[test]
    fn decode_grade_returns_none_for_empty() {
        assert_eq!(decode_grade(""), None);
        assert_eq!(decode_grade("<span></span>"), None);
    }

    #[test]
    fn decode_type_written() {
        assert!(matches!(decode_type("Scritto"), GradeType::Written));
        assert!(matches!(decode_type("grafico"), GradeType::Written));
    }

    #[test]
    fn decode_type_oral() {
        assert!(matches!(decode_type("Orale"), GradeType::Oral));
    }

    #[test]
    fn decode_type_practical() {
        assert!(matches!(decode_type("Pratico"), GradeType::Practical));
        assert!(matches!(decode_type("laboratorio"), GradeType::Practical));
    }

    #[test]
    fn decode_type_defaults_to_written() {
        assert!(matches!(decode_type("unknown"), GradeType::Written));
        assert!(matches!(decode_type(""), GradeType::Written));
    }

    #[test]
    fn decode_date_valid() {
        assert_eq!(decode_date("15/10/2024"), Some("2024-10-15".to_string()));
    }

    #[test]
    fn decode_date_pads_single_digits() {
        assert_eq!(decode_date("1/2/2024"), Some("2024-02-01".to_string()));
    }

    #[test]
    fn decode_date_invalid() {
        assert_eq!(decode_date("2024-10-15"), None); // ISO, not Italian
        assert_eq!(decode_date(""), None);
        assert_eq!(decode_date("15/13/2024"), None); // month out of range
        assert_eq!(decode_date("abc/def/ghi"), None);
    }

    #[test]
    fn decode_term_label_trimestre_is_1() {
        assert_eq!(decode_term_label("1° TRIMESTRE"), 1);
        assert_eq!(decode_term_label("Trimestre"), 1);
    }

    #[test]
    fn decode_term_label_pentamestre_is_2() {
        assert_eq!(decode_term_label("PENTAMESTRE"), 2);
        assert_eq!(decode_term_label("2° Pentamestre"), 2);
    }

    #[test]
    fn decode_term_label_starts_with_2_degree_is_2() {
        assert_eq!(decode_term_label("2° Quadrimestre"), 2);
    }

    #[test]
    fn decode_term_label_unknown_defaults_to_1() {
        assert_eq!(decode_term_label(""), 1);
        assert_eq!(decode_term_label("foo bar"), 1);
    }
}
