"""
Sync Provider Abstraction Layer

This module provides the base abstraction for external grade sync providers
(ClasseViva, Axios, etc.) with a registry pattern for provider management.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional


class SyncProvider(ABC):
    """
    Abstract base class for sync providers.

    All sync providers (ClasseViva, Axios, etc.) must implement this interface
    to provide a consistent integration pattern across the application.
    """

    def __init__(self, database):
        """
        Initialize provider with database access.

        Args:
            database: Database instance for credential/mapping storage
        """
        self._db = database
        self._authenticated = False
        self._user_display_name = None

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get human-readable provider name.

        Returns:
            Provider name (e.g., "ClasseViva", "Axios")
        """
        pass

    @abstractmethod
    def get_credential_fields(self) -> List[Dict[str, str]]:
        """
        Get credential field definitions for this provider.

        Returns:
            List of field dicts with keys:
            - name: Field identifier (e.g., "username")
            - label: Display label (e.g., "Username")
            - type: Input type ("text" or "password")
            - placeholder: Placeholder text

        Example:
            [
                {'name': 'username', 'label': 'Username', 'type': 'text', 'placeholder': 'S1234567'},
                {'name': 'password', 'label': 'Password', 'type': 'password', 'placeholder': ''}
            ]
        """
        pass

    @abstractmethod
    def login(self, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """
        Authenticate with the provider.

        Args:
            credentials: Dict mapping field names to values
                        (e.g., {'username': 'S123', 'password': 'pass123'})

        Returns:
            Tuple of (success: bool, message: str)
            - success: True if authentication succeeded
            - message: Success/error message for user
        """
        pass

    @abstractmethod
    def get_grades(self) -> Tuple[bool, List[Dict], str]:
        """
        Fetch grades from the provider.

        Must be called after successful login().

        Returns:
            Tuple of (success: bool, grades: List[Dict], message: str)
            - success: True if fetch succeeded
            - grades: List of grade dicts in VoteTracker format:
                {
                    'subject': str,
                    'grade': float,
                    'type': str ('Written', 'Oral', 'Practical'),
                    'date': str (ISO format 'YYYY-MM-DD'),
                    'description': str,
                    'term': int (1 or 2),
                    'weight': float (default 1.0)
                }
            - message: Success/error message
        """
        pass

    def is_authenticated(self) -> bool:
        """
        Check if provider is currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self._authenticated

    def logout(self):
        """
        Clear authentication state.
        """
        self._authenticated = False
        self._user_display_name = None

    def get_user_display_name(self) -> Optional[str]:
        """
        Get authenticated user's display name.

        Returns:
            User's full name or None if not authenticated
        """
        return self._user_display_name

    def get_mapping_prefix(self) -> str:
        """
        Get database key prefix for subject mappings.

        Override if provider needs custom prefix (default uses provider_id).

        Returns:
            Prefix string (e.g., "classeviva", "axios")
        """
        # Default: use lowercase provider name with spaces removed
        return self.get_provider_name().lower().replace(" ", "")


class SyncProviderRegistry:
    """
    Registry for managing sync provider instances.

    Providers must be registered before use via register().
    """

    _providers = {}  # provider_id -> provider_class
    _instances = {}  # provider_id -> provider_instance

    @classmethod
    def register(cls, provider_id: str, provider_class: type):
        """
        Register a provider class.

        Args:
            provider_id: Unique provider identifier (e.g., "classeviva", "axios")
            provider_class: Provider class (must inherit from SyncProvider)
        """
        if not issubclass(provider_class, SyncProvider):
            raise ValueError(f"Provider class must inherit from SyncProvider")

        cls._providers[provider_id] = provider_class

    @classmethod
    def get_provider(cls, provider_id: str, database) -> Optional[SyncProvider]:
        """
        Get or create provider instance.

        Args:
            provider_id: Provider identifier
            database: Database instance to pass to provider

        Returns:
            Provider instance or None if not registered
        """
        if provider_id not in cls._providers:
            return None

        # Create instance if not cached
        if provider_id not in cls._instances:
            provider_class = cls._providers[provider_id]
            cls._instances[provider_id] = provider_class(database)

        return cls._instances[provider_id]

    @classmethod
    def get_available_providers(cls) -> List[Tuple[str, str]]:
        """
        Get list of available providers.

        Returns:
            List of (provider_id, provider_name) tuples
        """
        result = []
        for provider_id, provider_class in cls._providers.items():
            # Instantiate temporarily to get name (providers are lightweight)
            temp_instance = provider_class(None)
            result.append((provider_id, temp_instance.get_provider_name()))
        return result

    @classmethod
    def clear_instances(cls):
        """
        Clear all cached provider instances.

        Useful for testing or when switching providers.
        """
        for instance in cls._instances.values():
            instance.logout()
        cls._instances.clear()
