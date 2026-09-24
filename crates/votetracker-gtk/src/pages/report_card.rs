use relm4::adw::prelude::*;
use relm4::{adw, gtk};
use votetracker_core::{calculate_weighted_average, Database};

pub struct ReportCardPage {
    pub container: adw::PreferencesPage,
}

impl ReportCardPage {
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

        let mut debts_count = 0;
        let mut total_with_grades = 0;

        let table_group = adw::PreferencesGroup::builder()
            .title("Pagella Scolastica")
            .description("Valutazioni periodiche e medie di fine anno")
            .build();

        for sub in &subjects {
            let term1_votes: Vec<_> = all_votes
                .iter()
                .filter(|v| v.subject_id == sub.id && v.term == 1)
                .cloned()
                .collect();
            let term2_votes: Vec<_> = all_votes
                .iter()
                .filter(|v| v.subject_id == sub.id && v.term == 2)
                .cloned()
                .collect();
            let all_sub_votes: Vec<_> = all_votes
                .iter()
                .filter(|v| v.subject_id == sub.id)
                .cloned()
                .collect();

            let avg1 = calculate_weighted_average(&term1_votes);
            let avg2 = calculate_weighted_average(&term2_votes);
            let final_avg = calculate_weighted_average(&all_sub_votes);

            let avg1_str = avg1.map(|a| format!("{:.1}", a)).unwrap_or_else(|| "-".to_string());
            let avg2_str = avg2.map(|a| format!("{:.1}", a)).unwrap_or_else(|| "-".to_string());
            let final_str = final_avg.map(|a| format!("{:.2}", a)).unwrap_or_else(|| "-".to_string());

            let is_failing = final_avg.map(|a| a < 6.0).unwrap_or(false);
            if final_avg.is_some() {
                total_with_grades += 1;
                if is_failing {
                    debts_count += 1;
                }
            }

            let row = adw::ActionRow::builder()
                .title(&sub.name)
                .subtitle(format!("1°Q: {}  |  2°Q: {}  |  Finale: {}", avg1_str, avg2_str, final_str))
                .build();

            let status_badge = gtk::Label::builder()
                .label(match final_avg {
                    Some(a) if a >= 6.0 => "Sufficiente",
                    Some(_) => "Debito",
                    None => "Nessun voto",
                })
                .css_classes(vec![
                    "caption",
                    match final_avg {
                        Some(a) if a >= 6.0 => "success",
                        Some(_) => "error",
                        None => "dim-label",
                    },
                ])
                .build();

            row.add_suffix(&status_badge);
            table_group.add(&row);
        }

        self.container.add(&table_group);

        // Summary Group
        let summary_group = adw::PreferencesGroup::builder()
            .title("Esito Generale")
            .build();

        let outcome_row = adw::ActionRow::builder()
            .title(if debts_count == 0 && total_with_grades > 0 {
                "Quadro Positivo: Nessun Debito"
            } else if debts_count > 0 {
                "Attenzione: Debiti Rilevati"
            } else {
                "Dati Incompleti"
            })
            .subtitle(format!(
                "Discipline valutate: {} | Debiti formativi: {}",
                total_with_grades, debts_count
            ))
            .build();

        let outcome_label = gtk::Label::builder()
            .label(if debts_count == 0 { "PROMOSSO" } else { "A RISCHIO" })
            .css_classes(vec![
                "title-3",
                if debts_count == 0 { "success" } else { "error" },
            ])
            .build();

        outcome_row.add_suffix(&outcome_label);
        summary_group.add(&outcome_row);
        self.container.add(&summary_group);
    }
}
