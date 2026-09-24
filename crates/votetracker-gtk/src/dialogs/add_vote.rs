use chrono::Local;
use relm4::adw::prelude::*;
use relm4::{adw, gtk};
use votetracker_core::{Database, NewVote, Subject};

pub struct AddVoteDialog {
    pub dialog: adw::PreferencesDialog,
    pub subject_combo: adw::ComboRow,
    pub grade_spin: adw::SpinRow,
    pub weight_spin: adw::SpinRow,
    pub term_combo: adw::ComboRow,
    pub type_combo: adw::ComboRow,
    pub notes_entry: adw::EntryRow,
    pub subjects: Vec<Subject>,
}

impl AddVoteDialog {
    pub fn new(db: &mut Database) -> Self {
        let dialog = adw::PreferencesDialog::builder()
            .title("Aggiungi Voto")
            .build();

        let page = adw::PreferencesPage::new();
        let group = adw::PreferencesGroup::new();

        let subjects = db.get_subjects().unwrap_or_default();
        let sub_names: Vec<String> = subjects.iter().map(|s| s.name.clone()).collect();
        let sub_names_str: Vec<&str> = sub_names.iter().map(|s| s.as_str()).collect();
        let string_list = gtk::StringList::new(&sub_names_str);

        let subject_combo = adw::ComboRow::builder()
            .title("Materia")
            .model(&string_list)
            .build();
        group.add(&subject_combo);

        let grade_spin = adw::SpinRow::builder()
            .title("Voto")
            .adjustment(&gtk::Adjustment::new(7.0, 1.0, 10.0, 0.25, 1.0, 0.0))
            .digits(2)
            .build();
        group.add(&grade_spin);

        let weight_spin = adw::SpinRow::builder()
            .title("Peso")
            .adjustment(&gtk::Adjustment::new(1.0, 0.25, 3.0, 0.25, 0.5, 0.0))
            .digits(2)
            .build();
        group.add(&weight_spin);

        let terms = ["1° Quadrimestre", "2° Quadrimestre"];
        let term_list = gtk::StringList::new(&terms);
        let term_combo = adw::ComboRow::builder()
            .title("Periodo (Quadrimestre)")
            .model(&term_list)
            .selected(0)
            .build();
        group.add(&term_combo);

        let types = ["Scritto", "Orale", "Pratico", "Test"];
        let type_list = gtk::StringList::new(&types);
        let type_combo = adw::ComboRow::builder()
            .title("Tipologia Prova")
            .model(&type_list)
            .selected(0)
            .build();
        group.add(&type_combo);

        let notes_entry = adw::EntryRow::builder()
            .title("Note / Argomento")
            .build();
        group.add(&notes_entry);

        page.add(&group);
        dialog.add(&page);

        Self {
            dialog,
            subject_combo,
            grade_spin,
            weight_spin,
            term_combo,
            type_combo,
            notes_entry,
            subjects,
        }
    }

    pub fn get_new_vote(&self, school_year_id: i64) -> Option<NewVote> {
        let sub_idx = self.subject_combo.selected() as usize;
        let subject = self.subjects.get(sub_idx)?;

        let grade = self.grade_spin.value();
        let weight = self.weight_spin.value();
        let term = (self.term_combo.selected() as i32) + 1;
        let vote_type = match self.type_combo.selected() {
            0 => "Scritto",
            1 => "Orale",
            2 => "Pratico",
            _ => "Test",
        }
        .to_string();
        let notes = self.notes_entry.text().to_string();
        let today = Local::now().format("%Y-%m-%d").to_string();

        Some(NewVote {
            subject_id: subject.id,
            grade,
            weight,
            vote_date: today,
            term,
            notes,
            vote_type,
            school_year_id,
        })
    }
}
