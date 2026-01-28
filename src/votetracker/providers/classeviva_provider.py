"""
ClasseViva Sync Provider Implementation

Wraps the ClasseVivaClient as a SyncProvider for use with the provider
abstraction system.
"""

from typing import List, Dict, Tuple
from ..sync_provider import SyncProvider
from ..classeviva import ClasseVivaClient, convert_classeviva_to_votetracker


class ClasseVivaProvider(SyncProvider):
    """ClasseViva implementation as a sync provider."""

    def __init__(self, database):
        super().__init__(database)
        self._client = None

    def get_provider_name(self) -> str:
        """Get human-readable provider name."""
        return "ClasseViva"

    def get_credential_fields(self) -> List[Dict[str, str]]:
        """
        Get credential field definitions for ClasseViva.

        Returns:
            List of field definitions for username and password
        """
        return [
            {
                'name': 'username',
                'label': 'Username',
                'type': 'text',
                'placeholder': 'S1234567'
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
        Authenticate with ClasseViva.

        Args:
            credentials: Dict with 'username' and 'password' keys

        Returns:
            Tuple of (success: bool, message: str)
        """
        username = credentials.get('username', '')
        password = credentials.get('password', '')

        if not username or not password:
            return False, "Username and password are required"

        # Create new client
        self._client = ClasseVivaClient(username, password)

        # Attempt login
        success, message = self._client.login()

        if success:
            self._authenticated = True
            self._user_display_name = self._client.get_user_display_name()

        return success, message

    def get_grades(self) -> Tuple[bool, List[Dict], str]:
        """
        Fetch grades from ClasseViva.

        Returns:
            Tuple of (success: bool, grades: List[Dict], message: str)
            Grades are in VoteTracker format after conversion
        """
        if not self.is_authenticated() or not self._client:
            return False, [], "Not authenticated - please log in first"

        # Fetch raw ClasseViva grades
        success, raw_grades, message = self._client.get_grades()

        if not success:
            # If session expired, clear auth state
            if "expired" in message.lower():
                self._authenticated = False
            return False, [], message

        # Convert to VoteTracker format
        votetracker_grades = convert_classeviva_to_votetracker(raw_grades)

        return True, votetracker_grades, f"Fetched {len(votetracker_grades)} grades"

    def logout(self):
        """Clear authentication state."""
        super().logout()
        if self._client:
            self._client.logout()
            self._client = None

    def get_mapping_prefix(self) -> str:
        """
        Get database key prefix for subject mappings.

        For backward compatibility with existing ClasseViva installations,
        we use 'cv' as the prefix (matching the old 'cv_mapping_' keys).
        """
        return "cv"
