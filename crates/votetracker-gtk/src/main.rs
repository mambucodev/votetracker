mod dialogs;
mod pages;

use relm4::adw::prelude::*;
use relm4::{adw, gtk, ComponentParts, ComponentSender, RelmApp, RelmWidgetExt, SimpleComponent};
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
        // NavigationSplitView (Sidebar + Content according to GNOME HIG)
        // =====================================================================
        let split_view = adw::NavigationSplitView::new();
        split_view.set_min_sidebar_width(220.0);
        split_view.set_max_sidebar_width(280.0);

        // ---------------------------------------------------------------------
        // 1. Sidebar
        // ---------------------------------------------------------------------
        let sidebar_box = gtk::Box::new(gtk::Orientation::Vertical, 0);

        let sidebar_header = adw::HeaderBar::new();
        let sidebar_title = adw::WindowTitle::new("VoteTracker", &active_year_name);
        sidebar_header.set_title_widget(Some(&sidebar_title));
        sidebar_box.append(&sidebar_header);

        // Sidebar navigation list
        let sidebar_list = gtk::ListBox::new();
        sidebar_list.add_css_class("navigation-sidebar");
        sidebar_list.set_selection_mode(gtk::SelectionMode::Single);

        let nav_items = [
            ("Dashboard", "utilities-system-monitor-symbolic", "dashboard"),
            ("Voti", "view-list-bullet-symbolic", "votes"),
            ("Materie", "folder-documents-symbolic", "subjects"),
            ("Simulatore", "accessories-calculator-symbolic", "simulator"),
            ("Pagella", "x-office-spreadsheet-symbolic", "report_card"),
            ("Impostazioni", "emblem-system-symbolic", "settings"),
        ];

        for (title, icon, _id) in &nav_items {
            let row = gtk::ListBoxRow::new();
            let row_box = gtk::Box::new(gtk::Orientation::Horizontal, 12);
            row_box.set_margin_top(8);
            row_box.set_margin_bottom(8);
            row_box.set_margin_start(12);
            row_box.set_margin_end(12);

            let img = gtk::Image::from_icon_name(icon);
            let lbl = gtk::Label::builder()
                .label(*title)
                .halign(gtk::Align::Start)
                .hexpand(true)
                .build();

            row_box.append(&img);
            row_box.append(&lbl);
            row.set_child(Some(&row_box));
            sidebar_list.append(&row);
        }

        // Select first item by default
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

        // Bottom CTA in Sidebar: Soft Pill Add Button
        let bottom_sidebar_box = gtk::Box::new(gtk::Orientation::Vertical, 0);
        bottom_sidebar_box.set_margin_all(12);

        let add_btn_sidebar = gtk::Button::builder()
            .label("Aggiungi Voto")
            .icon_name("list-add-symbolic")
            .css_classes(vec!["suggested-action", "pill"])
            .build();
        let sender_clone = sender.clone();
        add_btn_sidebar.connect_clicked(move |_| {
            sender_clone.input(AppMsg::ShowAddVoteDialog);
        });
        bottom_sidebar_box.append(&add_btn_sidebar);
        sidebar_box.append(&bottom_sidebar_box);

        let sidebar_page = adw::NavigationPage::builder()
            .title("VoteTracker")
            .tag("sidebar")
            .child(&sidebar_box)
            .build();
        split_view.set_sidebar(Some(&sidebar_page));

        // ---------------------------------------------------------------------
        // 2. Content Area
        // ---------------------------------------------------------------------
        let content_box = gtk::Box::new(gtk::Orientation::Vertical, 0);

        let content_header = adw::HeaderBar::new();
        let content_title = adw::WindowTitle::new("Dashboard", "");
        content_header.set_title_widget(Some(&content_title));

        let quick_add_btn = gtk::Button::builder()
            .icon_name("list-add-symbolic")
            .tooltip_text("Aggiungi nuovo voto")
            .build();
        let sender_clone2 = sender.clone();
        quick_add_btn.connect_clicked(move |_| {
            sender_clone2.input(AppMsg::ShowAddVoteDialog);
        });
        content_header.pack_end(&quick_add_btn);
        content_box.append(&content_header);

        // ViewStack with pages
        let view_stack = adw::ViewStack::new();
        view_stack.set_vexpand(true);

        view_stack.add_named(&dashboard.container, Some("dashboard"));
        view_stack.add_named(&votes_page.container, Some("votes"));
        view_stack.add_named(&subjects_page.container, Some("subjects"));
        view_stack.add_named(&simulator.container, Some("simulator"));
        view_stack.add_named(&report_card.container, Some("report_card"));
        view_stack.add_named(&settings_page.container, Some("settings"));

        // Wrap inside Clamp for optimal reading width on wide screens
        let clamp = adw::Clamp::builder()
            .maximum_size(900)
            .tightening_threshold(650)
            .child(&view_stack)
            .build();
        content_box.append(&clamp);

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
            let page_ids = ["dashboard", "votes", "subjects", "simulator", "report_card", "settings"];
            let page_titles = ["Dashboard", "Registro Voti", "Materie Scolastiche", "Simulatore Media", "Pagella", "Impostazioni"];

            if let Some(&tag) = page_ids.get(idx as usize) {
                view_stack_clone.set_visible_child_name(tag);
                let title = page_titles.get(idx as usize).unwrap_or(&"VoteTracker");
                content_title_clone.set_title(title);
                content_page_clone.set_title(title);

                // On collapsed (mobile), auto-slide to content
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
            AppMsg::SelectPage(_tag) => {
                // handle direct page navigation
            }
        }
    }
}

fn main() {
    tracing_subscriber::fmt::init();
    let app = RelmApp::new("io.github.mambucodev.votetracker");
    app.run::<AppModel>(());
}
