//! Axios (axioscloud) HTML-scrape provider — scaffolded with the full
//! login + grade-list contract documented in `docs/REWRITE_SPEC.md`.
//!
//! This is the minimum viable skeleton — it exposes `SyncProvider` so
//! the registry + Settings UI work today. Bringing the Python scraper's
//! quirks (grade-symbol decoder, multi-term page, `_AXToken` regex) across
//! is follow-up work; until then `fetch_grades` returns `Ok(vec![])` after
//! a successful auth handshake so the UI can still test the wiring.

use super::{CredentialField, RawGrade, SyncError, SyncProvider};
use async_trait::async_trait;
use reqwest::{cookie::Jar, Client};
use std::collections::HashMap;
use std::sync::Arc;

const LOGIN_URL: &str = "https://registrofamiglie.axioscloud.it/Pages/SD/SD_Login.aspx";

pub struct AxiosProvider {
    client: Client,
    authenticated: bool,
}

impl AxiosProvider {
    pub fn new() -> Self {
        let jar = Arc::new(Jar::default());
        let client = Client::builder()
            .cookie_provider(jar)
            .user_agent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
            .build()
            .unwrap_or_default();
        Self {
            client,
            authenticated: false,
        }
    }
}

#[async_trait]
impl SyncProvider for AxiosProvider {
    fn id(&self) -> &'static str {
        "axios"
    }
    fn display_name(&self) -> &'static str {
        "Axios"
    }
    fn mapping_prefix(&self) -> &'static str {
        "axios"
    }
    fn credential_fields(&self) -> Vec<CredentialField> {
        vec![
            CredentialField {
                name: "customer_id".into(),
                label: "Customer ID (school tax code)".into(),
                kind: "text".into(),
            },
            CredentialField {
                name: "username".into(),
                label: "Email / Username".into(),
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
        let customer_id = creds
            .get("customer_id")
            .cloned()
            .ok_or_else(|| SyncError::Auth("missing customer_id".into()))?;
        let username = creds
            .get("username")
            .cloned()
            .ok_or_else(|| SyncError::Auth("missing username".into()))?;
        let password = creds
            .get("password")
            .cloned()
            .ok_or_else(|| SyncError::Auth("missing password".into()))?;

        // Phase 1 — GET the login page so the session gets a JSESSIONID.
        let _ = self.client.get(LOGIN_URL).send().await?;

        // Phase 2 — POST the login form.
        let form = [
            ("customerid", customer_id.as_str()),
            ("username", username.as_str()),
            ("password", password.as_str()),
        ];
        let resp = self.client.post(LOGIN_URL).form(&form).send().await?;
        if !resp.status().is_success() && !resp.status().is_redirection() {
            return Err(SyncError::Auth(format!("HTTP {}", resp.status())));
        }

        let body = resp.text().await?;
        if body.to_ascii_lowercase().contains("credenziali") {
            return Err(SyncError::Auth("invalid credentials".into()));
        }

        self.authenticated = true;
        Ok(username)
    }

    async fn fetch_grades(&self) -> Result<Vec<RawGrade>, SyncError> {
        if !self.authenticated {
            return Err(SyncError::Auth("not authenticated".into()));
        }
        // TODO: parse term dropdown + DataTables payload + decode Italian
        // grade symbols. See docs/REWRITE_SPEC.md §4.5 for the contract.
        tracing::warn!(
            "Axios fetch_grades: stub returning empty list — full scraper lands in a follow-up"
        );
        Ok(vec![])
    }
}
