use relm4::adw::prelude::*;
use relm4::{adw, gtk};
use votetracker_core::{calculate_needed_grade, calculate_weighted_average, Database, Subject};

pub struct SimulatorPage {
    pub container: adw::PreferencesPage,
    subjects: Vec<Subject>,
    selected_subject_idx: usize,
    target_grade: f64,
    weight: f64,
}

impl SimulatorPage {
    pub fn new() -> Self {
        let container = adw::PreferencesPage::new();
        Self {
            container,
            subjects: Vec::new(),
            selected_subject_idx: 0,
            target_grade: 6.0,
            weight: 1.0,
        }
    }

    pub fn refresh(&mut self, db: &mut Database, school_year_id: Option<i64>) {
        while let Some(child) = self.container.first_child() {
            if let Ok(group) = child.downcast::<adw::PreferencesGroup>() {
                self.container.remove(&group);
            } else {
                break;
            }
        }

        self.subjects = db.get_subjects().unwrap_or_default();
        if self.subjects.is_empty() {
            let empty_group = adw::PreferencesGroup::builder()
                .title("Simulatore Voti")
                .description("Nessuna materia configurata nel database")
                .build();
            self.container.add(&empty_group);
            return;
        }

        if self.selected_subject_idx >= self.subjects.len() {
            self.selected_subject_idx = 0;
        }

        let current_sub = &self.subjects[self.selected_subject_idx];
        let votes = db
            .get_votes(Some(current_sub.id), None, school_year_id)
            .unwrap_or_default();

        let current_avg = calculate_weighted_average(&votes);
        let needed = calculate_needed_grade(&votes, self.target_grade, self.weight);

        // Group 1: Configuration
        let config_group = adw::PreferencesGroup::builder()
            .title("Obiettivo e Parametri")
            .description("Seleziona la materia e inserisci la media che desideri raggiungere")
            .build();

        let sub_names: Vec<String> = self.subjects.iter().map(|s| s.name.clone()).collect();
        let sub_names_str: Vec<&str> = sub_names.iter().map(|s| s.as_str()).collect();
        let string_list = gtk::StringList::new(&sub_names_str);

        let combo_row = adw::ComboRow::builder()
            .title("Materia")
            .model(&string_list)
            .selected(self.selected_subject_idx as u32)
            .build();
        config_group.add(&combo_row);

        let current_avg_str = match current_avg {
            Some(a) => format!("{:.2}", a),
            None => "Nessun voto presente".to_string(),
        };

        let current_row = adw::ActionRow::builder()
            .title("Media Attuale")
            .subtitle(current_avg_str)
            .build();
        config_group.add(&current_row);

        let target_spin = adw::SpinRow::builder()
            .title("Media Obiettivo")
            .adjustment(&gtk::Adjustment::new(self.target_grade, 1.0, 10.0, 0.25, 1.0, 0.0))
            .digits(2)
            .build();
        config_group.add(&target_spin);

        let weight_spin = adw::SpinRow::builder()
            .title("Peso Prossima Prova")
            .adjustment(&gtk::Adjustment::new(self.weight, 0.25, 5.0, 0.25, 0.5, 0.0))
            .digits(2)
            .build();
        config_group.add(&weight_spin);

        self.container.add(&config_group);

        // Group 2: Result Readout
        let result_group = adw::PreferencesGroup::builder()
            .title("Esito Simulazione")
            .build();

        let result_row = adw::ActionRow::builder().build();

        match (current_avg, needed) {
            (Some(curr), _) if curr >= self.target_grade => {
                result_row.set_title("Obiettivo Già Raggiunto!");
                result_row.set_subtitle(&format!(
                    "La tua media attuale ({:.2}) è già superiore o uguale al target ({:.2}).",
                    curr, self.target_grade
                ));
                let badge = gtk::Label::builder()
                    .label("OK")
                    .css_classes(vec!["title-2", "success"])
                    .build();
                result_row.add_suffix(&badge);
            }
            (_, Some(req)) if req > 10.0 => {
                result_row.set_title("Obiettivo Non Raggiungibile in Singola Prova");
                result_row.set_subtitle(&format!(
                    "Servirebbe un voto pari a {:.2} (superiore al massimo 10.0). Saranno necessarie più verifiche positive.",
                    req
                ));
                let badge = gtk::Label::builder()
                    .label("10+")
                    .css_classes(vec!["title-2", "warning"])
                    .build();
                result_row.add_suffix(&badge);
            }
            (_, Some(req)) if req < 1.0 => {
                result_row.set_title("Voto Minimo Sufficiente");
                result_row.set_subtitle(&format!(
                    "Anche con il voto minimo (1.0), la media rimarrà sopra l'obiettivo ({:.2}).",
                    self.target_grade
                ));
            }
            (_, Some(req)) => {
                result_row.set_title("Voto Minimo Necessario");
                result_row.set_subtitle(&format!(
                    "Devi prendere almeno {:.2} nella prossima verifica con peso {:.1} per raggiungere media {:.2}.",
                    req, self.weight, self.target_grade
                ));
                let badge = gtk::Label::builder()
                    .label(format!("{:.1}", req))
                    .css_classes(vec![
                        "title-1",
                        if req <= 6.0 {
                            "success"
                        } else if req <= 8.0 {
                            "accent"
                        } else {
                            "warning"
                        },
                    ])
                    .build();
                result_row.add_suffix(&badge);
            }
            _ => {
                result_row.set_title("Dati Insufficienti");
                result_row.set_subtitle("Aggiungi voti o imposta un peso valido per calcolare la stima.");
            }
        }

        result_group.add(&result_row);
        self.container.add(&result_group);
    }
}
