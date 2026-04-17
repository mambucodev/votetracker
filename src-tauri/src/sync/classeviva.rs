//! ClasseViva (Spaggiari) REST provider.
//!
//! Port of `legacy-python/src/votetracker/classeviva.py`.

use super::{CredentialField, RawGrade, SyncError, SyncProvider};
use crate::domain::types::GradeType;
use async_trait::async_trait;
use reqwest::header::{HeaderMap, HeaderValue, CONTENT_TYPE, USER_AGENT};
use serde::Deserialize;
use std::collections::HashMap;

const BASE: &str = "https://web.spaggiari.eu/rest/v1";
const API_KEY: &str = "Tg1NWEwNGIgIC0K";
const UA: &str = "CVVS/std/4.2.3 Android/12";

pub struct ClasseVivaProvider {
    token: Option<String>,
    ident: Option<String>,
    display_name: Option<String>,
    client: reqwest::Client,
}

impl ClasseVivaProvider {
    pub fn new() -> Self {
        Self {
            token: None,
            ident: None,
            display_name: None,
            client: reqwest::Client::builder()
                .user_agent(UA)
                .build()
                .unwrap_or_default(),
        }
    }

    fn headers(&self, with_token: bool) -> HeaderMap {
        let mut h = HeaderMap::new();
        h.insert(USER_AGENT, HeaderValue::from_static(UA));
        h.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
        h.insert("Z-Dev-ApiKey", HeaderValue::from_static(API_KEY));
        if with_token {
            if let Some(t) = &self.token {
                if let Ok(v) = HeaderValue::from_str(t) {
                    h.insert("Z-Auth-Token", v);
                }
            }
        }
        h
    }
}

#[derive(Deserialize)]
struct LoginResponse {
    token: String,
    ident: String,
    #[serde(default, rename = "firstName")]
    first_name: String,
    #[serde(default, rename = "lastName")]
    last_name: String,
}

#[derive(Deserialize)]
struct GradesResponse {
    grades: Vec<ApiGrade>,
}

#[derive(Deserialize)]
struct ApiGrade {
    #[serde(default)]
    decimal_value: Option<f64>,
    #[serde(default, rename = "decimalValue")]
    decimal_value_camel: Option<f64>,
    #[serde(default, rename = "subjectDesc")]
    subject_desc: String,
    #[serde(default, rename = "componentDesc")]
    component_desc: String,
    #[serde(default, rename = "notesForFamily")]
    notes_for_family: Option<String>,
    #[serde(default, rename = "evtDate")]
    evt_date: Option<String>,
    #[serde(default, rename = "weightFactor")]
    weight_factor: Option<f64>,
    #[serde(default, rename = "periodPos")]
    period_pos: Option<i32>,
    #[serde(default)]
    canceled: Option<bool>,
}

#[async_trait]
impl SyncProvider for ClasseVivaProvider {
    fn id(&self) -> &'static str {
        "classeviva"
    }
    fn display_name(&self) -> &'static str {
        "ClasseViva"
    }
    fn mapping_prefix(&self) -> &'static str {
        "cv"
    }
    fn credential_fields(&self) -> Vec<CredentialField> {
        vec![
            CredentialField {
                name: "username".into(),
                label: "Username (S-code)".into(),
                kind: "text".into(),
            },
            CredentialField {
                name: "password".into(),
                label: "Password".into(),
                kind: "password".into(),
            },
        ]
    }

    async fn login(&mut self, creds: &HashMap<String, String>) -> Result<String, SyncError> {
        let username = creds
            .get("username")
            .cloned()
            .ok_or_else(|| SyncError::Auth("missing username".into()))?;
        let password = creds
            .get("password")
            .cloned()
            .ok_or_else(|| SyncError::Auth("missing password".into()))?;

        let payload = serde_json::json!({
            "ident": serde_json::Value::Null,
            "uid": username,
            "pass": password,
        });

        let resp = self
            .client
            .post(format!("{BASE}/auth/login"))
            .headers(self.headers(false))
            .json(&payload)
            .send()
            .await?;

        if !resp.status().is_success() {
            return Err(SyncError::Auth(format!(
                "HTTP {} from ClasseViva login",
                resp.status()
            )));
        }

        let body: LoginResponse = resp.json().await?;
        self.token = Some(body.token);
        self.ident = Some(body.ident.clone());
        let name = format!("{} {}", body.first_name, body.last_name).trim().to_string();
        self.display_name = Some(name.clone());
        Ok(name)
    }

    async fn fetch_grades(&self) -> Result<Vec<RawGrade>, SyncError> {
        let ident = self
            .ident
            .as_ref()
            .ok_or_else(|| SyncError::Auth("not logged in".into()))?
            .clone();
        // ClasseViva returns ident with an "S" prefix; the grades endpoint
        // uses it verbatim.
        let path = format!("{BASE}/students/{ident}/grades");
        let resp = self
            .client
            .get(path)
            .headers(self.headers(true))
            .send()
            .await?;

        if !resp.status().is_success() {
            return Err(SyncError::Parse(format!(
                "HTTP {} fetching grades",
                resp.status()
            )));
        }

        let body: GradesResponse = resp
            .json()
            .await
            .map_err(|e| SyncError::Parse(e.to_string()))?;

        let grades = body
            .grades
            .into_iter()
            .filter(|g| !g.canceled.unwrap_or(false))
            .filter_map(|g| {
                let value = g.decimal_value.or(g.decimal_value_camel).unwrap_or(0.0);
                let kind = map_kind(&g.component_desc);
                let term = if g.period_pos.unwrap_or(1) > 1 { 2 } else { 1 };
                Some(RawGrade {
                    subject: g.subject_desc,
                    grade: value,
                    kind,
                    date: g.evt_date.unwrap_or_default(),
                    description: g.notes_for_family,
                    weight: g.weight_factor.unwrap_or(1.0),
                    term,
                })
            })
            .collect();

        Ok(grades)
    }
}

fn map_kind(desc: &str) -> GradeType {
    let d = desc.to_ascii_lowercase();
    if d.contains("oral") {
        GradeType::Oral
    } else if d.contains("laborator") || d.contains("pratic") {
        GradeType::Practical
    } else {
        GradeType::Written
    }
}
