"""
Unit tests for ClasseViva provider conversion functions.

These tests verify that ClasseViva grade format is correctly converted to
VoteTracker format.
"""
from __future__ import annotations

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from votetracker.classeviva import (
    convert_classeviva_to_votetracker,
    _map_grade_type,
    _parse_term,
)

class TestClasseVivaGradeTypeMapping(unittest.TestCase):
    """Test grade type mapping from ClasseViva to VoteTracker."""

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

class TestClasseVivaTermParsing(unittest.TestCase):
    """Test term parsing from period strings and positions."""

    def test_primary_period_pos(self):
        """Test parsing via periodPos."""
        self.assertEqual(_parse_term("1° Quadrimestre", period_pos=1), 1)
        self.assertEqual(_parse_term("2° Quadrimestre", period_pos=2), 2)
        self.assertEqual(_parse_term("Pentamestre", period_pos=3), 2)  # Any pos > 1 -> 2
        self.assertEqual(_parse_term("Unknown", period_pos=1), 1)
        self.assertEqual(_parse_term("Unknown", period_pos=2), 2)

    def test_fallback_period_desc(self):
        """Test parsing via periodDesc fallback."""
        self.assertEqual(_parse_term("1° Quadrimestre"), 1)
        self.assertEqual(_parse_term("Primo Quadrimestre"), 1)
        self.assertEqual(_parse_term("Quadrimestre 1"), 1)

        self.assertEqual(_parse_term("2° Quadrimestre"), 2)
        self.assertEqual(_parse_term("Secondo Quadrimestre"), 2)
        self.assertEqual(_parse_term("Quadrimestre 2"), 2)
        self.assertEqual(_parse_term("secondo periodo"), 2)

    def test_invalid_data_defaults_to_term1(self):
        """Test that missing or invalid data defaults to term 1."""
        self.assertEqual(_parse_term(""), 1)
        self.assertEqual(_parse_term("Quadrimestre Unico"), 1)
        self.assertEqual(_parse_term("Unknown"), 1)

class TestClasseVivaToVoteTrackerConversion(unittest.TestCase):
    """Test full conversion from ClasseViva format to VoteTracker format."""

    def test_basic_conversion(self):
        """Test conversion of a basic grade."""
        classeviva_grades = [
            {
                "subjectDesc": "MATEMATICA",
                "decimalValue": 8.5,
                "evtDate": "2024-10-15",
                "componentDesc": "Scritto",
                "notesForFamily": "Test di algebra",
                "weightFactor": 1.0,
                "periodDesc": "1° Quadrimestre",
                "periodPos": 1
            }
        ]

        result = convert_classeviva_to_votetracker(classeviva_grades)

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
        classeviva_grades = [
            {
                "subjectDesc": "MATEMATICA",
                "decimalValue": 8.5,
                "evtDate": "2024-10-15",
                "componentDesc": "Scritto",
                "periodPos": 1
            },
            {
                "subjectDesc": "ITALIANO",
                "decimalValue": 7.0,
                "evtDate": "2024-03-20",
                "componentDesc": "Orale",
                "periodPos": 2
            }
        ]

        result = convert_classeviva_to_votetracker(classeviva_grades)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["subject"], "MATEMATICA")
        self.assertEqual(result[0]["term"], 1)
        self.assertEqual(result[1]["subject"], "ITALIANO")
        self.assertEqual(result[1]["term"], 2)

    def test_missing_optional_fields(self):
        """Test conversion with missing optional fields."""
        classeviva_grades = [
            {
                "subjectDesc": "SCIENZE",
                "decimalValue": 7.5,
                "evtDate": "2024-11-10"
                # Missing: componentDesc, notesForFamily, weightFactor, periodDesc/periodPos
            }
        ]

        result = convert_classeviva_to_votetracker(classeviva_grades)

        self.assertEqual(len(result), 1)
        grade = result[0]

        self.assertEqual(grade["subject"], "SCIENZE")
        self.assertEqual(grade["grade"], 7.5)
        self.assertEqual(grade["type"], "Written")  # Default
        self.assertEqual(grade["description"], "")
        self.assertEqual(grade["weight"], 1.0)  # Default
        self.assertEqual(grade["term"], 1)

    def test_skips_canceled_and_invalid_grades(self):
        """Test that canceled and invalid grades are skipped."""
        classeviva_grades = [
            {
                "subjectDesc": "MATEMATICA",
                "decimalValue": 8.5,
                "evtDate": "2024-10-15"
            },
            {
                "subjectDesc": "ITALIANO",
                # Missing decimalValue
                "evtDate": "2024-10-20"
            },
            {
                "subjectDesc": "STORIA",
                "decimalValue": 7.0,
                "evtDate": "2024-11-05",
                "canceled": True  # Canceled grade
            }
        ]

        result = convert_classeviva_to_votetracker(classeviva_grades)

        # Only the first valid non-canceled grade should be converted
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["subject"], "MATEMATICA")

    def test_different_grade_types(self):
        """Test conversion with different grade types."""
        classeviva_grades = [
            {"subjectDesc": "MAT", "decimalValue": 8.0, "componentDesc": "Scritto"},
            {"subjectDesc": "ITA", "decimalValue": 7.5, "componentDesc": "Orale"},
            {"subjectDesc": "SCI", "decimalValue": 9.0, "componentDesc": "Pratico"}
        ]

        result = convert_classeviva_to_votetracker(classeviva_grades)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["type"], "Written")
        self.assertEqual(result[1]["type"], "Oral")
        self.assertEqual(result[2]["type"], "Practical")

if __name__ == '__main__':
    unittest.main()
