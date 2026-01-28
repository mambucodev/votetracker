"""
Unit tests for Axios provider conversion functions.

These tests verify that Axios grade format is correctly converted to
VoteTracker format.
"""

import unittest
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from votetracker.providers.axios_provider import (
    convert_axios_to_votetracker,
    _map_grade_type,
    _parse_term_from_date
)


class TestAxiosGradeTypeMapping(unittest.TestCase):
    """Test grade type mapping from Axios to VoteTracker."""

    def test_oral_mapping(self):
        """Test oral grade types."""
        self.assertEqual(_map_grade_type("Orale"), "Oral")
        self.assertEqual(_map_grade_type("orale"), "Oral")
        self.assertEqual(_map_grade_type("ORALE"), "Oral")
        self.assertEqual(_map_grade_type("oral"), "Oral")

    def test_written_mapping(self):
        """Test written grade types."""
        self.assertEqual(_map_grade_type("Scritto"), "Written")
        self.assertEqual(_map_grade_type("scritto"), "Written")
        self.assertEqual(_map_grade_type("SCRITTO"), "Written")
        self.assertEqual(_map_grade_type("written"), "Written")
        self.assertEqual(_map_grade_type("Grafico"), "Written")

    def test_practical_mapping(self):
        """Test practical grade types."""
        self.assertEqual(_map_grade_type("Pratico"), "Practical")
        self.assertEqual(_map_grade_type("pratico"), "Practical")
        self.assertEqual(_map_grade_type("PRATICO"), "Practical")
        self.assertEqual(_map_grade_type("practical"), "Practical")
        self.assertEqual(_map_grade_type("Laboratorio"), "Practical")

    def test_unknown_defaults_to_written(self):
        """Test that unknown types default to Written."""
        self.assertEqual(_map_grade_type("Unknown"), "Written")
        self.assertEqual(_map_grade_type(""), "Written")
        self.assertEqual(_map_grade_type("Altro"), "Written")


class TestAxiosTermParsing(unittest.TestCase):
    """Test term parsing from dates."""

    def test_term1_months(self):
        """Test dates in term 1 (Sep-Jan)."""
        self.assertEqual(_parse_term_from_date("2024-09-15"), 1)  # September
        self.assertEqual(_parse_term_from_date("2024-10-20"), 1)  # October
        self.assertEqual(_parse_term_from_date("2024-11-05"), 1)  # November
        self.assertEqual(_parse_term_from_date("2024-12-12"), 1)  # December
        self.assertEqual(_parse_term_from_date("2024-01-30"), 1)  # January

    def test_term2_months(self):
        """Test dates in term 2 (Feb-Aug)."""
        self.assertEqual(_parse_term_from_date("2024-02-15"), 2)  # February
        self.assertEqual(_parse_term_from_date("2024-03-20"), 2)  # March
        self.assertEqual(_parse_term_from_date("2024-04-10"), 2)  # April
        self.assertEqual(_parse_term_from_date("2024-05-25"), 2)  # May
        self.assertEqual(_parse_term_from_date("2024-06-10"), 2)  # June
        self.assertEqual(_parse_term_from_date("2024-07-05"), 2)  # July
        self.assertEqual(_parse_term_from_date("2024-08-20"), 2)  # August

    def test_invalid_date_defaults_to_term1(self):
        """Test that invalid dates default to term 1."""
        self.assertEqual(_parse_term_from_date("invalid"), 1)
        self.assertEqual(_parse_term_from_date(""), 1)
        self.assertEqual(_parse_term_from_date("2024-13-01"), 1)  # Invalid month


class TestAxiosToVoteTrackerConversion(unittest.TestCase):
    """Test full conversion from Axios format to VoteTracker format."""

    def test_basic_conversion(self):
        """Test conversion of a basic grade."""
        axios_grades = [
            {
                "subject": "MATEMATICA",
                "value": 8.5,
                "kind": "Scritto",
                "date": "2024-10-15",
                "comment": "Test di algebra",
                "weight": 1.0
            }
        ]

        result = convert_axios_to_votetracker(axios_grades)

        self.assertEqual(len(result), 1)
        grade = result[0]

        self.assertEqual(grade["subject"], "MATEMATICA")
        self.assertEqual(grade["grade"], 8.5)
        self.assertEqual(grade["type"], "Written")
        self.assertEqual(grade["date"], "2024-10-15")
        self.assertEqual(grade["description"], "Test di algebra")
        self.assertEqual(grade["weight"], 1.0)
        self.assertEqual(grade["term"], 1)

    def test_multiple_grades_conversion(self):
        """Test conversion of multiple grades."""
        axios_grades = [
            {
                "subject": "MATEMATICA",
                "value": 8.5,
                "kind": "Scritto",
                "date": "2024-10-15",
                "comment": "Test",
                "weight": 1.0
            },
            {
                "subject": "ITALIANO",
                "value": 7.0,
                "kind": "Orale",
                "date": "2024-03-20",
                "comment": "Interrogazione",
                "weight": 1.5
            }
        ]

        result = convert_axios_to_votetracker(axios_grades)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["subject"], "MATEMATICA")
        self.assertEqual(result[0]["term"], 1)
        self.assertEqual(result[1]["subject"], "ITALIANO")
        self.assertEqual(result[1]["term"], 2)

    def test_missing_optional_fields(self):
        """Test conversion with missing optional fields."""
        axios_grades = [
            {
                "subject": "SCIENZE",
                "value": 7.5,
                "date": "2024-11-10"
                # Missing: kind, comment, weight
            }
        ]

        result = convert_axios_to_votetracker(axios_grades)

        self.assertEqual(len(result), 1)
        grade = result[0]

        self.assertEqual(grade["subject"], "SCIENZE")
        self.assertEqual(grade["grade"], 7.5)
        self.assertEqual(grade["type"], "Written")  # Default
        self.assertEqual(grade["description"], "")
        self.assertEqual(grade["weight"], 1.0)  # Default

    def test_skips_invalid_grades(self):
        """Test that invalid grades are skipped."""
        axios_grades = [
            {
                "subject": "MATEMATICA",
                "value": 8.5,
                "date": "2024-10-15"
            },
            {
                "subject": "ITALIANO",
                # Missing value
                "date": "2024-10-20"
            },
            {
                # Missing subject
                "value": 7.0,
                "date": "2024-11-05"
            },
            {
                "subject": "SCIENZE",
                "value": "invalid",  # Invalid value
                "date": "2024-11-10"
            }
        ]

        result = convert_axios_to_votetracker(axios_grades)

        # Only the first valid grade should be converted
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["subject"], "MATEMATICA")

    def test_different_grade_types(self):
        """Test conversion with different grade types."""
        axios_grades = [
            {"subject": "MAT", "value": 8.0, "kind": "Scritto", "date": "2024-10-15"},
            {"subject": "ITA", "value": 7.5, "kind": "Orale", "date": "2024-10-20"},
            {"subject": "SCI", "value": 9.0, "kind": "Pratico", "date": "2024-11-05"}
        ]

        result = convert_axios_to_votetracker(axios_grades)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["type"], "Written")
        self.assertEqual(result[1]["type"], "Oral")
        self.assertEqual(result[2]["type"], "Practical")


if __name__ == '__main__':
    unittest.main()
