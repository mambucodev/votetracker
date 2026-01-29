"""
Axios Sync Provider Implementation

Integrates with Axios Italia electronic register system using the axios Python library.
Automatically detects available students and allows selection if multiple found.
"""

import subprocess
import json
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from lxml import html
import requests
from ..sync_provider import SyncProvider

try:
    from axios.navigator import Navigator
    from axios.models import Credentials
    AXIOS_AVAILABLE = True
except ImportError:
    AXIOS_AVAILABLE = False


class AxiosProvider(SyncProvider):
    """Axios implementation using axios Python library with auto student detection."""

    def __init__(self, database):
        super().__init__(database)
        self._credentials = {}
        self._selected_student_id = None
        self._available_students = []  # List of (student_id, student_name) tuples
        self._navigator = None

    def get_provider_name(self) -> str:
        """Get human-readable provider name."""
        return "Axios"

    def _scrape_students(self, customer_id: str, username: str, password: str) -> List[Tuple[str, str]]:
        """
        Scrape available students from Axios web interface.

        Args:
            customer_id: School customer ID
            username: Login username
            password: Login password

        Returns:
            List of (student_id, student_name) tuples

        Raises:
            Exception: If login fails or cannot find students
        """
        # Helper function for headers (same as axios library)
        def headers_for(url: str) -> dict:
            return {
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://family.axioscloud.it",
                "Referer": url,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }

        session = requests.Session()
        start_url = f"https://family.axioscloud.it/Secret/REStart.aspx?Customer_ID={customer_id}"

        try:
            # Get the login page with proper headers
            resp = session.get(start_url, headers=headers_for(start_url), timeout=10)

            # DEBUG: Save initial page
            try:
                with open("/tmp/axios_initial_page.html", 'w', encoding='utf-8') as f:
                    f.write(resp.text)
            except:
                pass

            tree = html.fromstring(resp.text)

            # Extract ASP.NET viewstate (with safety checks)
            viewstate_list = tree.xpath('//input[@id="__VIEWSTATE"]/@value')
            viewstategenerator_list = tree.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value')
            eventvalidation_list = tree.xpath('//input[@id="__EVENTVALIDATION"]/@value')

            if not viewstate_list or not viewstategenerator_list or not eventvalidation_list:
                raise Exception(
                    f"Failed to extract login form data. "
                    f"Customer ID '{customer_id}' may be invalid. "
                    f"Page saved to /tmp/axios_initial_page.html. "
                    f"Verify customer ID at https://family.axioscloud.it"
                )

            viewstate = viewstate_list[0]
            viewstategenerator = viewstategenerator_list[0]
            eventvalidation = eventvalidation_list[0]

            # Initial POST (seems required by axios)
            start_payload = {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                "ibtnRE.x": 0,
                "ibtnRE.y": 0,
                "mha": "",
            }
            resp = session.post(start_url, data=start_payload, headers=headers_for(start_url), timeout=10)
            tree = html.fromstring(resp.text)

            # Update viewstate
            viewstate_list = tree.xpath('//input[@id="__VIEWSTATE"]/@value')
            viewstategenerator_list = tree.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value')
            eventvalidation_list = tree.xpath('//input[@id="__EVENTVALIDATION"]/@value')

            if not viewstate_list or not viewstategenerator_list or not eventvalidation_list:
                raise Exception("Failed to extract updated login form data")

            viewstate = viewstate_list[0]
            viewstategenerator = viewstategenerator_list[0]
            eventvalidation = eventvalidation_list[0]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            if "extract" in str(e):
                raise
            raise Exception(f"Failed to access login page: {str(e)}")

        # Actual login
        login_payload = {
            "__LASTFOCUS": "",
            "__EVENTTARGET": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "txtImproveDone": "",
            "txtUser": username,
            "txtPassword": password,
            "btnLogin": "Accedi",
        }
        login_url = "https://family.axioscloud.it/Secret/RELogin.aspx"
        resp = session.post(
            login_url,
            data=login_payload,
            headers=headers_for(start_url),
            timeout=10
        )
        tree = html.fromstring(resp.text)

        # Check if login successful
        user_name = tree.xpath('//span[@id="lblUserName"]/text()')
        if not user_name:
            raise Exception("Login failed - check username and password")

        # DEBUG: Save HTML for inspection
        debug_html_path = "/tmp/axios_login_debug.html"
        try:
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(resp.text)
        except:
            pass  # Ignore debug write errors

        # Look for student selector dropdown
        # Common patterns: select with options, or hidden inputs with student data
        students = []

        # Try to find student dropdown (if multiple students)
        student_options = tree.xpath('//select[contains(@id, "Student") or contains(@name, "Alu")]//option')
        if student_options:
            for option in student_options:
                student_id = option.get('value', '').strip()
                student_name = option.text_content().strip()
                if student_id and student_name and student_id != '':
                    students.append((student_id, student_name))

        # If no dropdown found, might be single student - extract from page
        if not students:
            # Try various XPath patterns for student ID
            patterns = [
                '//input[contains(@id, "AluSelected")]/@value',
                '//input[contains(@id, "txtAluSelected")]/@value',
                '//input[contains(@name, "AluSelected")]/@value',
                '//input[@id="ctl00_ContentPlaceHolderBody_txtAluSelected"]/@value',
                '//span[contains(@id, "AluSelected")]/text()',
            ]

            for pattern in patterns:
                student_id_input = tree.xpath(pattern)
                if student_id_input and student_id_input[0].strip():
                    student_id = student_id_input[0].strip()
                    # Use the logged-in user name as student name
                    student_name = user_name[0] if user_name else "Student"
                    students.append((student_id, student_name))
                    break

        # If still no students, try to find ANY input with a numeric value
        # (student IDs are usually numeric)
        if not students:
            all_inputs = tree.xpath('//input[@type="hidden"]')
            for inp in all_inputs:
                inp_id = inp.get('id', '')
                inp_value = inp.get('value', '').strip()
                # Look for patterns that might be student IDs
                if 'alu' in inp_id.lower() and inp_value and inp_value.isdigit():
                    student_name = user_name[0] if user_name else "Student"
                    students.append((inp_value, student_name))
                    break

        if not students:
            # Provide helpful error with debug info
            raise Exception(
                f"Could not find student information. "
                f"HTML saved to {debug_html_path} for debugging. "
                f"Please report this issue with your customer ID (school code)."
            )

        return students

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
            }
        ]

    def login(self, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """
        Authenticate with Axios and auto-detect students.

        Args:
            credentials: Dict with customer_id, username, password
                        Optionally: student_id if already selected

        Returns:
            Tuple of (success: bool, message: str)
            Special case: If multiple students found, returns (False, "MULTIPLE_STUDENTS:{json_data}")
        """
        customer_id = credentials.get('customer_id', '').strip()
        username = credentials.get('username', '').strip()
        password = credentials.get('password', '').strip()
        student_id = credentials.get('student_id', '').strip()  # Optional

        # Validate required fields
        if not all([customer_id, username, password]):
            return False, "Customer ID, username, and password are required"

        # Check if axios library is available
        if not AXIOS_AVAILABLE:
            return False, "Axios library not found. Please install: pip install axios"

        # Check if axios CLI is installed
        try:
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

        # Store credentials
        self._credentials = credentials.copy()

        # If student_id already provided (from selection), use it directly
        if student_id:
            self._selected_student_id = student_id
        else:
            # Scrape available students
            try:
                self._available_students = self._scrape_students(customer_id, username, password)
            except Exception as e:
                return False, f"Failed to retrieve student information: {str(e)}"

            if not self._available_students:
                return False, "No students found for this account"

            # If only one student, auto-select it
            if len(self._available_students) == 1:
                self._selected_student_id = self._available_students[0][0]
                student_name = self._available_students[0][1]
                # Store in credentials for future use
                self._credentials['student_id'] = self._selected_student_id
            else:
                # Multiple students - return special message for UI to handle
                students_json = json.dumps([
                    {"id": sid, "name": sname}
                    for sid, sname in self._available_students
                ])
                return False, f"MULTIPLE_STUDENTS:{students_json}"

        # Test connection by fetching grades
        success, grades, message = self.get_grades()

        if success:
            self._authenticated = True
            # Set display name
            if self._available_students:
                student_name = next(
                    (name for sid, name in self._available_students if sid == self._selected_student_id),
                    username
                )
                self._user_display_name = f"{student_name}"
            else:
                self._user_display_name = username

            # Warn if no grades found
            if len(grades) == 0:
                return True, f"Connected as {self._user_display_name} (No grades found - check school year/term)"
            else:
                return True, f"Connected as {self._user_display_name} ({len(grades)} grades found)"
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

        if not self._selected_student_id:
            return False, [], "No student selected - please reconnect"

        try:
            # Prepare environment variables for axios CLI
            env = os.environ.copy()
            env.update({
                'AXIOS_CUSTOMER_ID': self._credentials.get('customer_id', ''),
                'AXIOS_USERNAME': self._credentials.get('username', ''),
                'AXIOS_PASSWORD': self._credentials.get('password', ''),
                'AXIOS_STUDENT_ID': self._selected_student_id
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
        self._selected_student_id = None
        self._available_students = []
        self._navigator = None


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
