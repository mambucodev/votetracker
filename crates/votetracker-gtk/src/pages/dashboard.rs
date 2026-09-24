use relm4::adw::prelude::*;
use relm4::{adw, gtk};
use votetracker_core::{calculate_statistics, calculate_weighted_average, Database};

pub struct DashboardPage {
    pub container: adw::PreferencesPage,
}

impl DashboardPage {
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
        let stats = calculate_statistics(&all_votes);

        // 1. Soft Hero Card (Overview)
        let hero_group = adw::PreferencesGroup::new();
        let hero_box = gtk::Box::new(gtk::Orientation::Vertical, 12);
        hero_box.set_margin_top(12);
        hero_box.set_margin_bottom(12);
        hero_box.set_margin_start(16);
        hero_box.set_margin_end(16);
        hero_box.add_css_class("card");

        let header_label = gtk::Label::builder()
            .label("Rendimento Scolastico")
            .css_classes(vec!["heading", "dim-label"])
            .halign(gtk::Align::Start)
            .margin_top(16)
            .margin_start(20)
            .build();
        hero_box.append(&header_label);

        let gpa_str = stats.average.map(|a| format!("{:.2}", a)).unwrap_or_else(|| "—".to_string());
        let is_passing = stats.average.map(|a| a >= 6.0).unwrap_or(true);

        let middle_box = gtk::Box::new(gtk::Orientation::Horizontal, 16);
        middle_box.set_margin_start(20);
        middle_box.set_margin_end(20);

        let gpa_label = gtk::Label::builder()
            .label(&gpa_str)
            .css_classes(vec![
                "title-1",
                if is_passing { "success" } else { "error" },
            ])
            .build();
        middle_box.append(&gpa_label);

        let status_pill = gtk::Label::builder()
            .label(if stats.average.is_none() {
                "In attesa di voti"
            } else if is_passing {
                "Media Positiva"
            } else {
                "Sotto la Sufficienza"
            })
            .css_classes(vec![
                "pill",
                if stats.average.is_none() {
                    "dim-label"
                } else if is_passing {
                    "success"
                } else {
                    "error"
                },
            ])
            .valign(gtk::Align::Center)
            .build();
        middle_box.append(&status_pill);
        hero_box.append(&middle_box);

        // Pills row for sub-metrics
        let metrics_box = gtk::Box::new(gtk::Orientation::Horizontal, 12);
        metrics_box.set_margin_start(20);
        metrics_box.set_margin_end(20);
        metrics_box.set_margin_bottom(20);

        let total_pill = gtk::Label::builder()
            .label(format!("Voti Totali: {}", stats.total_votes))
            .css_classes(vec!["caption", "dim-label"])
            .build();
        let pass_rate_pill = gtk::Label::builder()
            .label(format!("Sufficienze: {:.0}%", stats.passing_rate))
            .css_classes(vec!["caption", "dim-label"])
            .build();
        let fails_pill = gtk::Label::builder()
            .label(format!("Insufficienze: {}", stats.failing_count))
            .css_classes(vec![
                "caption",
                if stats.failing_count > 0 { "error" } else { "dim-label" },
            ])
            .build();

        metrics_box.append(&total_pill);
        metrics_box.append(&gtk::Label::new(Some("•")));
        metrics_box.append(&pass_rate_pill);
        metrics_box.append(&gtk::Label::new(Some("•")));
        metrics_box.append(&fails_pill);

        hero_box.append(&metrics_box);
        hero_group.add(&hero_box);
        self.container.add(&hero_group);

        // 2. Subject Averages Group
        let subjects_group = adw::PreferencesGroup::builder()
            .title("Medie per Disciplina")
            .description("Panoramica del rendimento scolastico per ogni materia")
            .build();

        if subjects.is_empty() {
            let empty_row = adw::ActionRow::builder()
                .title("Nessuna materia presente")
                .subtitle("Aggiungi le tue materie nella sezione Materie")
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
                        "{} voti registrati • Obiettivo: {:.1}",
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
