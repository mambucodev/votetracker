//! Axios (axioscloud) HTML-scrape provider.
//!
//! Implements the full scrape contract from `docs/REWRITE_SPEC.md` §4.5:
//! login (GET + form POST with `customerid` / `username` / `password`),
//! term-list discovery, DataTables-shape grade-list POSTs, and the
//! Italian grade-symbol decoder. Pure decoding lives in
//! [`axios_decode`] so it can be unit-tested without a network.

use super::axios_decode::{decode_date, decode_grade, decode_term_label, decode_type};
use super::{CredentialField, RawGrade, SyncError, SyncProvider};
use async_trait::async_trait;
use reqwest::{cookie::Jar, Client};
use scraper::{Html, Selector};
use serde::Deserialize;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

const BASE: &str = "https://registrofamiglie.axioscloud.it";
const LOGIN_URL: &str = "https://registrofamiglie.axioscloud.it/Pages/SD/SD_Login.aspx";
const AJAX_URL: &str = "https://registrofamiglie.axioscloud.it/Pages/APP/APP_Ajax_Get.aspx";

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

    /// GET the `FAMILY_VOTI` endpoint without a payload — the response
    /// contains a `<select id="fiFrazId">` with one `<option>` per term.
    async fn discover_terms(&self) -> Result<Vec<TermEntry>, SyncError> {
        let ts = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_millis())
            .unwrap_or(0);
        let url = format!("{AJAX_URL}?Action=FAMILY_VOTI&_={ts}");
        let resp = self
            .client
            .get(&url)
            .header("X-Requested-With", "XMLHttpRequest")
            .send()
            .await?;
        if !resp.status().is_success() {
            return Err(SyncError::Parse(format!(
                "HTTP {} discovering terms",
                resp.status()
            )));
        }
        let body: AjaxHtmlResponse = resp
            .json()
            .await
            .map_err(|e| SyncError::Parse(format!("term list JSON: {e}")))?;
        Ok(parse_term_options(&body.html))
    }

    /// For a given term (FRAZ_X) POST the term selection, then parse the
    /// `<input id="frazione" value="NNN">` from the returned HTML fragment.
    async fn resolve_frazione_id(&self, fraz_id: &str) -> Result<String, SyncError> {
        let url = format!("{AJAX_URL}?Action=FAMILY_VOTI");
        let payload = serde_json::json!({ "iFrazId": fraz_id });
        let resp = self
            .client
            .post(&url)
            .header("X-Requested-With", "XMLHttpRequest")
            .json(&payload)
            .send()
            .await?;
        if !resp.status().is_success() {
            return Err(SyncError::Parse(format!(
                "HTTP {} resolving frazione for {fraz_id}",
                resp.status()
            )));
        }
        let body: AjaxHtmlResponse = resp
            .json()
            .await
            .map_err(|e| SyncError::Parse(format!("frazione JSON: {e}")))?;
        parse_frazione_value(&body.html).ok_or_else(|| {
            SyncError::Parse(format!("missing frazione input for {fraz_id}"))
        })
    }

    /// POST the DataTables-style grade list query for a given `frazione`
    /// integer identifier. Returns the raw `data` array.
    async fn fetch_grade_rows(&self, frazione: &str) -> Result<Vec<GradeRow>, SyncError> {
        let url = format!("{AJAX_URL}?Action=FAMILY_VOTI_ELENCO_LISTA");
        let payload = serde_json::json!({
            "draw": 1,
            "start": 0,
            "length": 1000,
            "frazione": frazione,
        });
        let resp = self
            .client
            .post(&url)
            .header("X-Requested-With", "XMLHttpRequest")
            .json(&payload)
            .send()
            .await?;
        if !resp.status().is_success() {
            return Err(SyncError::Parse(format!(
                "HTTP {} fetching grades for frazione {frazione}",
                resp.status()
            )));
        }
        let body: GradeListResponse = resp
            .json()
            .await
            .map_err(|e| SyncError::Parse(format!("grade list JSON: {e}")))?;
        Ok(body.data)
    }
}

/// Entry parsed from the term-list `<option>` dropdown.
#[derive(Debug, Clone)]
struct TermEntry {
    /// `FRAZ_001`-style identifier used as the POST payload value.
    id: String,
    /// Human-visible label — fed to `decode_term_label`.
    label: String,
}

/// The shape of `APP_Ajax_Get.aspx` responses that embed HTML.
#[derive(Deserialize)]
struct AjaxHtmlResponse {
    #[serde(default)]
    html: String,
}

/// Top-level DataTables-style payload for the grade list endpoint.
#[derive(Deserialize)]
struct GradeListResponse {
    #[serde(default)]
    data: Vec<GradeRow>,
}

/// One row from the grade list. Field names match Axios's JSON.
#[derive(Debug, Deserialize)]
struct GradeRow {
    #[serde(default)]
    giorno: String,
    #[serde(default)]
    materia: String,
    #[serde(default)]
    voto: String,
    #[serde(default)]
    tipo: String,
    #[serde(default)]
    commento: String,
}

/// Parses `<option value="FRAZ_XXX">Label</option>` entries out of the
/// HTML fragment returned by the term-list endpoint. Skips placeholder
/// options with empty values.
fn parse_term_options(html: &str) -> Vec<TermEntry> {
    let doc = Html::parse_fragment(html);
    // Scope to the select we care about so we don't pick up unrelated
    // dropdowns if Axios ever nests them in the same fragment.
    let option_sel = Selector::parse("select#fiFrazId option, select option").unwrap();
    let mut out = Vec::new();
    for el in doc.select(&option_sel) {
        let value = el.value().attr("value").unwrap_or("").trim().to_string();
        if value.is_empty() {
            continue;
        }
        let label = el.text().collect::<String>().trim().to_string();
        out.push(TermEntry { id: value, label });
    }
    out
}

/// Extracts the `value` attribute from `<input id="frazione">` inside an
/// HTML fragment.
fn parse_frazione_value(html: &str) -> Option<String> {
    let doc = Html::parse_fragment(html);
    let sel = Selector::parse(r#"input#frazione"#).ok()?;
    let el = doc.select(&sel).next()?;
    el.value().attr("value").map(|v| v.trim().to_string())
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

        let terms = self.discover_terms().await?;
        if terms.is_empty() {
            tracing::warn!("Axios: no terms discovered — empty grade list");
            return Ok(vec![]);
        }

        let mut out = Vec::new();
        for term in terms {
            let term_num = decode_term_label(&term.label);
            // Select the term so `frazione` is available, then resolve it.
            let frazione = match self.resolve_frazione_id(&term.id).await {
                Ok(f) => f,
                Err(e) => {
                    tracing::warn!(
                        "Axios: could not resolve frazione for {} ({}): {e}",
                        term.id,
                        term.label
                    );
                    continue;
                }
            };

            let rows = match self.fetch_grade_rows(&frazione).await {
                Ok(r) => r,
                Err(e) => {
                    tracing::warn!(
                        "Axios: grade fetch failed for frazione {frazione} ({}): {e}",
                        term.label
                    );
                    continue;
                }
            };

            for row in rows {
                let Some(value) = decode_grade(&row.voto) else {
                    tracing::debug!(
                        "Axios: skipping row with undecodable voto {:?} (materia {})",
                        row.voto,
                        row.materia
                    );
                    continue;
                };
                let Some(date) = decode_date(&row.giorno) else {
                    tracing::debug!(
                        "Axios: skipping row with bad date {:?} (materia {})",
                        row.giorno,
                        row.materia
                    );
                    continue;
                };
                let kind = decode_type(&row.tipo);
                let description = {
                    let c = row.commento.trim();
                    if c.is_empty() {
                        None
                    } else {
                        Some(c.to_string())
                    }
                };

                out.push(RawGrade {
                    subject: row.materia.trim().to_string(),
                    grade: value,
                    kind,
                    date,
                    description,
                    weight: 1.0,
                    term: term_num,
                });
            }
        }

        Ok(out)
    }
}

// Silence "unused" warnings on the BASE constant under some build configs
// (it's kept for symmetry / external references and documentation).
#[allow(dead_code)]
const _BASE_REFERENCED: &str = BASE;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_term_options_basic() {
        let html = r#"
            <select id="fiFrazId">
                <option value="">-- seleziona --</option>
                <option value="FRAZ_001">1° TRIMESTRE</option>
                <option value="FRAZ_002">PENTAMESTRE</option>
            </select>
        "#;
        let terms = parse_term_options(html);
        assert_eq!(terms.len(), 2);
        assert_eq!(terms[0].id, "FRAZ_001");
        assert_eq!(terms[0].label, "1° TRIMESTRE");
        assert_eq!(terms[1].id, "FRAZ_002");
        assert_eq!(terms[1].label, "PENTAMESTRE");
    }

    #[test]
    fn parse_frazione_value_ok() {
        let html = r#"<div><input id="frazione" value="42" type="hidden"></div>"#;
        assert_eq!(parse_frazione_value(html), Some("42".to_string()));
    }

    #[test]
    fn parse_frazione_value_missing() {
        assert_eq!(parse_frazione_value("<div></div>"), None);
    }
}
