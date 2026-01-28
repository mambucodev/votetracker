"""
Unit tests for database module.
"""

import unittest
import tempfile
import os
from src.votetracker.database import Database


class TestDatabase(unittest.TestCase):
    """Test suite for Database class."""

    def setUp(self):
        """Create temporary database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        # Monkey-patch get_db_path to use temp file
        import src.votetracker.database as db_module
        self.original_get_db_path = db_module.get_db_path
        db_module.get_db_path = lambda: self.temp_db.name

        self.db = Database()

    def tearDown(self):
        """Clean up temp database."""
        import src.votetracker.database as db_module
        db_module.get_db_path = self.original_get_db_path
        self.db.close()
        os.unlink(self.temp_db.name)

    # ========================================================================
    # SUBJECT TESTS
    # ========================================================================

    def test_add_subject(self):
        """Test adding a subject."""
        subject_id = self.db.add_subject("Math")
        self.assertIsNotNone(subject_id)

        # Verify it exists
        subjects = self.db.get_subjects()
        self.assertIn("Math", subjects)

    def test_add_duplicate_subject(self):
        """Test adding duplicate subject returns existing ID."""
        id1 = self.db.add_subject("Math")
        id2 = self.db.add_subject("Math")
        self.assertEqual(id1, id2)

    def test_rename_subject(self):
        """Test renaming a subject."""
        self.db.add_subject("Math")
        result = self.db.rename_subject("Math", "Mathematics")
        self.assertTrue(result)

        subjects = self.db.get_subjects()
        self.assertIn("Mathematics", subjects)
        self.assertNotIn("Math", subjects)

    def test_delete_subject(self):
        """Test deleting a subject."""
        self.db.add_subject("Math")
        result = self.db.delete_subject("Math")
        self.assertTrue(result)

        subjects = self.db.get_subjects()
        self.assertNotIn("Math", subjects)

    def test_subject_caching(self):
        """Test that subjects are cached correctly."""
        # Add subjects
        self.db.add_subject("Math")
        self.db.add_subject("Science")

        # Get subjects (should cache)
        subjects1 = self.db.get_subjects()

        # Get again (should return from cache)
        subjects2 = self.db.get_subjects()

        self.assertEqual(subjects1, subjects2)

        # Force refresh
        subjects3 = self.db.get_subjects(force_refresh=True)
        self.assertEqual(subjects1, subjects3)

    # ========================================================================
    # SCHOOL YEAR TESTS
    # ========================================================================

    def test_add_school_year(self):
        """Test adding a school year."""
        # Default year is created, add another
        result = self.db.add_school_year(2030)
        self.assertTrue(result)

        years = self.db.get_school_years()
        year_names = [y['name'] for y in years]
        self.assertIn("2030/2031", year_names)

    def test_school_year_caching(self):
        """Test that school years are cached correctly."""
        years1 = self.db.get_school_years()
        years2 = self.db.get_school_years()

        # Should be equal (from cache)
        self.assertEqual(len(years1), len(years2))

    # ========================================================================
    # VOTE TESTS
    # ========================================================================

    def test_add_vote(self):
        """Test adding a vote."""
        # Create school year first
        active_year = self.db.get_active_school_year()
        self.assertIsNotNone(active_year)

        # Add vote
        vote_id = self.db.add_vote(
            subject="Math",
            grade=8.5,
            vote_type="Written",
            date="2024-01-15",
            description="Test",
            term=1,
            weight=1.0,
            school_year_id=active_year['id']
        )
        self.assertIsNotNone(vote_id)

        # Verify it exists
        votes = self.db.get_votes(subject="Math")
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0]['grade'], 8.5)

    def test_update_vote(self):
        """Test updating a vote."""
        active_year = self.db.get_active_school_year()

        # Add vote
        vote_id = self.db.add_vote(
            subject="Math",
            grade=8.5,
            vote_type="Written",
            date="2024-01-15",
            description="Test",
            term=1,
            weight=1.0,
            school_year_id=active_year['id']
        )

        # Update it
        result = self.db.update_vote(
            vote_id=vote_id,
            subject="Math",
            grade=9.0,
            vote_type="Written",
            date="2024-01-15",
            description="Updated",
            term=1,
            weight=1.0
        )
        self.assertTrue(result)

        # Verify update
        votes = self.db.get_votes(subject="Math")
        self.assertEqual(votes[0]['grade'], 9.0)
        self.assertEqual(votes[0]['description'], "Updated")

    def test_delete_vote(self):
        """Test deleting a vote."""
        active_year = self.db.get_active_school_year()

        # Add vote
        vote_id = self.db.add_vote(
            subject="Math",
            grade=8.5,
            vote_type="Written",
            date="2024-01-15",
            description="Test",
            term=1,
            weight=1.0,
            school_year_id=active_year['id']
        )

        # Delete it
        result = self.db.delete_vote(vote_id)
        self.assertTrue(result)

        # Verify deletion
        votes = self.db.get_votes(subject="Math")
        self.assertEqual(len(votes), 0)

    def test_get_votes_filtering(self):
        """Test vote filtering by subject, year, term."""
        active_year = self.db.get_active_school_year()

        # Add multiple votes
        self.db.add_vote("Math", 8.5, "Written", "2024-01-15", "", 1, 1.0, active_year['id'])
        self.db.add_vote("Math", 7.5, "Oral", "2024-01-16", "", 1, 1.0, active_year['id'])
        self.db.add_vote("Science", 9.0, "Written", "2024-01-17", "", 1, 1.0, active_year['id'])
        self.db.add_vote("Math", 8.0, "Written", "2024-01-18", "", 2, 1.0, active_year['id'])

        # Filter by subject
        math_votes = self.db.get_votes(subject="Math")
        self.assertEqual(len(math_votes), 3)

        # Filter by term
        term1_votes = self.db.get_votes(term=1)
        self.assertEqual(len(term1_votes), 3)

        # Filter by subject and term
        math_term1 = self.db.get_votes(subject="Math", term=1)
        self.assertEqual(len(math_term1), 2)

    def test_grade_statistics(self):
        """Test grade statistics calculation."""
        active_year = self.db.get_active_school_year()

        # Add votes for multiple subjects
        self.db.add_vote("Math", 8.0, "Written", "2024-01-15", "", 1, 1.0, active_year['id'])
        self.db.add_vote("Math", 9.0, "Written", "2024-01-16", "", 1, 1.0, active_year['id'])
        self.db.add_vote("Science", 7.0, "Written", "2024-01-17", "", 1, 1.0, active_year['id'])
        self.db.add_vote("Science", 8.0, "Written", "2024-01-18", "", 1, 1.0, active_year['id'])

        stats = self.db.get_grade_statistics()

        self.assertEqual(stats['total_votes'], 4)
        self.assertAlmostEqual(stats['subject_avgs']['Math'], 8.5, places=2)
        self.assertAlmostEqual(stats['subject_avgs']['Science'], 7.5, places=2)
        self.assertAlmostEqual(stats['overall_avg'], 8.0, places=2)  # (8.5 + 7.5) / 2

    # ========================================================================
    # GRADE GOALS TESTS
    # ========================================================================

    def test_set_grade_goal(self):
        """Test setting a grade goal."""
        self.db.add_subject("Math")
        active_year = self.db.get_active_school_year()

        result = self.db.set_grade_goal("Math", 8.0, active_year['id'], 1)
        self.assertTrue(result)

        goal = self.db.get_grade_goal("Math", active_year['id'], 1)
        self.assertEqual(goal, 8.0)

    def test_delete_grade_goal(self):
        """Test deleting a grade goal."""
        self.db.add_subject("Math")
        active_year = self.db.get_active_school_year()

        self.db.set_grade_goal("Math", 8.0, active_year['id'], 1)
        result = self.db.delete_grade_goal("Math", active_year['id'], 1)
        self.assertTrue(result)

        goal = self.db.get_grade_goal("Math", active_year['id'], 1)
        self.assertIsNone(goal)

    def test_calculate_needed_grade(self):
        """Test calculating needed grade to reach goal."""
        active_year = self.db.get_active_school_year()

        # Add some votes
        self.db.add_vote("Math", 7.0, "Written", "2024-01-15", "", 1, 1.0, active_year['id'])
        self.db.add_vote("Math", 8.0, "Written", "2024-01-16", "", 1, 1.0, active_year['id'])

        # Current average is 7.5, target is 8.0
        needed = self.db.calculate_needed_grade("Math", 8.0, active_year['id'], 1, 1.0)

        # (7 + 8 + needed) / 3 = 8.0
        # needed = 9.0
        self.assertIsNotNone(needed)
        self.assertAlmostEqual(needed, 9.0, places=1)


if __name__ == '__main__':
    unittest.main()
