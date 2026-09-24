use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SchoolYear {
    pub id: i64,
    pub name: String,
    pub is_active: bool,
    pub created_at: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Subject {
    pub id: i64,
    pub name: String,
    pub color: String,
    pub target_grade: f64,
    pub created_at: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Vote {
    pub id: i64,
    pub subject_id: i64,
    pub grade: f64,
    pub weight: f64,
    pub vote_date: String,
    pub term: i32,
    pub notes: String,
    pub vote_type: String,
    pub created_at: Option<String>,
    pub school_year_id: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NewVote {
    pub subject_id: i64,
    pub grade: f64,
    pub weight: f64,
    pub vote_date: String,
    pub term: i32,
    pub notes: String,
    pub vote_type: String,
    pub school_year_id: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GradeGoal {
    pub id: i64,
    pub subject_id: i64,
    pub target_grade: f64,
    pub school_year_id: i64,
    pub term: i32,
    pub notes: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GradeStatistics {
    pub average: Option<f64>,
    pub total_votes: usize,
    pub numeric_votes_count: usize,
    pub failing_count: usize,
    pub min_grade: Option<f64>,
    pub max_grade: Option<f64>,
    pub passing_rate: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GradeDistribution {
    pub failing: usize,     // < 6.0
    pub sufficient: usize,  // 6.0 - 6.99
    pub good: usize,        // 7.0 - 7.99
    pub distinct: usize,    // 8.0 - 8.99
    pub excellent: usize,   // 9.0 - 10.0
    pub non_numeric: usize, // <= 0.0
}
