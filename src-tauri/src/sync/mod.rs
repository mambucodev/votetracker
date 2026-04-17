//! Sync provider trait + registry + import engine.
//!
//! Providers return a uniform `RawGrade` list; the import engine maps
//! subjects via settings, matches `(subject, date, type)` to decide
//! new / updated / skipped, and writes to the DB.

pub mod axios;
pub mod axios_decode;
pub mod classeviva;
pub mod import;

use crate::domain::types::GradeType;
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CredentialField {
    pub name: String,
    pub label: String,
    #[serde(rename = "type")]
    pub kind: String, // "text" | "password"
}

#[derive(Debug, Clone, Serialize)]
pub struct RawGrade {
    pub subject: String,
    pub grade: f64,
    #[serde(rename = "type")]
    pub kind: GradeType,
    pub date: String, // YYYY-MM-DD
    pub description: Option<String>,
    pub weight: f64,
    pub term: i32,
}

#[derive(Debug, thiserror::Error)]
pub enum SyncError {
    #[error("network: {0}")]
    Network(#[from] reqwest::Error),
    #[error("auth failed: {0}")]
    Auth(String),
    #[error("parse: {0}")]
    Parse(String),
    #[error("io: {0}")]
    Io(String),
}

#[async_trait]
pub trait SyncProvider: Send + Sync {
    fn id(&self) -> &'static str;
    fn display_name(&self) -> &'static str;
    fn credential_fields(&self) -> Vec<CredentialField>;
    fn mapping_prefix(&self) -> &'static str;

    async fn login(&mut self, creds: &HashMap<String, String>) -> Result<String, SyncError>;
    async fn fetch_grades(&self) -> Result<Vec<RawGrade>, SyncError>;
}

pub fn provider_by_id(id: &str) -> Option<Box<dyn SyncProvider>> {
    match id {
        "classeviva" => Some(Box::new(classeviva::ClasseVivaProvider::new())),
        "axios" => Some(Box::new(axios::AxiosProvider::new())),
        _ => None,
    }
}

pub fn all_provider_ids() -> &'static [&'static str] {
    &["classeviva", "axios"]
}
