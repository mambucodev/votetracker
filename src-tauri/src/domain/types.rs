//! Canonical domain shapes, mirrored on the TS side.
//!
//! Keep field names in **snake_case** on the wire so React code receives them
//! unchanged — `serde_json` plus the `#[serde(rename_all = …)]` on the enum
//! yields a stable IPC contract.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub enum GradeType {
    Written,
    Oral,
    Practical,
}

impl GradeType {
    pub fn as_str(&self) -> &'static str {
        match self {
            GradeType::Written => "Written",
            GradeType::Oral => "Oral",
            GradeType::Practical => "Practical",
        }
    }

    pub fn from_str_loose(s: &str) -> Option<Self> {
        let norm = s.trim().to_ascii_lowercase();
        match norm.as_str() {
            "written" | "scritto" | "grafico" => Some(GradeType::Written),
            "oral" | "orale" => Some(GradeType::Oral),
            "practical" | "pratico" | "laboratorio" => Some(GradeType::Practical),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Vote {
    pub id: Option<i64>,
    pub subject: String,
    pub grade: f64,
    #[serde(rename = "type")]
    pub kind: GradeType,
    pub term: i32,
    pub date: String, // YYYY-MM-DD
    pub description: Option<String>,
    #[serde(default = "default_weight")]
    pub weight: f64,
    pub school_year_id: Option<i64>,
}

fn default_weight() -> f64 {
    1.0
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchoolYear {
    pub id: i64,
    pub name: String,
    pub start_year: i32,
    pub is_active: bool,
}
