"""
Unit tests for utility functions.
"""

import unittest
from src.votetracker.utils import calc_average, round_report_card, get_status_color
from src.votetracker.constants import PASSING_GRADE, GRADE_INSUFFICIENT


class TestUtils(unittest.TestCase):
    """Test suite for utility functions."""

    # ========================================================================
    # AVERAGE CALCULATION TESTS
    # ========================================================================

    def test_calc_average_empty(self):
        """Test average of empty list."""
        self.assertEqual(calc_average([]), 0.0)

    def test_calc_average_simple(self):
        """Test simple average calculation."""
        votes = [
            {'grade': 8.0, 'weight': 1.0},
            {'grade': 9.0, 'weight': 1.0},
        ]
        self.assertEqual(calc_average(votes), 8.5)

    def test_calc_average_weighted(self):
        """Test weighted average calculation."""
        votes = [
            {'grade': 8.0, 'weight': 1.0},
            {'grade': 10.0, 'weight': 2.0},
        ]
        # (8*1 + 10*2) / (1+2) = 28/3 = 9.333...
        self.assertAlmostEqual(calc_average(votes), 9.333, places=2)

    def test_calc_average_complex(self):
        """Test complex weighted average."""
        votes = [
            {'grade': 6.0, 'weight': 1.0},
            {'grade': 7.5, 'weight': 1.5},
            {'grade': 9.0, 'weight': 2.0},
        ]
        # (6*1 + 7.5*1.5 + 9*2) / (1+1.5+2) = 35.25/4.5 = 7.833...
        self.assertAlmostEqual(calc_average(votes), 7.833, places=2)

    def test_calc_average_zero_weight(self):
        """Test average with zero total weight."""
        votes = [
            {'grade': 8.0, 'weight': 0.0},
        ]
        self.assertEqual(calc_average(votes), 0.0)

    # ========================================================================
    # ROUNDING TESTS
    # ========================================================================

    def test_round_report_card(self):
        """Test Italian rounding (0.5 rounds up)."""
        self.assertEqual(round_report_card(7.5), 8)
        self.assertEqual(round_report_card(7.4), 7)
        self.assertEqual(round_report_card(7.6), 8)
        self.assertEqual(round_report_card(5.5), 6)
        self.assertEqual(round_report_card(5.4), 5)

    def test_round_report_card_edge_cases(self):
        """Test Italian rounding edge cases."""
        self.assertEqual(round_report_card(0.0), 0)
        self.assertEqual(round_report_card(10.0), 10)
        self.assertEqual(round_report_card(0.5), 1)
        self.assertEqual(round_report_card(9.5), 10)

    # ========================================================================
    # COLOR TESTS
    # ========================================================================

    def test_get_status_color_failing(self):
        """Test status color for failing grades."""
        color = get_status_color(4.0)
        self.assertEqual(color.name(), "#e74c3c")  # Red

        color = get_status_color(5.0)
        self.assertEqual(color.name(), "#e74c3c")  # Red

    def test_get_status_color_warning(self):
        """Test status color for warning grades."""
        color = get_status_color(5.5)
        self.assertEqual(color.name(), "#f39c12")  # Orange

        color = get_status_color(5.9)
        self.assertEqual(color.name(), "#f39c12")  # Orange

    def test_get_status_color_passing(self):
        """Test status color for passing grades."""
        color = get_status_color(6.0)
        self.assertEqual(color.name(), "#27ae60")  # Green

        color = get_status_color(8.0)
        self.assertEqual(color.name(), "#27ae60")  # Green

        color = get_status_color(10.0)
        self.assertEqual(color.name(), "#27ae60")  # Green

    def test_get_status_color_thresholds(self):
        """Test exact threshold values."""
        # Just below 5.5 should be red
        color = get_status_color(GRADE_INSUFFICIENT - 0.01)
        self.assertEqual(color.name(), "#e74c3c")

        # Exactly 5.5 should be orange
        color = get_status_color(GRADE_INSUFFICIENT)
        self.assertEqual(color.name(), "#f39c12")

        # Just below 6.0 should be orange
        color = get_status_color(PASSING_GRADE - 0.01)
        self.assertEqual(color.name(), "#f39c12")

        # Exactly 6.0 should be green
        color = get_status_color(PASSING_GRADE)
        self.assertEqual(color.name(), "#27ae60")


if __name__ == '__main__':
    unittest.main()
