mod dialogs;
mod pages;

use relm4::adw::prelude::*;
use relm4::{adw, gtk, ComponentParts, ComponentSender, RelmApp, SimpleComponent};
use votetracker_core::{Database, NewVote};

use crate::dialogs::add_vote::AddVoteDialog;
use crate::pages::dashboard::DashboardPage;
use crate::pages::report_card::ReportCardPage;
use crate::pages::settings::SettingsPage;
use crate::pages::simulator::SimulatorPage;
use crate::pages::subjects::SubjectsPage;
use crate::pages::votes::VotesPage;

struct AppModel {
    db: Database,
    window: adw::ApplicationWindow,
    active_year_id: Option<i64>,
    dashboard: DashboardPage,
    votes_page: VotesPage,
    subjects_page: SubjectsPage,
    simulator: SimulatorPage,
    report_card: ReportCardPage,
    settings_page: SettingsPage,
}

#[derive(Debug)]
enum AppMsg {
    Refresh,
    ShowAddVoteDialog,
    VoteAdded(NewVote),
    #[allow(dead_code)]
    SelectPage(String),
}

#[allow(dead_code)]
struct AppWidgets {
    window: adw::ApplicationWindow,
}

fn create_nav_row(title: &str, icon_name: &str) -> gtk::ListBoxRow {
    let row = gtk::ListBoxRow::new();
    let row_box = gtk::Box::new(gtk::Orientation::Horizontal, 12);
    row_box.set_margin_top(8);
    row_box.set_margin_bottom(8);
    row_box.set_margin_start(12);
    row_box.set_margin_end(12);

    let img = gtk::Image::from_icon_name(icon_name);
    let lbl = gtk::Label::builder()
        .label(title)
        .halign(gtk::Align::Start)
        .hexpand(true)
        .build();

    row_box.append(&img);
    row_box.append(&lbl);
    row.set_child(Some(&row_box));
    row
}

fn create_nav_spacer() -> gtk::ListBoxRow {
    let row = gtk::ListBoxRow::new();
    row.set_selectable(false);
    row.set_activatable(false);
    let sep = gtk::Separator::new(gtk::Orientation::Horizontal);
    sep.set_opacity(0.0);
    sep.set_margin_top(6);
    sep.set_margin_bottom(6);
    row.set_child(Some(&sep));
    row
}

impl SimpleComponent for AppModel {
    type Input = AppMsg;
    type Output = ();
    type Init = ();
    type Root = adw::ApplicationWindow;
    type Widgets = AppWidgets;

    fn init_root() -> Self::Root {
        adw::ApplicationWindow::builder()
            .title("VoteTracker")
            .default_width(960)
            .default_height(650)
            .build()
    }

    fn init(
        _init: Self::Init,
        root: Self::Root,
        sender: ComponentSender<Self>,
    ) -> ComponentParts<Self> {
        let mut db = Database::new::<&str>(None).expect("Failed to initialize database");
        let active_year = db.get_active_school_year().ok().flatten();
        let active_year_id = active_year.as_ref().map(|y| y.id);
        let active_year_name = active_year.as_ref().map(|y| y.name.clone()).unwrap_or_else(|| "2025/2026".to_string());

        let dashboard = DashboardPage::new();
        dashboard.refresh(&mut db, active_year_id);

        let votes_page = VotesPage::new();
        votes_page.refresh(&mut db, active_year_id);

        let subjects_page = SubjectsPage::new();
        subjects_page.refresh(&mut db, active_year_id);

        let mut simulator = SimulatorPage::new();
        simulator.refresh(&mut db, active_year_id);

        let report_card = ReportCardPage::new();
        report_card.refresh(&mut db, active_year_id);

        let settings_page = SettingsPage::new();
        settings_page.refresh(&mut db);

        // =====================================================================
        // NavigationSplitView (Native GNOME sidebar + content)
        // =====================================================================
        let split_view = adw::NavigationSplitView::new();
        split_view.set_min_sidebar_width(220.0);
        split_view.set_max_sidebar_width(280.0);

        // ---------------------------------------------------------------------
        // 1. Sidebar (Clean like Nautilus)
        // ---------------------------------------------------------------------
        let sidebar_box = gtk::Box::new(gtk::Orientation::Vertical, 0);

        let sidebar_header = adw::HeaderBar::new();
        let sidebar_title = adw::WindowTitle::new("VoteTracker", "");
        sidebar_header.set_title_widget(Some(&sidebar_title));
        sidebar_box.append(&sidebar_header);

        let sidebar_list = gtk::ListBox::new();
        sidebar_list.add_css_class("navigation-sidebar");
        sidebar_list.set_selection_mode(gtk::SelectionMode::Single);

        // Group 1: Panoramica
        sidebar_list.append(&create_nav_row("Dashboard", "utilities-system-monitor-symbolic"));
        sidebar_list.append(&create_nav_row("Voti", "view-list-bullet-symbolic"));
        sidebar_list.append(&create_nav_row("Materie", "folder-documents-symbolic"));

        // Spacer
        sidebar_list.append(&create_nav_spacer());

        // Group 2: Strumenti
        sidebar_list.append(&create_nav_row("Simulatore", "accessories-calculator-symbolic"));
        sidebar_list.append(&create_nav_row("Pagella", "x-office-spreadsheet-symbolic"));

        // Spacer
        sidebar_list.append(&create_nav_spacer());

        // Group 3: Preferenze
        sidebar_list.append(&create_nav_row("Impostazioni", "emblem-system-symbolic"));

        // Select first row
        if let Some(first_row) = sidebar_list.row_at_index(0) {
            sidebar_list.select_row(Some(&first_row));
        }

        let scrolled_sidebar = gtk::ScrolledWindow::builder()
            .hscrollbar_policy(gtk::PolicyType::Never)
            .vscrollbar_policy(gtk::PolicyType::Automatic)
            .vexpand(true)
            .child(&sidebar_list)
            .build();
        sidebar_box.append(&scrolled_sidebar);

        let sidebar_page = adw::NavigationPage::builder()
            .title("VoteTracker")
            .tag("sidebar")
            .child(&sidebar_box)
            .build();
        split_view.set_sidebar(Some(&sidebar_page));

        // ---------------------------------------------------------------------
        // 2. Content Area (Clean flat layout like Nautilus)
        // ---------------------------------------------------------------------
        let content_box = gtk::Box::new(gtk::Orientation::Vertical, 0);

        let content_header = adw::HeaderBar::new();
        let content_title = adw::WindowTitle::new("Dashboard", "");
        content_header.set_title_widget(Some(&content_title));

        // Year indicator pill
        let year_pill = gtk::Button::builder()
            .label(&active_year_name)
            .css_classes(vec!["flat"])
            .tooltip_text("Anno scolastico attivo")
            .build();
        content_header.pack_end(&year_pill);

        // Native Suggested Action Button in HeaderBar (like Nautilus new folder / action)
        let add_btn = gtk::Button::builder()
            .label("Nuovo Voto")
            .icon_name("list-add-symbolic")
            .css_classes(vec!["suggested-action"])
            .tooltip_text("Registra un nuovo voto")
            .build();
        let sender_clone = sender.clone();
        add_btn.connect_clicked(move |_| {
            sender_clone.input(AppMsg::ShowAddVoteDialog);
        });
        content_header.pack_end(&add_btn);

        content_box.append(&content_header);

        // ViewStack directly inside content box
        let view_stack = adw::ViewStack::new();
        view_stack.set_vexpand(true);

        view_stack.add_named(&dashboard.container, Some("dashboard"));
        view_stack.add_named(&votes_page.container, Some("votes"));
        view_stack.add_named(&subjects_page.container, Some("subjects"));
        view_stack.add_named(&simulator.container, Some("simulator"));
        view_stack.add_named(&report_card.container, Some("report_card"));
        view_stack.add_named(&settings_page.container, Some("settings"));

        content_box.append(&view_stack);

        let content_page = adw::NavigationPage::builder()
            .title("Dashboard")
            .tag("content")
            .child(&content_box)
            .build();
        split_view.set_content(Some(&content_page));

        // Connect Sidebar Selection to ViewStack and Titles
        let view_stack_clone = view_stack.clone();
        let content_title_clone = content_title.clone();
        let content_page_clone = content_page.clone();
        let split_view_clone = split_view.clone();

        sidebar_list.connect_row_activated(move |_, row| {
            let idx = row.index();
            // Mapping accounting for spacers at row 3 and row 6
            let page_mapping = match idx {
                0 => Some(("dashboard", "Dashboard")),
                1 => Some(("votes", "Registro Voti")),
                2 => Some(("subjects", "Materie Scolastiche")),
                4 => Some(("simulator", "Simulatore Media")),
                5 => Some(("report_card", "Pagella")),
                7 => Some(("settings", "Impostazioni")),
                _ => None,
            };

            if let Some((tag, title)) = page_mapping {
                view_stack_clone.set_visible_child_name(tag);
                content_title_clone.set_title(title);
                content_page_clone.set_title(title);

                // Auto slide on mobile
                split_view_clone.set_show_content(true);
            }
        });

        // ---------------------------------------------------------------------
        // 3. Adaptive Breakpoint (< 760px collapses sidebar to navigation stack)
        // ---------------------------------------------------------------------
        let breakpoint = adw::Breakpoint::new(adw::BreakpointCondition::new_length(
            adw::BreakpointConditionLengthType::MaxWidth,
            760.0,
            adw::LengthUnit::Sp,
        ));

        let sv1 = split_view.clone();
        breakpoint.connect_apply(move |_| {
            sv1.set_collapsed(true);
        });

        let sv2 = split_view.clone();
        breakpoint.connect_unapply(move |_| {
            sv2.set_collapsed(false);
        });

        root.add_breakpoint(breakpoint);
        root.set_content(Some(&split_view));

        let model = AppModel {
            db,
            window: root.clone(),
            active_year_id,
            dashboard,
            votes_page,
            subjects_page,
            simulator,
            report_card,
            settings_page,
        };

        let widgets = AppWidgets { window: root };

        ComponentParts { model, widgets }
    }

    fn update(&mut self, msg: Self::Input, sender: ComponentSender<Self>) {
        match msg {
            AppMsg::Refresh => {
                self.dashboard.refresh(&mut self.db, self.active_year_id);
                self.votes_page.refresh(&mut self.db, self.active_year_id);
                self.subjects_page.refresh(&mut self.db, self.active_year_id);
                self.simulator.refresh(&mut self.db, self.active_year_id);
                self.report_card.refresh(&mut self.db, self.active_year_id);
                self.settings_page.refresh(&mut self.db);
            }
            AppMsg::ShowAddVoteDialog => {
                let add_dialog = std::rc::Rc::new(AddVoteDialog::new(&mut self.db));
                let dialog_clone = add_dialog.clone();
                let sender_clone = sender.clone();
                let year_id = self.active_year_id.unwrap_or(1);

                add_dialog.dialog.connect_closed(move |_| {
                    if let Some(new_vote) = dialog_clone.get_new_vote(year_id) {
                        sender_clone.input(AppMsg::VoteAdded(new_vote));
                    }
                });

                add_dialog.dialog.present(Some(&self.window));
            }
            AppMsg::VoteAdded(new_vote) => {
                if self.db.add_vote(&new_vote).is_ok() {
                    sender.input(AppMsg::Refresh);
                }
            }
            AppMsg::SelectPage(_tag) => {}
        }
    }
}

fn main() {
    tracing_subscriber::fmt::init();
    let app = RelmApp::new("io.github.mambucodev.votetracker");
    app.run::<AppModel>(());
}
