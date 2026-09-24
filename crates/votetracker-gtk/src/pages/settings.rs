use relm4::adw::prelude::*;
use relm4::{adw, gtk};
use votetracker_core::Database;

pub struct SettingsPage {
    pub container: adw::PreferencesPage,
}

impl SettingsPage {
    pub fn new() -> Self {
        let container = adw::PreferencesPage::new();
        Self { container }
    }

    pub fn refresh(&self, db: &mut Database) {
        while let Some(child) = self.container.first_child() {
            if let Ok(group) = child.downcast::<adw::PreferencesGroup>() {
                self.container.remove(&group);
            } else {
                break;
            }
        }

        // 1. School Year Group
        let active_year = db.get_active_school_year().unwrap_or_default();
        let year_group = adw::PreferencesGroup::builder()
            .title("Anno Scolastico")
            .description("Gestione dell'anno accademico corrente")
            .build();

        let year_row = adw::ActionRow::builder()
            .title("Anno Selezionato")
            .subtitle(active_year.as_ref().map(|y| y.name.as_str()).unwrap_or("Nessun anno attivo"))
            .build();

        let switch_btn = gtk::Button::builder()
            .label("Cambia")
            .valign(gtk::Align::Center)
            .build();
        year_row.add_suffix(&switch_btn);
        year_group.add(&year_row);
        self.container.add(&year_group);

        // 2. Appearance Group
        let appearance_group = adw::PreferencesGroup::builder()
            .title("Aspetto")
            .description("Personalizzazione del tema grafico")
            .build();

        let theme_row = adw::ActionRow::builder()
            .title("Tema dell'Interfaccia")
            .subtitle("Adatta automaticamente l'aspetto al sistema GNOME")
            .build();

        let theme_label = gtk::Label::builder()
            .label("Predefinito di Sistema")
            .css_classes(vec!["dim-label"])
            .build();
        theme_row.add_suffix(&theme_label);
        appearance_group.add(&theme_row);
        self.container.add(&appearance_group);

        // 3. Electronic Register Sync Group
        let sync_group = adw::PreferencesGroup::builder()
            .title("Registri Elettronici")
            .description("Integrazione con ClasseViva e Axios Italia")
            .build();

        let cv_row = adw::ActionRow::builder()
            .title("Spaggiari ClasseViva")
            .subtitle("Sincronizzazione voti e materie")
            .build();
        let cv_switch = adw::SwitchRow::builder()
            .title("Abilita Sincronizzazione")
            .build();
        cv_row.add_suffix(&cv_switch);
        sync_group.add(&cv_row);

        let axios_row = adw::ActionRow::builder()
            .title("Axios Italia")
            .subtitle("Sincronizzazione registro elettronico")
            .build();
        sync_group.add(&axios_row);
        self.container.add(&sync_group);

        // 4. About Group
        let about_group = adw::PreferencesGroup::builder()
            .title("Informazioni")
            .build();

        let about_row = adw::ActionRow::builder()
            .title("VoteTracker")
            .subtitle("Versione 3.0.0 (Rust &amp; Libadwaita)")
            .build();

        let author_label = gtk::Label::builder()
            .label("Mambuco")
            .css_classes(vec!["dim-label"])
            .build();
        about_row.add_suffix(&author_label);
        about_group.add(&about_row);
        self.container.add(&about_group);
    }
}
