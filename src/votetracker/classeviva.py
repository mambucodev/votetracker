"""
ClasseViva API integration module.
Handles authentication and grade fetching from Spaggiari's ClasseViva electronic register.
"""

import requests
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class ClasseVivaClient:
    """Client for interacting with ClasseViva REST API."""

    def __init__(self, username: str = None, password: str = None):
        self.base_url = "https://web.spaggiari.eu/rest/"
        self.token = None
        self.student_id = None
        self.username = username
        self.password = password
        self.token_expiry = None
        self.user_info = {}
        # Numeric student ID will be set after login
        self._student_id_numeric = None

    def _get_headers(self, auth: bool = False) -> Dict[str, str]:
        """Get required headers for API requests."""
        headers = {
            "User-Agent": "CVVS/std/4.2.3 Android/12",
            "Z-Dev-ApiKey": "Tg1NWEwNGIgIC0K",
            "Content-Type": "application/json"
        }

        if auth and self.token:
            headers["Z-Auth-Token"] = self.token

        return headers

    def login(self, username: str = None, password: str = None) -> Tuple[bool, str]:
        """
        Authenticate with ClasseViva.

        Args:
            username: ClasseViva username (optional if set in constructor)
            password: ClasseViva password (optional if set in constructor)

        Returns:
            Tuple of (success: bool, message: str)
        """
        username = username or self.username
        password = password or self.password

        if not username or not password:
            return False, "Username and password required"

        try:
            url = f"{self.base_url}v1/auth/login"
            payload = {
                "ident": None,
                "pass": password,
                "uid": username
            }

            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.student_id = data.get("ident")
                self.token_expiry = data.get("expire")
                self.user_info = {
                    "firstName": data.get("firstName", ""),
                    "lastName": data.get("lastName", "")
                }
                self.username = username
                self.password = password
                # Extract numeric student ID from the ident returned by API
                # The ident field contains the full ID (e.g., "S1234567" or "G1234567")
                # Strip the S/G prefix for use in API endpoints
                if self.student_id:
                    self._student_id_numeric = self.student_id.removeprefix("S").removeprefix("G")
                else:
                    self._student_id_numeric = None

                full_name = f"{self.user_info.get('firstName', '')} {self.user_info.get('lastName', '')}".strip()
                return True, f"Connected as {full_name}" if full_name else "Connected"

            elif response.status_code == 422:
                return False, "Invalid credentials"
            else:
                return False, f"Authentication failed (HTTP {response.status_code})"

        except requests.exceptions.Timeout:
            return False, "Connection timeout - check your internet connection"
        except requests.exceptions.ConnectionError:
            return False, "Network error - cannot reach ClasseViva servers"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_grades(self) -> Tuple[bool, List[Dict], str]:
        """
        Fetch grades from ClasseViva.

        Returns:
            Tuple of (success: bool, grades: List[Dict], message: str)
        """
        if not self.is_authenticated():
            return False, [], "Not authenticated - please log in first"

        try:
            url = f"{self.base_url}v1/students/{self._student_id_numeric}/grades"

            response = requests.get(
                url,
                headers=self._get_headers(auth=True),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                grades = data.get("grades", [])
                return True, grades, f"Fetched {len(grades)} grades"

            elif response.status_code == 401:
                self.token = None  # Clear expired token
                return False, [], "Session expired - please log in again"
            else:
                return False, [], f"Failed to fetch grades (HTTP {response.status_code})"

        except requests.exceptions.Timeout:
            return False, [], "Request timeout - check your internet connection"
        except requests.exceptions.ConnectionError:
            return False, [], "Network error - cannot reach ClasseViva servers"
        except Exception as e:
            return False, [], f"Error: {str(e)}"

    def logout(self):
        """Clear authentication token and session."""
        self.token = None
        self.student_id = None
        self.token_expiry = None
        self.user_info = {}

    def is_authenticated(self) -> bool:
        """Check if client has a valid authentication token."""
        return self.token is not None

    def get_user_display_name(self) -> str:
        """Get the full name of the authenticated user."""
        if not self.user_info:
            return ""

        full_name = f"{self.user_info.get('firstName', '')} {self.user_info.get('lastName', '')}".strip()
        return full_name


def convert_classeviva_to_votetracker(grades: List[Dict]) -> List[Dict]:
    """
    Convert ClasseViva grade format to VoteTracker format.

    Args:
        grades: List of grade dictionaries from ClasseViva API

    Returns:
        List of grade dictionaries compatible with VoteTracker import
    """
    votetracker_grades = []

    for grade in grades:
        # Skip canceled grades
        if grade.get("canceled", False):
            continue

        # Extract subject name
        subject = grade.get("subjectDesc", "Unknown")

        # Extract grade value
        grade_value = grade.get("decimalValue")
        if grade_value is None:
            continue  # Skip if no grade value

        # Extract date
        date = grade.get("evtDate", "")

        # Map componentDesc to type (Orale → Oral, Scritto → Written, etc.)
        component_desc = grade.get("componentDesc", "Written")
        vote_type = _map_grade_type(component_desc)

        # Extract description from notes
        description = grade.get("notesForFamily", "")

        # Extract weight factor
        weight = grade.get("weightFactor", 1.0)
        if weight is None:
            weight = 1.0

        # Parse term from periodDesc (e.g., "1° Quadrimestre" → 1)
        period_desc = grade.get("periodDesc", "")
        term = _parse_term(period_desc)

        # Build VoteTracker-compatible dict
        votetracker_grade = {
            "subject": subject,
            "grade": float(grade_value),
            "type": vote_type,
            "date": date,
            "description": description,
            "weight": float(weight),
            "term": term
        }

        votetracker_grades.append(votetracker_grade)

    return votetracker_grades


def _map_grade_type(component_desc: str) -> str:
    """
    Map ClasseViva componentDesc to VoteTracker type.

    Args:
        component_desc: ClasseViva component description (e.g., "Orale", "Scritto")

    Returns:
        VoteTracker type: "Oral", "Written", or "Practical"
    """
    component_lower = component_desc.lower()

    if "oral" in component_lower or "orale" in component_lower:
        return "Oral"
    elif "scritto" in component_lower or "written" in component_lower or "grafico" in component_lower:
        return "Written"
    elif "pratico" in component_lower or "practical" in component_lower or "laboratorio" in component_lower:
        return "Practical"
    else:
        # Default to Written for unknown types
        return "Written"


def _parse_term(period_desc: str) -> int:
    """
    Parse term number from ClasseViva period description.

    Args:
        period_desc: Period description (e.g., "1° Quadrimestre", "2° Quadrimestre")

    Returns:
        Term number (1 or 2), defaults to 1 if cannot parse
    """
    # Look for "1°" or "2°" or "primo" or "secondo"
    if "2" in period_desc or "secondo" in period_desc.lower():
        return 2
    else:
        return 1  # Default to term 1
