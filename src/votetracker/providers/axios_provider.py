"""
Axios Sync Provider Implementation

Integrates with Axios Italia electronic register system via the axios Python CLI.
"""

import subprocess
import json
import os
from typing import List, Dict, Tuple
from datetime import datetime
from ..sync_provider import SyncProvider


class AxiosProvider(SyncProvider):
    """Axios implementation using axios Python library (CLI wrapper)."""

    def __init__(self, database):
        super().__init__(database)
        self._credentials = {}

    def get_provider_name(self) -> str:
        """Get human-readable provider name."""
        return "Axios"

    def get_credential_fields(self) -> List[Dict[str, str]]:
        """
        Get credential field definitions for Axios.

        Returns:
            List of field definitions for Axios authentication
        """
        return [
            {
                'name': 'customer_id',
                'label': 'Customer ID (School Tax Code)',
                'type': 'text',
                'placeholder': 'AAAA12345678B'
            },
            {
                'name': 'username',
                'label': 'Username',
                'type': 'text',
                'placeholder': 'student.name'
            },
            {
                'name': 'password',
                'label': 'Password',
                'type': 'password',
                'placeholder': ''
            },
            {
                'name': 'student_id',
                'label': 'Student ID',
                'type': 'text',
                'placeholder': '12345'
            }
        ]

    def login(self, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """
        Authenticate with Axios.

        For Axios, authentication is handled via environment variables
        during each CLI call. We test credentials by attempting to fetch grades.

        Args:
            credentials: Dict with customer_id, username, password, student_id

        Returns:
            Tuple of (success: bool, message: str)
        """
        customer_id = credentials.get('customer_id', '').strip()
        username = credentials.get('username', '').strip()
        password = credentials.get('password', '').strip()
        student_id = credentials.get('student_id', '').strip()

        # Validate all fields present
        if not all([customer_id, username, password, student_id]):
            return False, "All credential fields are required"

        # Store credentials for use in get_grades()
        self._credentials = credentials.copy()

        # Test credentials by attempting to fetch grades
        # (axios CLI validates on each call, no persistent session)
        try:
            # Check if axios CLI is installed
            result = subprocess.run(
                ['axios', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return False, "Axios CLI not found. Please install: pip install axios"

        except FileNotFoundError:
            return False, "Axios CLI not found. Please install: pip install axios"
        except Exception as e:
            return False, f"Error checking axios CLI: {str(e)}"

        # Try fetching grades to validate credentials
        success, grades, message = self.get_grades()

        if success:
            self._authenticated = True
            self._user_display_name = f"{username} ({student_id})"
            return True, f"Connected as {username}"
        else:
            return False, f"Authentication failed: {message}"

    def get_grades(self) -> Tuple[bool, List[Dict], str]:
        """
        Fetch grades from Axios.

        Returns:
            Tuple of (success: bool, grades: List[Dict], message: str)
            Grades are in VoteTracker format after conversion
        """
        if not self._credentials:
            return False, [], "Not authenticated - please log in first"

        try:
            # Prepare environment variables for axios CLI
            env = os.environ.copy()
            env.update({
                'AXIOS_CUSTOMER_ID': self._credentials.get('customer_id', ''),
                'AXIOS_USERNAME': self._credentials.get('username', ''),
                'AXIOS_PASSWORD': self._credentials.get('password', ''),
                'AXIOS_STUDENT_ID': self._credentials.get('student_id', '')
            })

            # Call axios CLI to fetch grades
            result = subprocess.run(
                ['axios', '--output-format', 'json', 'grades', 'list'],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"

                # Check for common error patterns
                if "authentication" in error_msg.lower() or "invalid" in error_msg.lower():
                    return False, [], "Invalid credentials"
                elif "not found" in error_msg.lower() or "student" in error_msg.lower():
                    return False, [], "Student not found or access denied"
                elif "timeout" in error_msg.lower():
                    return False, [], "Connection timeout - check your internet connection"
                else:
                    return False, [], f"Axios CLI error: {error_msg}"

            # Parse JSON output
            try:
                raw_grades = json.loads(result.stdout)
            except json.JSONDecodeError:
                return False, [], "Invalid response from Axios CLI"

            # Convert to VoteTracker format
            votetracker_grades = convert_axios_to_votetracker(raw_grades)

            return True, votetracker_grades, f"Fetched {len(votetracker_grades)} grades"

        except subprocess.TimeoutExpired:
            return False, [], "Request timeout - check your internet connection"
        except FileNotFoundError:
            return False, [], "Axios CLI not found. Please install: pip install axios"
        except Exception as e:
            return False, [], f"Error: {str(e)}"

    def logout(self):
        """Clear authentication state."""
        super().logout()
        self._credentials = {}


def convert_axios_to_votetracker(grades: List[Dict]) -> List[Dict]:
    """
    Convert Axios grade format to VoteTracker format.

    Args:
        grades: List of grade dictionaries from Axios CLI

    Returns:
        List of grade dictionaries compatible with VoteTracker import
    """
    votetracker_grades = []

    for grade in grades:
        # Skip if missing essential data
        if not grade.get('value') or not grade.get('subject'):
            continue

        # Extract subject name
        subject = grade.get('subject', 'Unknown')

        # Extract grade value
        try:
            grade_value = float(grade.get('value'))
        except (ValueError, TypeError):
            continue  # Skip invalid grades

        # Extract date (expect ISO format YYYY-MM-DD)
        date = grade.get('date', '')
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        # Map kind to type (Scritto→Written, Orale→Oral, Pratico→Practical)
        kind = grade.get('kind', 'Scritto')
        vote_type = _map_grade_type(kind)

        # Extract description/comment
        description = grade.get('comment', '')

        # Extract weight (default to 1.0)
        weight = grade.get('weight', 1.0)
        try:
            weight = float(weight)
        except (ValueError, TypeError):
            weight = 1.0

        # Parse term from date (Sep-Jan = term 1, Feb-Jun = term 2)
        term = _parse_term_from_date(date)

        # Build VoteTracker-compatible dict
        votetracker_grade = {
            "subject": subject,
            "grade": grade_value,
            "type": vote_type,
            "date": date,
            "description": description,
            "weight": weight,
            "term": term
        }

        votetracker_grades.append(votetracker_grade)

    return votetracker_grades


def _map_grade_type(kind: str) -> str:
    """
    Map Axios kind to VoteTracker type.

    Args:
        kind: Axios grade kind (e.g., "Scritto", "Orale", "Pratico")

    Returns:
        VoteTracker type: "Oral", "Written", or "Practical"
    """
    kind_lower = kind.lower()

    if "oral" in kind_lower or "orale" in kind_lower:
        return "Oral"
    elif "scritto" in kind_lower or "written" in kind_lower or "grafico" in kind_lower:
        return "Written"
    elif "pratico" in kind_lower or "practical" in kind_lower or "laboratorio" in kind_lower:
        return "Practical"
    else:
        # Default to Written for unknown types
        return "Written"


def _parse_term_from_date(date_str: str) -> int:
    """
    Infer term from date.

    Italian school system typically:
    - Term 1 (Primo Quadrimestre): September to January
    - Term 2 (Secondo Quadrimestre): February to June

    Args:
        date_str: Date string in ISO format (YYYY-MM-DD)

    Returns:
        Term number (1 or 2), defaults to 1 if cannot parse
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        month = date_obj.month

        # Term 1: September (9) through January (1)
        # Term 2: February (2) through June (6), July (7), August (8)
        if month >= 2 and month <= 8:
            return 2
        else:
            return 1

    except (ValueError, AttributeError):
        return 1  # Default to term 1
