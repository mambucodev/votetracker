import re

with open("tests/test_sync_provider.py", "r") as f:
    content = f.read()

test_to_insert = """
    def test_register_invalid_provider(self):
        \"\"\"Test registering a class that does not inherit from SyncProvider.\"\"\"
        class InvalidProvider:
            pass

        with self.assertRaises(ValueError):
            SyncProviderRegistry.register("invalid", InvalidProvider)
"""

content = content.replace("    def test_get_provider_unregistered(self):", test_to_insert + "\n    def test_get_provider_unregistered(self):")

with open("tests/test_sync_provider.py", "w") as f:
    f.write(content)
