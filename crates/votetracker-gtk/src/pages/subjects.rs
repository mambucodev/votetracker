use relm4::adw::prelude::*;
use relm4::{adw, gtk};
use votetracker_core::{calculate_weighted_average, Database};

pub struct SubjectsPage {
    pub container: gtk::ScrolledWindow,
    content_box: gtk::Box,
}

impl SubjectsPage {
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
        }
    }

    pub fn refresh(&self, db: &mut Database, school_year_id: Option<i64>) {
        while let Some(child) = self.content_box.first_child() {
            self.content_box.remove(&child);
        }

        let subjects = db.get_subjects().unwrap_or_default();
        let all_votes = db.get_votes(None, None, school_year_id).unwrap_or_default();

        let header_box = gtk::Box::new(gtk::Orientation::Horizontal, 12);
        let header_label = gtk::Label::builder()
            .label(format!("Discipline Scolastiche ({})", subjects.len()))
            .css_classes(vec!["heading", "dim-label"])
            .halign(gtk::Align::Start)
            .hexpand(true)
            .build();
        header_box.append(&header_label);
        self.content_box.append(&header_box);

        if subjects.is_empty() {
            let status = adw::StatusPage::builder()
                .icon_name("folder-documents-symbolic")
                .title("Nessuna Materia Presente")
                .description("Configura le tue materie scolastiche")
                .build();
            self.content_box.append(&status);
        } else {
            let list_box = gtk::ListBox::new();
            list_box.add_css_class("boxed-list");
            list_box.set_selection_mode(gtk::SelectionMode::None);

            for sub in &subjects {
                let votes: Vec<_> = all_votes
                    .iter()
                    .filter(|v| v.subject_id == sub.id)
                    .cloned()
                    .collect();

                let avg = calculate_weighted_average(&votes);
                let avg_str = match avg {
                    Some(a) => format!("{:.2}", a),
                    None => "—".to_string(),
                };

                let row = adw::ActionRow::builder()
                    .title(&sub.name)
                    .subtitle(format!("Obiettivo: {:.1} • {} verifiche registrate", sub.target_grade, votes.len()))
                    .build();

                let dot = gtk::Label::builder()
                    .label("●")
                    .css_classes(vec![
                        match avg {
                            Some(a) if a >= sub.target_grade => "success",
                            Some(_) => "error",
                            None => "dim-label",
                        },
                        "title-3",
                    ])
                    .build();
                row.add_prefix(&dot);

                let badge = gtk::Label::builder()
                    .label(&avg_str)
                    .css_classes(vec![
                        "pill",
                        match avg {
                            Some(a) if a >= sub.target_grade => "success",
                            Some(_) => "error",
                            None => "dim-label",
                        },
                    ])
                    .build();
                row.add_suffix(&badge);
                list_box.append(&row);
            }

            self.content_box.append(&list_box);
        }
    }
}
