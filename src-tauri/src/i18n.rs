//! Language detection + translation maps. Full en/it tables ported in M7.

pub fn system_language() -> &'static str {
    let lang = std::env::var("LANG").or_else(|_| std::env::var("LC_ALL"));
    match lang {
        Ok(v) if v.to_ascii_lowercase().starts_with("it") => "it",
        _ => "en",
    }
}
