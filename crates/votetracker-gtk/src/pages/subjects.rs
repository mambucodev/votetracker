use relm4::adw::prelude::*;
use relm4::{adw, gtk};
use votetracker_core::{calculate_weighted_average, Database};

pub struct SubjectsPage {
    pub container: adw::PreferencesPage,
}

impl SubjectsPage {
    pub fn new() -> Self {
        let container = adw::PreferencesPage::new();
        Self { container }
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
        let all_votes = db.get_votes(None, None, school_year_id).unwrap_or_default();

        let group = adw::PreferencesGroup::builder()
            .title("Materie Scolastiche")
            .description("Configura le materie, gli obiettivi minimi e visualizza il rendimento")
            .build();

        if subjects.is_empty() {
            let empty_row = adw::ActionRow::builder()
                .title("Nessuna materia registrata")
                .subtitle("Aggiungi la tua prima materia")
                .build();
            group.add(&empty_row);
        } else {
            for sub in &subjects {
                let votes: Vec<_> = all_votes
                    .iter()
                    .filter(|v| v.subject_id == sub.id)
                    .cloned()
                    .collect();

                let avg = calculate_weighted_average(&votes);
                let avg_str = match avg {
                    Some(a) => format!("Media: {:.2}", a),
                    None => "Nessun voto".to_string(),
                };

                let row = adw::ActionRow::builder()
                    .title(&sub.name)
                    .subtitle(format!("{} • Obiettivo: {:.1} • Voti: {}", avg_str, sub.target_grade, votes.len()))
                    .build();

                let color_dot = gtk::Label::builder()
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

                row.add_prefix(&color_dot);

                let badge = gtk::Label::builder()
                    .label(match avg {
                        Some(a) => format!("{:.1}", a),
                        None => "-".to_string(),
                    })
                    .css_classes(vec![
                        "title-3",
                        match avg {
                            Some(a) if a >= sub.target_grade => "accent",
                            Some(_) => "error",
                            None => "dim-label",
                        },
                    ])
                    .build();

                row.add_suffix(&badge);
                group.add(&row);
            }
        }

        self.container.add(&group);
    }
}
