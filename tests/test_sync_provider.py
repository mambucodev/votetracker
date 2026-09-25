import unittest
from src.votetracker.sync_provider import SyncProvider, SyncProviderRegistry

class DummySyncProvider(SyncProvider):
    def get_provider_name(self) -> str:
        return "Dummy Provider"

    def get_credential_fields(self) -> list[dict[str, str]]:
        return []

    def login(self, credentials: dict[str, str]) -> tuple[bool, str]:
        return True, "Success"

    def get_grades(self) -> tuple[bool, list[dict], str]:
        return True, [], "Success"

class TestSyncProvider(unittest.TestCase):
    def setUp(self):
        self.provider = DummySyncProvider(database=None)

    def test_initial_state(self):
        """Test the initial state of a SyncProvider."""
        self.assertFalse(self.provider.is_authenticated())
        self.assertIsNone(self.provider.get_user_display_name())
        self.assertEqual(self.provider._db, None)

    def test_logout(self):
        """Test logout clears authentication state."""
        self.provider._authenticated = True
        self.provider._user_display_name = "Test User"

        self.provider.logout()

        self.assertFalse(self.provider.is_authenticated())
        self.assertIsNone(self.provider.get_user_display_name())

    def test_get_mapping_prefix(self):
        """Test default get_mapping_prefix behavior."""
        self.assertEqual(self.provider.get_mapping_prefix(), "dummyprovider")

class TestSyncProviderRegistry(unittest.TestCase):
    def setUp(self):
        # Clear registry before each test to avoid interference
        SyncProviderRegistry._providers.clear()
        SyncProviderRegistry._instances.clear()

    def tearDown(self):
        # Clean up after each test
        SyncProviderRegistry.clear_instances()
        SyncProviderRegistry._providers.clear()

    def test_register_valid_provider(self):
        """Test registering a valid subclass of SyncProvider."""
        SyncProviderRegistry.register("dummy", DummySyncProvider)
        self.assertIn("dummy", SyncProviderRegistry._providers)
        self.assertEqual(SyncProviderRegistry._providers["dummy"], DummySyncProvider)



    def test_register_invalid_provider(self):
        """Test registering a class that does not inherit from SyncProvider."""
        class InvalidProvider:
            pass

        with self.assertRaises(ValueError):
            SyncProviderRegistry.register("invalid", InvalidProvider)

    def test_get_provider_unregistered(self):
        """Test getting a provider that hasn't been registered."""
        provider = SyncProviderRegistry.get_provider("nonexistent", None)
        self.assertIsNone(provider)

    def test_get_provider_instantiation(self):
        """Test getting a registered provider instantiates and caches it."""
        SyncProviderRegistry.register("dummy", DummySyncProvider)

        # First call should instantiate
        provider1 = SyncProviderRegistry.get_provider("dummy", None)
        self.assertIsInstance(provider1, DummySyncProvider)

        # Second call should return cached instance
        provider2 = SyncProviderRegistry.get_provider("dummy", None)
        self.assertIs(provider1, provider2)

    def test_get_available_providers(self):
        """Test getting a list of available providers."""
        SyncProviderRegistry.register("dummy", DummySyncProvider)
        available = SyncProviderRegistry.get_available_providers()

        self.assertEqual(len(available), 1)
        self.assertEqual(available[0], ("dummy", "Dummy Provider"))

    def test_clear_instances(self):
        """Test clear_instances calls logout and clears cache."""
        SyncProviderRegistry.register("dummy", DummySyncProvider)
        provider = SyncProviderRegistry.get_provider("dummy", None)

        # Mock logout to verify it's called
        logout_called = False
        def mock_logout():
            nonlocal logout_called
            logout_called = True

        provider.logout = mock_logout

        SyncProviderRegistry.clear_instances()

        self.assertTrue(logout_called)
        self.assertEqual(len(SyncProviderRegistry._instances), 0)

if __name__ == "__main__":
    unittest.main()
