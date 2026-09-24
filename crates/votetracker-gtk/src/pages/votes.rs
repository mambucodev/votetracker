use std::collections::HashMap;
use relm4::adw::prelude::*;
use relm4::{adw, gtk};
use votetracker_core::Database;

pub struct VotesPage {
    pub container: gtk::ScrolledWindow,
    content_box: gtk::Box,
    current_term_filter: Option<i32>,
}

impl VotesPage {
    pub fn new() -> Self {
        let content_box = gtk::Box::new(gtk::Orientation::Vertical, 16);
        content_box.set_margin_top(24);
        content_box.set_margin_bottom(24);
        content_box.set_margin_start(24);
        content_box.set_margin_end(24);

        let container = gtk::ScrolledWindow::builder()
            .hscrollbar_policy(gtk::PolicyType::Never)
            .vscrollbar_policy(gtk::PolicyType::Automatic)
            .child(&content_box)
            .build();

        Self {
            container,
            content_box,
            current_term_filter: None,
        }
    }

    #[allow(dead_code)]
    pub fn set_term_filter(&mut self, term: Option<i32>) {
        self.current_term_filter = term;
    }

    pub fn refresh(&self, db: &mut Database, school_year_id: Option<i64>) {
        while let Some(child) = self.content_box.first_child() {
            self.content_box.remove(&child);
        }

        let subjects = db.get_subjects().unwrap_or_default();
        let sub_map: HashMap<i64, String> = subjects.into_iter().map(|s| (s.id, s.name)).collect();

        let votes = db
            .get_votes(None, self.current_term_filter, school_year_id)
            .unwrap_or_default();

        if votes.is_empty() {
            // Native GNOME Empty State
            let status_page = adw::StatusPage::builder()
                .icon_name("document-edit-symbolic")
                .title("Nessun Voto Registrato")
                .description("Inizia ad aggiungere i tuoi voti per monitorare il rendimento scolastico")
                .vexpand(true)
                .build();
            self.content_box.append(&status_page);
        } else {
            // Header with count
            let header_box = gtk::Box::new(gtk::Orientation::Horizontal, 12);
            let count_label = gtk::Label::builder()
                .label(format!("{} verifiche registrate", votes.len()))
                .css_classes(vec!["heading", "dim-label"])
                .halign(gtk::Align::Start)
                .hexpand(true)
                .build();
            header_box.append(&count_label);
            self.content_box.append(&header_box);

            // Clean Boxed List
            let list_box = gtk::ListBox::new();
            list_box.add_css_class("boxed-list");
            list_box.set_selection_mode(gtk::SelectionMode::None);

            for v in &votes {
                let subject_name = sub_map
                    .get(&v.subject_id)
                    .cloned()
                    .unwrap_or_else(|| "Materia".to_string());

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

                let is_passing = v.grade >= 6.0;
                let grade_label = gtk::Label::builder()
                    .label(&grade_str)
                    .css_classes(vec![
                        "pill",
                        if v.grade <= 0.0 {
                            "dim-label"
                        } else if is_passing {
                            "success"
                        } else {
                            "error"
                        },
                    ])
                    .build();

                row.add_suffix(&grade_label);
                list_box.append(&row);
            }

            self.content_box.append(&list_box);
        }
    }
}
