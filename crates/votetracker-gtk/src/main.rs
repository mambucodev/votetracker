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
use crate::pages::votes::VotesPage;

struct AppModel {
    db: Database,
    window: adw::ApplicationWindow,
    active_year_id: Option<i64>,
    dashboard: DashboardPage,
    votes_page: VotesPage,
    simulator: SimulatorPage,
    report_card: ReportCardPage,
    settings_page: SettingsPage,
}

#[derive(Debug)]
enum AppMsg {
    Refresh,
    ShowAddVoteDialog,
    VoteAdded(NewVote),
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
            .default_width(850)
            .default_height(600)
            .build()
    }

    fn init(
        _init: Self::Init,
        root: Self::Root,
        sender: ComponentSender<Self>,
    ) -> ComponentParts<Self> {
        let mut db = Database::new::<&str>(None).expect("Failed to initialize database");
        let active_year_id = db.get_active_school_year().ok().flatten().map(|y| y.id);

        let dashboard = DashboardPage::new();
        dashboard.refresh(&mut db, active_year_id);

        let votes_page = VotesPage::new();
        votes_page.refresh(&mut db, active_year_id);

        let mut simulator = SimulatorPage::new();
        simulator.refresh(&mut db, active_year_id);

        let report_card = ReportCardPage::new();
        report_card.refresh(&mut db, active_year_id);

        let settings_page = SettingsPage::new();
        settings_page.refresh(&mut db);

        // 1. Layout containers
        let main_box = gtk::Box::new(gtk::Orientation::Vertical, 0);

        // 2. ViewStack
        let view_stack = adw::ViewStack::new();
        view_stack.set_vexpand(true);

        view_stack
            .add_titled_with_icon(
                &dashboard.container,
                Some("dashboard"),
                "Dashboard",
                "utilities-system-monitor-symbolic",
            );
        view_stack
            .add_titled_with_icon(
                &votes_page.container,
                Some("votes"),
                "Voti",
                "view-list-bullet-symbolic",
            );
        view_stack
            .add_titled_with_icon(
                &simulator.container,
                Some("simulator"),
                "Simulatore",
                "accessories-calculator-symbolic",
            );
        view_stack
            .add_titled_with_icon(
                &report_card.container,
                Some("report_card"),
                "Pagella",
                "x-office-spreadsheet-symbolic",
            );
        view_stack
            .add_titled_with_icon(
                &settings_page.container,
                Some("settings"),
                "Impostazioni",
                "emblem-system-symbolic",
            );

        // 3. HeaderBar with ViewSwitcher
        let header_bar = adw::HeaderBar::new();
        let view_switcher = adw::ViewSwitcher::new();
        view_switcher.set_stack(Some(&view_stack));
        view_switcher.set_policy(adw::ViewSwitcherPolicy::Wide);
        header_bar.set_title_widget(Some(&view_switcher));

        // Add Vote Button in HeaderBar
        let add_btn = gtk::Button::builder()
            .icon_name("list-add-symbolic")
            .tooltip_text("Aggiungi nuovo voto")
            .build();
        let sender_clone = sender.clone();
        add_btn.connect_clicked(move |_| {
            sender_clone.input(AppMsg::ShowAddVoteDialog);
        });
        header_bar.pack_start(&add_btn);

        main_box.append(&header_bar);
        main_box.append(&view_stack);

        // 4. Mobile Bottom ViewSwitcherBar
        let view_switcher_bar = adw::ViewSwitcherBar::new();
        view_switcher_bar.set_stack(Some(&view_stack));
        main_box.append(&view_switcher_bar);

        // 5. Adaptive Breakpoint (< 700px collapses to bottom bar)
        let breakpoint = adw::Breakpoint::new(adw::BreakpointCondition::new_length(
            adw::BreakpointConditionLengthType::MaxWidth,
            700.0,
            adw::LengthUnit::Sp,
        ));

        let vs1 = view_switcher.clone();
        let vsb1 = view_switcher_bar.clone();
        breakpoint.connect_apply(move |_| {
            vs1.set_visible(false);
            vsb1.set_reveal(true);
        });

        let vs2 = view_switcher.clone();
        let vsb2 = view_switcher_bar.clone();
        breakpoint.connect_unapply(move |_| {
            vs2.set_visible(true);
            vsb2.set_reveal(false);
        });

        root.add_breakpoint(breakpoint);
        root.set_content(Some(&main_box));

        let model = AppModel {
            db,
            window: root.clone(),
            active_year_id,
            dashboard,
            votes_page,
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
        }
    }
}

fn main() {
    tracing_subscriber::fmt::init();
    let app = RelmApp::new("io.github.mambucodev.votetracker");
    app.run::<AppModel>(());
}
