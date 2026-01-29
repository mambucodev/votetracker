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
        self._auth_token = None
        self._dashboard_url = None

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

            # Extract authentication token
            token_match = re.search(r"id='_AXToken'\s+value='([^']+)'", resp.text)
            if token_match:
                self._auth_token = token_match.group(1)
            else:
                return False, "Login succeeded but couldn't extract authentication token"

            # Save the dashboard URL for Referer header in AJAX requests
            self._dashboard_url = resp.url

            # If student_id already provided, use it
            if student_id:
                self._selected_student_id = student_id
                self._authenticated = True
                self._user_display_name = username
                return True, f"Connected as {username}"

            # Set authenticated
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

        if not self._auth_token:
            return False, [], "No authentication token available"

        try:
            ajax_url = "https://registrofamiglie.axioscloud.it/Pages/APP/APP_Ajax_Get.aspx"

            # Add RVT header (auth token) and Referer
            headers = {
                'RVT': self._auth_token,
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
            }

            # Add Referer header if we have the dashboard URL
            if self._dashboard_url:
                headers['Referer'] = self._dashboard_url

            # Add cache-busting timestamp
            import time

            # Step 0: Load dashboard first (browser does this before FAMILY_VOTI)
            timestamp = int(time.time() * 1000)
            resp_dash = self._session.get(f"{ajax_url}?Action=DashboardLoad&_={timestamp}", headers=headers, timeout=10)

            if resp_dash.status_code != 200:
                return False, [], f"Failed to load dashboard (HTTP {resp_dash.status_code})"

            # Step 1: Load the grades page (uppercase Action parameter)
            timestamp = int(time.time() * 1000)
            resp = self._session.get(f"{ajax_url}?Action=FAMILY_VOTI&_={timestamp}", headers=headers, timeout=10)

            if resp.status_code != 200:
                return False, [], f"Failed to load grades page (HTTP {resp.status_code}): {resp.text[:200]}"

            # Parse JSON response
            try:
                voti_data = resp.json()
                errorcode = voti_data.get('errorcode', '-1')

                # errorcode "0" means success
                if errorcode != "0":
                    errormsg = voti_data.get('errormsg', 'Unknown error')
                    return False, [], f"Error loading grades page: {errormsg}"

                # Extract ALL frazione values from the dropdown (for all terms)
                html_content = voti_data.get('html', '')

                # Find the frazione dropdown specifically (id='fiFrazId')
                # Extract only options from this dropdown, not the subject filter dropdown
                frazione_select_match = re.search(r"<select[^>]+id=['\"]fiFrazId['\"][^>]*>(.*?)</select>", html_content, re.DOTALL)

                if not frazione_select_match:
                    return False, [], "No frazione/term dropdown found in response"

                frazione_select_html = frazione_select_match.group(1)

                # Now extract options only from this dropdown
                frazione_options = re.findall(r'<option\s+value\s*=\s*[\'"]([^\'\"]+)[\'"].*?>([^<]+)</option>', frazione_select_html)

                if not frazione_options:
                    return False, [], "No term options found in frazione dropdown"

            except Exception as e:
                return False, [], f"Failed to parse grades page response: {str(e)}"

            # Step 2: Fetch grades (just once - server returns all grades regardless of term selection)
            # We'll determine which term each grade belongs to based on date

            # Parse term date ranges from the options
            term_ranges = []
            for frazione_value, frazione_label in frazione_options:
                # Extract dates from label: "TRIMESTRE (15/09/2025 - 15/12/2025)"
                date_match = re.search(r'\((\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})\)', frazione_label)
                if date_match:
                    start_str, end_str = date_match.groups()
                    # Convert DD/MM/YYYY to YYYY-MM-DD
                    start_parts = start_str.split('/')
                    end_parts = end_str.split('/')
                    start_date = f"{start_parts[2]}-{start_parts[1]}-{start_parts[0]}"
                    end_date = f"{end_parts[2]}-{end_parts[1]}-{end_parts[0]}"

                    # Determine term number
                    term_num = 1 if 'TRIMESTRE' in frazione_label.upper() and 'PENTA' not in frazione_label.upper() else 2

                    term_ranges.append({
                        'term': term_num,
                        'start': start_date,
                        'end': end_date,
                        'label': frazione_label
                    })

            print(f"DEBUG: Parsed term ranges: {term_ranges}")

            # Extract hidden frazione value for POST request
            frazione_match = re.search(r'id=[\'"]frazione[\'"].*?value=[\'"]([^\'\"]+)[\'"]', html_content)
            frazione = frazione_match.group(1) if frazione_match else ""

            if not frazione:
                return False, [], "Could not extract frazione value from grades page"

            # Fetch grades once (using the hidden frazione from the already-loaded page)
            post_data = {
                "draw": 1,
                "columns": {},
                "order": [],
                "start": 0,
                "length": 1000,
                "search": {"value": "", "regex": False},
                "iMatId": "",
                "frazione": frazione
            }

            post_headers = headers.copy()
            post_headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
            post_headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

            resp = self._session.post(
                f"{ajax_url}?Action=FAMILY_VOTI_ELENCO_LISTA",
                headers=post_headers,
                data=json.dumps(post_data),
                timeout=10
            )

            if resp.status_code != 200:
                return False, [], f"Failed to fetch grades list (HTTP {resp.status_code}): {resp.text[:200]}"

            grades_data = resp.json()
            raw_grades = grades_data.get('data', [])

            if not raw_grades:
                return True, [], "No grades found"

            # Convert grades and assign term based on date
            all_grades = self._convert_axios_grades(raw_grades)

            for grade in all_grades:
                grade_date = grade['date']  # YYYY-MM-DD format

                # Find which term this grade belongs to based on date
                assigned_term = 2  # Default to term 2 if not found
                for term_range in term_ranges:
                    if term_range['start'] <= grade_date <= term_range['end']:
                        assigned_term = term_range['term']
                        break

                grade['term'] = assigned_term

            print(f"DEBUG: Total grades fetched: {len(all_grades)}")
            return True, all_grades, f"Successfully fetched {len(all_grades)} grades"

        except requests.exceptions.Timeout:
            return False, [], "Request timeout"
        except requests.exceptions.RequestException as e:
            return False, [], f"Network error: {str(e)}"
        except Exception as e:
            return False, [], f"Error: {str(e)}"

    def _convert_axios_grades(self, raw_grades: List[Dict]) -> List[Dict]:
        """
        Convert Axios grades to VoteTracker format.

        Args:
            raw_grades: List of grades from Axios API

        Returns:
            List of grades in VoteTracker format
        """
        vt_grades = []

        for grade in raw_grades:
            try:
                # Extract date (DD/MM/YYYY -> YYYY-MM-DD)
                date_str = grade.get('giorno', '')
                if date_str:
                    day, month, year = date_str.split('/')
                    date = f"{year}-{month}-{day}"
                else:
                    continue  # Skip if no date

                # Extract subject
                subject = grade.get('materia', '').strip()
                if not subject:
                    continue  # Skip if no subject

                # Extract grade value from HTML
                voto_html = grade.get('voto', '')
                # Extract from title attribute: "Voto: 7+ ... Valore: 7,25"
                valore_match = re.search(r'Valore:\s*([\d,\.]+)', voto_html)
                if valore_match:
                    # Use the numeric value (e.g., 7,25)
                    grade_value = valore_match.group(1).replace(',', '.')
                else:
                    # Fallback: extract from span content (e.g., "7+", "8.48")
                    grade_match = re.search(r'>([^<]+)<', voto_html)
                    if grade_match:
                        grade_value = grade_match.group(1).strip()
                        # Convert "7+" to 7.25, "7-" to 6.75, etc.
                        if '+' in grade_value:
                            grade_value = str(float(grade_value.replace('+', '')) + 0.25)
                        elif '-' in grade_value:
                            grade_value = str(float(grade_value.replace('-', '')) - 0.25)
                        elif '½' in grade_value or '1/2' in grade_value:
                            grade_value = str(float(grade_value.replace('½', '').replace('1/2', '')) + 0.5)
                    else:
                        continue  # Skip if can't extract grade

                # Convert to float
                try:
                    grade_float = float(grade_value)
                except ValueError:
                    continue  # Skip if not a valid number

                # Map type (Orale, Scritto, Pratico)
                tipo = grade.get('tipo', '').lower()
                if 'oral' in tipo or 'oral' in tipo:
                    vote_type = 'Oral'
                elif 'scritt' in tipo or 'written' in tipo:
                    vote_type = 'Written'
                elif 'pratic' in tipo or 'practical' in tipo:
                    vote_type = 'Practical'
                else:
                    vote_type = 'Oral'  # Default to Oral

                # Extract description (remove HTML entities)
                description = grade.get('commento', '').strip()
                description = description.replace('&amp;', '&')
                description = description.replace('&#224;', 'à')
                description = description.replace('&#232;', 'è')
                description = description.replace('&#233;', 'é')
                description = description.replace('&#39;', "'")
                description = description.replace('&lt;', '<')
                description = description.replace('&gt;', '>')
                description = description.replace('\r\n', ' ')
                description = description.replace('\n', ' ')
                # Limit length
                if len(description) > 500:
                    description = description[:497] + "..."

                # Create VoteTracker grade
                vt_grade = {
                    'subject': subject,
                    'grade': grade_float,
                    'type': vote_type,
                    'date': date,
                    'description': description,
                    'weight': 1.0  # Default weight
                }

                vt_grades.append(vt_grade)

            except Exception as e:
                # Skip grades that can't be converted
                continue

        return vt_grades

    def logout(self):
        """Clear authentication state."""
        super().logout()
        self._credentials = {}
        self._selected_student_id = None
        self._available_students = []
        if self._session:
            self._session.close()
        self._session = None
