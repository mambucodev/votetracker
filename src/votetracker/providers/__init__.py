"""
Sync Provider Implementations

This package contains all sync provider implementations (ClasseViva, Axios, etc.)
and handles provider registration with the SyncProviderRegistry.
"""

from ..sync_provider import SyncProviderRegistry


def register_all_providers():
    """
    Register all available sync providers.

    This should be called once during application initialization.
    """
    # Import providers here to avoid circular imports
    from .classeviva_provider import ClasseVivaProvider
    from .axios_provider import AxiosProvider

    # Register all providers (both use requests, which is required)
    SyncProviderRegistry.register('classeviva', ClasseVivaProvider)
    SyncProviderRegistry.register('axios', AxiosProvider)
