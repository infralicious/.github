#!/usr/bin/env python3
"""Tests for App inventory check, no dependency, no network."""
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "check_app_inventory", os.path.join(ROOT, "check-app-inventory.py")
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def entry(slug="infralicious-test", scope="org", selection="all"):
    """Return a good inventory entry, for tests."""
    return {
        "slug": slug,
        "app_id": 123,
        "installation_id": 456,
        "owner_type": "infralicious",
        "source": "manifest",
        "scope": scope,
        "repository_selection": selection,
        "repositories": ["all"] if scope == "org" else ["template"],
        "permissions": {"contents": "read", "metadata": "read"},
        "events": [],
        "purpose": "Test App, for tests only",
    }


def live(slug="infralicious-test", selection="all"):
    """Return a good live installation, for tests."""
    return {
        "app_slug": slug,
        "app_id": 123,
        "id": 456,
        "repository_selection": selection,
        "permissions": {"contents": "read", "metadata": "read"},
        "events": [],
    }


class TestInventory(unittest.TestCase):
    """Check inventory compare, schema, and manifest sync."""

    def test_match_passes(self):
        """Match passes, with no errors."""
        errors, warnings = MODULE.compare_live_to_inventory([live()], [entry()])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_unknown_app_fails(self):
        """Unknown App fails, new App must be codified."""
        errors, _ = MODULE.compare_live_to_inventory([live(), live(slug="new-app")], [entry()])
        self.assertTrue(any("UNKNOWN" in message for message in errors))

    def test_missing_app_fails(self):
        """Missing App fails, uninstall must update inventory."""
        errors, _ = MODULE.compare_live_to_inventory([], [entry()])
        self.assertTrue(any("MISSING" in message for message in errors))

    def test_scope_mismatch_fails(self):
        """Scope mismatch fails, scope must match inventory."""
        errors, _ = MODULE.compare_live_to_inventory([live(selection="selected")], [entry()])
        self.assertTrue(any("repository_selection" in message for message in errors))

    def test_permission_mismatch_fails(self):
        """Permission mismatch fails, permissions must match inventory."""
        bad = live()
        bad["permissions"] = {"contents": "write", "metadata": "read"}
        errors, _ = MODULE.compare_live_to_inventory([bad], [entry()])
        self.assertTrue(any("permissions" in message for message in errors))

    def test_installation_id_mismatch_warns(self):
        """Installation_id mismatch warns, reinstall may explain it."""
        bad = live()
        bad["installation_id"] = 999
        errors, warnings = MODULE.compare_live_to_inventory([bad], [entry()])
        self.assertEqual(errors, [])
        self.assertTrue(any("installation_id" in message for message in warnings))

    def test_schema_duplicate_fails(self):
        """Duplicate slug fails, inventory slugs must be unique."""
        errors = MODULE.validate_inventory([entry(), entry()])
        self.assertTrue(any("duplicate" in message for message in errors))

    def test_schema_repo_scope_needs_one_repo(self):
        """Repo scope needs exactly one repo listed."""
        bad = entry(slug="repo-app", scope="repo", selection="selected")
        bad["repositories"] = ["a", "b"]
        errors = MODULE.validate_inventory([bad])
        self.assertTrue(any("exactly one" in message for message in errors))


if __name__ == "__main__":
    unittest.main()
