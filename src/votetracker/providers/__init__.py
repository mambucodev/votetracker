"""
Sync Provider Implementations

This package contains all sync provider implementations (ClasseViva, Axios, etc.)
and handles provider registration with the SyncProviderRegistry.
"""

import subprocess
from ..sync_provider import SyncProviderRegistry


def _is_axios_available() -> bool:
    """
    Check if axios CLI is available in the system.

    Returns:
        True if axios CLI is installed and accessible
    """
    try:
        result = subprocess.run(
            ['axios', '--version'],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


def register_all_providers():
    """
    Register all available sync providers.

    This should be called once during application initialization.
    Providers are only registered if their dependencies are available.
    """
    # Import providers here to avoid circular imports
    from .classeviva_provider import ClasseVivaProvider

    # Always register ClasseViva (uses requests, which is required)
    SyncProviderRegistry.register('classeviva', ClasseVivaProvider)

    # Only register Axios if the CLI is available
    if _is_axios_available():
        from .axios_provider import AxiosProvider
        SyncProviderRegistry.register('axios', AxiosProvider)
