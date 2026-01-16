"""
Page widgets for VoteTracker.
Each module contains a page widget for the main application.
"""

from .dashboard import DashboardPage
from .votes import VotesPage
from .subjects import SubjectsPage
from .simulator import SimulatorPage
from .calendar import CalendarPage
from .report_card import ReportCardPage
from .statistics import StatisticsPage
from .settings import SettingsPage

__all__ = [
    "DashboardPage",
    "VotesPage",
    "SubjectsPage",
    "SimulatorPage",
    "CalendarPage",
    "ReportCardPage",
    "StatisticsPage",
    "SettingsPage",
]
