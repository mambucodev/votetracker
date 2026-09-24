use relm4::adw::prelude::*;
use relm4::{adw, gtk};
use votetracker_core::{calculate_statistics, calculate_weighted_average, Database};

pub struct DashboardPage {
    pub container: gtk::ScrolledWindow,
    content_box: gtk::Box,
}

impl DashboardPage {
    pub fn new() -> Self {
        let content_box = gtk::Box::new(gtk::Orientation::Vertical, 20);
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
        let stats = calculate_statistics(&all_votes);

        // 1. Clean Hero Card
        let hero_card = gtk::Box::new(gtk::Orientation::Vertical, 14);
        hero_card.add_css_class("card");
        hero_card.set_margin_bottom(8);

        let card_content = gtk::Box::new(gtk::Orientation::Vertical, 12);
        card_content.set_margin_top(18);
        card_content.set_margin_bottom(18);
        card_content.set_margin_start(20);
        card_content.set_margin_end(20);

        // Card Header
        let card_header = gtk::Box::new(gtk::Orientation::Horizontal, 12);
        let header_lbl = gtk::Label::builder()
            .label("Rendimento Scolastico")
            .css_classes(vec!["heading"])
            .halign(gtk::Align::Start)
            .hexpand(true)
            .build();
        card_header.append(&header_lbl);

        let is_passing = stats.average.map(|a| a >= 6.0).unwrap_or(true);
        let status_badge = gtk::Label::builder()
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
            .build();
        card_header.append(&status_badge);
        card_content.append(&card_header);

        // Score display
        let score_box = gtk::Box::new(gtk::Orientation::Horizontal, 16);
        let gpa_str = stats.average.map(|a| format!("{:.2}", a)).unwrap_or_else(|| "—".to_string());
        let gpa_lbl = gtk::Label::builder()
            .label(&gpa_str)
            .css_classes(vec![
                "title-1",
                if stats.average.is_none() {
                    "dim-label"
                } else if is_passing {
                    "success"
                } else {
                    "error"
                },
            ])
            .build();
        score_box.append(&gpa_lbl);

        let gpa_sub_box = gtk::Box::new(gtk::Orientation::Vertical, 2);
        gpa_sub_box.set_valign(gtk::Align::Center);
        let sub_title = gtk::Label::builder()
            .label("Media Generale Ponderata")
            .css_classes(vec!["body", "dim-label"])
            .halign(gtk::Align::Start)
            .build();
        let sub_notes = gtk::Label::builder()
            .label(if stats.average.is_none() {
                "Nessun voto calcolato per questo anno"
            } else {
                "Calcolata su tutte le prove valide"
            })
            .css_classes(vec!["caption", "dim-label"])
            .halign(gtk::Align::Start)
            .build();
        gpa_sub_box.append(&sub_title);
        gpa_sub_box.append(&sub_notes);
        score_box.append(&gpa_sub_box);
        card_content.append(&score_box);

        // Stats Footer Row
        let footer_box = gtk::Box::new(gtk::Orientation::Horizontal, 16);
        footer_box.set_margin_top(4);

        let chip1 = gtk::Label::builder()
            .label(format!("Voti Totali: {}", stats.total_votes))
            .css_classes(vec!["caption", "dim-label"])
            .build();
        let chip2 = gtk::Label::builder()
            .label(format!("Sufficienze: {:.0}%", stats.passing_rate))
            .css_classes(vec!["caption", "dim-label"])
            .build();
        let chip3 = gtk::Label::builder()
            .label(format!("Insufficienze: {}", stats.failing_count))
            .css_classes(vec![
                "caption",
                if stats.failing_count > 0 { "error" } else { "dim-label" },
            ])
            .build();

        footer_box.append(&chip1);
        footer_box.append(&gtk::Label::new(Some("•")));
        footer_box.append(&chip2);
        footer_box.append(&gtk::Label::new(Some("•")));
        footer_box.append(&chip3);
        card_content.append(&footer_box);

        hero_card.append(&card_content);
        self.content_box.append(&hero_card);

        // 2. Section Header
        let section_header = gtk::Box::new(gtk::Orientation::Horizontal, 8);
        section_header.set_margin_top(8);
        section_header.set_margin_bottom(4);

        let section_title = gtk::Label::builder()
            .label("Materie")
            .css_classes(vec!["title-3"])
            .halign(gtk::Align::Start)
            .hexpand(true)
            .build();
        section_header.append(&section_title);

        let count_pill = gtk::Label::builder()
            .label(format!("{} materie", subjects.len()))
            .css_classes(vec!["caption", "dim-label"])
            .build();
        section_header.append(&count_pill);
        self.content_box.append(&section_header);

        // 3. Subjects Boxed List (Clean GNOME boxed-list)
        let list_box = gtk::ListBox::new();
        list_box.add_css_class("boxed-list");
        list_box.set_selection_mode(gtk::SelectionMode::None);

        if subjects.is_empty() {
            let empty_row = adw::ActionRow::builder()
                .title("Nessuna materia presente")
                .subtitle("Aggiungi le tue materie nella sezione Materie")
                .build();
            list_box.append(&empty_row);
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
                    None => "—".to_string(),
                };

                let row = adw::ActionRow::builder()
                    .title(&sub.name)
                    .subtitle(format!(
                        "{} verifiche • Obiettivo: {:.1}",
                        sub_votes.len(),
                        sub.target_grade
                    ))
                    .build();

                let dot = gtk::Label::builder()
                    .label("●")
                    .css_classes(vec![
                        match sub_avg {
                            Some(a) if a >= 6.0 => "success",
                            Some(_) => "error",
                            None => "dim-label",
                        },
                        "title-3",
                    ])
                    .build();
                row.add_prefix(&dot);

                let badge = gtk::Label::builder()
                    .label(&sub_avg_str)
                    .css_classes(vec![
                        "pill",
                        match sub_avg {
                            Some(a) if a >= 6.0 => "success",
                            Some(_) => "error",
                            None => "dim-label",
                        },
                    ])
                    .build();
                row.add_suffix(&badge);
                list_box.append(&row);
            }
        }

        self.content_box.append(&list_box);
    }
}
