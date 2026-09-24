use std::collections::HashMap;
use relm4::adw::prelude::*;
use relm4::{adw, gtk};
use votetracker_core::Database;

pub struct VotesPage {
    pub container: adw::PreferencesPage,
    current_term_filter: Option<i32>,
}

impl VotesPage {
    pub fn new() -> Self {
        let container = adw::PreferencesPage::new();
        Self {
            container,
            current_term_filter: None,
        }
    }

    #[allow(dead_code)]
    pub fn set_term_filter(&mut self, term: Option<i32>) {
        self.current_term_filter = term;
    }

    pub fn refresh(&self, db: &mut Database, school_year_id: Option<i64>) {
        while let Some(child) = self.container.first_child() {
            if let Ok(group) = child.downcast::<adw::PreferencesGroup>() {
                self.container.remove(&group);
            } else {
                break;
            }
        }

        let subjects = db.get_subjects().unwrap_or_default();
        let sub_map: HashMap<i64, String> = subjects.into_iter().map(|s| (s.id, s.name)).collect();

        let votes = db
            .get_votes(None, self.current_term_filter, school_year_id)
            .unwrap_or_default();

        let votes_group = adw::PreferencesGroup::builder()
            .title(match self.current_term_filter {
                Some(1) => "Registro Voti - 1° Quadrimestre",
                Some(2) => "Registro Voti - 2° Quadrimestre",
                _ => "Registro Voti - Tutti i Periodi",
            })
            .description(format!("Totale elementi: {}", votes.len()))
            .build();

        if votes.is_empty() {
            let empty_row = adw::ActionRow::builder()
                .title("Nessun voto registrato")
                .subtitle("Usa il pulsante '+' per aggiungere il tuo primo voto")
                .build();
            votes_group.add(&empty_row);
        } else {
            for v in &votes {
                let subject_name = sub_map
                    .get(&v.subject_id)
                    .cloned()
                    .unwrap_or_else(|| "Materia Sconosciuta".to_string());

                let grade_str = if v.grade <= 0.0 {
                    "+ / -".to_string()
                } else {
                    format!("{:.1}", v.grade)
                };

                let mut subtitle = format!("{} • {} • Peso: {:.1}", v.vote_date, v.vote_type, v.weight);
                if !v.notes.is_empty() {
                    subtitle.push_str(&format!(" • {}", v.notes));
                }

                let row = adw::ActionRow::builder()
                    .title(&subject_name)
                    .subtitle(&subtitle)
                    .build();

                let grade_label = gtk::Label::builder()
                    .label(&grade_str)
                    .css_classes(vec![
                        "title-2",
                        if v.grade <= 0.0 {
                            "dim-label"
                        } else if v.grade >= 6.0 {
                            "success"
                        } else {
                            "error"
                        },
                    ])
                    .build();

                row.add_suffix(&grade_label);
                votes_group.add(&row);
            }
        }

        self.container.add(&votes_group);
    }
}
