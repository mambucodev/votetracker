"""
Axios Sync Provider Implementation - New Registro Famiglie

Integrates with Axios Italia's NEW electronic register system (registrofamiglie.axioscloud.it).
Replaces the old family.axioscloud.it system which is deprecated for 2025/2026.
"""

import json
import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from lxml import html
import requests
from ..sync_provider import SyncProvider


class AxiosProvider(SyncProvider):
    """Axios implementation using NEW Registro Famiglie (registrofamiglie.axioscloud.it)."""

    def __init__(self, database):
        super().__init__(database)
        self._credentials = {}
        self._session = None
        self._selected_student_id = None
        self._available_students = []

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
                'placeholder': '80202890580'
            },
            {
                'name': 'username',
                'label': 'Username or Email',
                'type': 'text',
                'placeholder': 'username or email@example.com'
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
        Authenticate with Axios Registro Famiglie.

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

        # Store credentials
        self._credentials = credentials.copy()

        # Create session
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        })

        try:
            # Step 1: GET login page to establish session
            login_url = "https://registrofamiglie.axioscloud.it/Pages/SD/SD_Login.aspx"
            resp = self._session.get(login_url, timeout=10)

            if resp.status_code != 200:
                return False, f"Failed to load login page (HTTP {resp.status_code})"

            # Step 2: POST login credentials
            login_data = {
                'customerid': customer_id,
                'username': username,
                'password': password
            }

            resp = self._session.post(login_url, data=login_data, timeout=15, allow_redirects=True)

            # Debug: save response
            try:
                with open("/tmp/axios_registrofamiglie_login.html", 'w', encoding='utf-8') as f:
                    f.write(resp.text)
            except:
                pass

            # Check if login successful
            # Look for error messages or success indicators
            tree = html.fromstring(resp.text)

            # Check for error messages
            error_divs = tree.xpath('//div[contains(@class, "alert-danger")]//text()')
            if error_divs:
                error_msg = ' '.join([e.strip() for e in error_divs if e.strip()])
                if error_msg and len(error_msg) > 10:
                    return False, f"Login failed: {error_msg}"

            # Check if we're still on login page (indicates failure)
            if "Login" in resp.text and "form-title" in resp.text:
                # Still on login page - check why
                if "customerid" in resp.text.lower():
                    return False, "Login failed - check customer ID, username, and password"

            # If student_id already provided, use it
            if student_id:
                self._selected_student_id = student_id
                self._authenticated = True
                self._user_display_name = username
                return True, f"Connected as {username}"

            # Try to detect students (implementation pending - need to see dashboard first)
            # For now, assume single student and set authenticated
            self._authenticated = True
            self._user_display_name = username

            # Try to fetch grades to validate
            success, grades, message = self.get_grades()

            if success and len(grades) > 0:
                return True, f"Connected as {username} ({len(grades)} grades found)"
            elif success and len(grades) == 0:
                return True, f"Connected as {username} (No grades found - check school year/term)"
            else:
                # Login worked but can't fetch grades yet
                return True, f"Connected as {username} (Grade fetching not yet implemented)"

        except requests.exceptions.Timeout:
            return False, "Connection timeout - check your internet connection"
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_grades(self) -> Tuple[bool, List[Dict], str]:
        """
        Fetch grades from Axios Registro Famiglie.

        Returns:
            Tuple of (success: bool, grades: List[Dict], message: str)
            Grades are in VoteTracker format after conversion
        """
        if not self._session or not self._authenticated:
            return False, [], "Not authenticated - please log in first"

        # TODO: Implement grade fetching once we understand the dashboard structure
        # For now, return empty to allow testing login
        return True, [], "Grade fetching not yet implemented - coming soon"

    def logout(self):
        """Clear authentication state."""
        super().logout()
        self._credentials = {}
        self._selected_student_id = None
        self._available_students = []
        if self._session:
            self._session.close()
        self._session = None
