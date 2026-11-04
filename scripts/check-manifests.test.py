#!/usr/bin/env python3
"""Tests for manifest linter, no dependency."""
import importlib.util
import json
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "check_manifests", os.path.join(ROOT, "check-manifests.py")
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def good_manifest():
    """Return a good manifest, for tests."""
    return {
        "name": "infralicious-test",
        "url": "https://github.com/infralicious/.github",
        "description": "Test App, for lint tests only",
        "public": False,
        "redirect_url": "https://github.com/infralicious/.github",
        "default_permissions": {"contents": "read", "metadata": "read"},
        "default_events": [],
    }


def lint_dict(data, filename="infralicious-test.json"):
    """Lint a manifest dict, in a temp directory."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, filename)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        return MODULE.lint_manifest(path)


def codes(issues, level="ERROR"):
    """Return codes for one level, from lint issues."""
    return [code for issue_level, code, _ in issues if issue_level == level]


class TestLintManifest(unittest.TestCase):
    """Check linter rules, good and bad manifests."""

    def test_good_manifest_has_no_errors(self):
        """Good manifest has no errors."""
        issues = lint_dict(good_manifest())
        self.assertEqual(codes(issues), [])

    def test_public_true_fails(self):
        """Public true fails, Apps must be private."""
        data = good_manifest()
        data["public"] = True
        self.assertIn("E06", codes(lint_dict(data)))

    def test_redirect_mismatch_fails(self):
        """Redirect mismatch fails, redirect must equal url."""
        data = good_manifest()
        data["redirect_url"] = "https://example.com/"
        self.assertIn("E05", codes(lint_dict(data)))

    def test_hook_without_url_fails(self):
        """Hook without url fails, GitHub rejects it."""
        data = good_manifest()
        data["hook_attributes"] = {"active": False}
        self.assertIn("E11", codes(lint_dict(data)))

    def test_unknown_permission_fails(self):
        """Unknown permission fails, linter allowlist guards it."""
        data = good_manifest()
        data["default_permissions"] = {"contents": "read", "bogus_perm": "read"}
        self.assertIn("E08", codes(lint_dict(data)))

    def test_bad_permission_value_fails(self):
        """Bad permission value fails, value must be read or write."""
        data = good_manifest()
        data["default_permissions"] = {"contents": "admin"}
        self.assertIn("E09", codes(lint_dict(data)))

    def test_write_permission_warns(self):
        """Write permission warns, but does not fail."""
        data = good_manifest()
        data["default_permissions"] = {"contents": "write", "metadata": "read"}
        issues = lint_dict(data)
        self.assertEqual(codes(issues), [])
        self.assertIn("W01", codes(issues, level="WARN"))

    def test_file_name_mismatch_fails(self):
        """File name mismatch fails, file name must match App name."""
        issues = lint_dict(good_manifest(), filename="infralicious-other.json")
        self.assertIn("E15", codes(issues))

    def test_inventory_file_is_skipped(self):
        """Inventory file is skipped, inventory is not a manifest."""
        with tempfile.TemporaryDirectory() as tmp:
            good_path = os.path.join(tmp, "infralicious-test.json")
            with open(good_path, "w", encoding="utf-8") as handle:
                json.dump(good_manifest(), handle)
            inv_path = os.path.join(tmp, "inventory.json")
            with open(inv_path, "w", encoding="utf-8") as handle:
                json.dump({"org": "infralicious", "apps": []}, handle)
            result = MODULE.main(["--apps-dir", tmp])
            self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
