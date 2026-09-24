use relm4::adw::prelude::*;
use relm4::{adw, gtk};
use votetracker_core::{calculate_weighted_average, Database};

pub struct DashboardPage {
    pub container: adw::PreferencesPage,
}

impl DashboardPage {
    pub fn new() -> Self {
        let container = adw::PreferencesPage::new();
        Self { container }
    }

    pub fn refresh(&self, db: &mut Database, school_year_id: Option<i64>) {
        // Clear existing groups by replacing content
        // In GTK4 / Libadwaita PreferencesPage, we can remove groups
        while let Some(child) = self.container.first_child() {
            if let Ok(group) = child.downcast::<adw::PreferencesGroup>() {
                self.container.remove(&group);
            } else {
                break;
            }
        }

        let subjects = db.get_subjects().unwrap_or_default();
        let all_votes = db.get_votes(None, None, school_year_id).unwrap_or_default();

        // 1. Overall Summary Group
        let summary_group = adw::PreferencesGroup::builder()
            .title("Riepilogo Generale")
            .description("Panoramica delle tue prestazioni scolastiche")
            .build();

        let general_avg = calculate_weighted_average(&all_votes);
        let avg_str = match general_avg {
            Some(avg) => format!("{:.2}", avg),
            None => "N/D".to_string(),
        };

        let avg_row = adw::ActionRow::builder()
            .title("Media Generale Ponderata")
            .subtitle(format!("Totale voti registrati: {}", all_votes.len()))
            .build();

        let avg_label = gtk::Label::builder()
            .label(&avg_str)
            .css_classes(vec![
                "title-1",
                if general_avg.map(|a| a >= 6.0).unwrap_or(true) {
                    "accent"
                } else {
                    "error"
                },
            ])
            .build();

        avg_row.add_suffix(&avg_label);
        summary_group.add(&avg_row);
        self.container.add(&summary_group);

        // 2. Subject Averages Group
        let subjects_group = adw::PreferencesGroup::builder()
            .title("Medie per Materia")
            .description("Dettaglio del rendimento per ogni disciplina")
            .build();

        if subjects.is_empty() {
            let empty_row = adw::ActionRow::builder()
                .title("Nessuna materia presente")
                .subtitle("Aggiungi le tue materie nelle impostazioni")
                .build();
            subjects_group.add(&empty_row);
        } else {
            for sub in &subjects {
                let sub_votes: Vec<_> = all_votes
                    .iter()
                    .filter(|v| v.subject_id == sub.id)
                    .cloned()
                    .collect();

                let sub_avg = calculate_weighted_average(&sub_votes);
                let sub_avg_str = match sub_avg {
                    Some(avg) => format!("{:.2}", avg),
                    None => "-".to_string(),
                };

                let row = adw::ActionRow::builder()
                    .title(&sub.name)
                    .subtitle(format!(
                        "Voti: {} | Obiettivo: {:.1}",
                        sub_votes.len(),
                        sub.target_grade
                    ))
                    .build();

                let badge = gtk::Label::builder()
                    .label(&sub_avg_str)
                    .css_classes(vec![
                        "title-3",
                        match sub_avg {
                            Some(a) if a >= 6.0 => "success",
                            Some(_) => "error",
                            None => "dim-label",
                        },
                    ])
                    .build();

                row.add_suffix(&badge);
                subjects_group.add(&row);
            }
        }

        self.container.add(&subjects_group);
    }
}
