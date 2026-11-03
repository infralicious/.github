#!/usr/bin/env python3
"""Tests for zizmor central counting, no dependency."""
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "zizmor_central", os.path.join(ROOT, "zizmor-central.py")
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TestCountFindings(unittest.TestCase):
    """Check plain and ANSI finding counts."""

    def test_plain_lines_count(self):
        """Plain lines count by level."""
        out = (
            "error[github-app]: dangerous use\n"
            "warning[ref-version-mismatch]: pin mismatch\n"
            "help[artipacked]: use persist-credentials\n"
            "  --> file.yml:1:1\n"
        )
        count, high = MODULE.count_findings(out)
        self.assertEqual(count, 3)
        self.assertEqual(high, 1)

    def test_ansi_lines_count(self):
        """ANSI lines count like plain lines."""
        out = (
            "\x1b[1m\x1b[91merror[github-app]\x1b[0m: dangerous use\n"
            "\x1b[1m\x1b[33mwarning[ref-version-mismatch]\x1b[0m: pin mismatch\n"
        )
        count, high = MODULE.count_findings(out)
        self.assertEqual(count, 2)
        self.assertEqual(high, 1)

    def test_summary_lines_do_not_count(self):
        """Summary lines do not count as findings."""
        out = "12 findings (3 ignored, 8 suppressed): 0 high\n"
        count, high = MODULE.count_findings(out)
        self.assertEqual(count, 0)
        self.assertEqual(high, 0)

    def test_empty_output_counts_zero(self):
        """Empty output counts zero."""
        count, high = MODULE.count_findings("")
        self.assertEqual(count, 0)
        self.assertEqual(high, 0)


if __name__ == "__main__":
    unittest.main()
