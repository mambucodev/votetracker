"""
Sync Provider Implementations

This package contains all sync provider implementations (ClasseViva, Axios, etc.)
and handles provider registration with the SyncProviderRegistry.
"""

from ..sync_provider import SyncProviderRegistry


def _is_axios_available():
    """Check if lxml is installed (required by Axios provider)."""
    try:
        import lxml  # noqa: F401
        return True
    except ImportError:
        return False


def register_all_providers():
    """
    Register all available sync providers.

    This should be called once during application initialization.
    """
    # Import providers here to avoid circular imports
    from .classeviva_provider import ClasseVivaProvider

    # ClasseViva only needs requests (required dependency)
    SyncProviderRegistry.register('classeviva', ClasseVivaProvider)

    # Axios requires lxml (optional dependency)
    if _is_axios_available():
        from .axios_provider import AxiosProvider
        SyncProviderRegistry.register('axios', AxiosProvider)
