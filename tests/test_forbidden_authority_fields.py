#!/usr/bin/env python3
"""Regression tests for forbidden future authority field handling."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from education_adaptation_cards import EXAMPLES, expect_invalid_doc, find_forbidden_future_authority_fields, load_json

REPORT_SCRIPT = ROOT / "scripts" / "report_forbidden_authority_fields.py"
RENDER_SCRIPT = ROOT / "scripts" / "render_learning_dossier.py"
INVENTORY = ROOT / "examples" / "rendered" / "forbidden_authority_fields.json"
INVALID = ROOT / "examples" / "invalid"

FORBIDDEN_FIXTURES = {
    "packet_student_id.json": "student_id",
    "card_lms_export.json": "lms_export",
    "dossier_classroom_deployment.json": "classroom_deployment",
    "assessment_gate_gradebook_write.json": "gradebook_write",
}


def run_report(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def run_renderer(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RENDER_SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class ForbiddenAuthorityFieldTests(unittest.TestCase):
    def test_named_invalid_fixtures_fail_with_specific_field_tokens(self) -> None:
        for fixture_name, field in FORBIDDEN_FIXTURES.items():
            with self.subTest(fixture=fixture_name):
                failure = expect_invalid_doc(INVALID / fixture_name)

                self.assertIn(f"forbidden_future_authority_field={field}", failure)
                self.assertIn("must not", failure)
                self.assertNotIn("unexpected keys", failure)
                self.assertNotIn("keys mismatch", failure)

    def test_valid_fixtures_have_zero_forbidden_field_findings(self) -> None:
        for fixture in EXAMPLES:
            with self.subTest(fixture=fixture.name):
                findings = find_forbidden_future_authority_fields(load_json(fixture), fixture.name)
                self.assertEqual([], findings)

                result = run_report("--input", str(fixture))
                self.assertEqual(0, result.returncode, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual({"forbidden_fields": 0}, report["summary"])

    def test_inventory_check_is_fresh(self) -> None:
        result = run_report("--check", str(INVENTORY))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("forbidden_authority_check=ok", result.stdout)

    def test_check_does_not_mutate_target(self) -> None:
        before = INVENTORY.read_text(encoding="utf-8")

        result = run_report("--check", str(INVENTORY))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, INVENTORY.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            stale_target = Path(tmpdir) / "forbidden_authority_fields.json"
            stale_report = json.loads(before)
            stale_report["fields"] = stale_report["fields"][:-1]
            stale_content = json.dumps(stale_report, indent=2, ensure_ascii=False) + "\n"
            stale_target.write_text(stale_content, encoding="utf-8")

            stale = run_report("--check", str(stale_target))

            self.assertNotEqual(0, stale.returncode)
            self.assertIn("forbidden_authority_check=stale", stale.stderr)
            self.assertEqual(stale_content, stale_target.read_text(encoding="utf-8"))

    def test_renderer_fails_closed_for_forbidden_authority_fixtures_without_writing_output(self) -> None:
        for fixture_name, field in FORBIDDEN_FIXTURES.items():
            with self.subTest(fixture=fixture_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    output = Path(tmpdir) / "rendered.md"
                    result = run_renderer("--input", str(INVALID / fixture_name), "--output", str(output))

                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("render_boundary=failed", result.stderr)
                    self.assertIn(f"forbidden_future_authority_field={field}", result.stderr)
                    self.assertFalse(output.exists())
                    self.assertEqual("", result.stdout)


if __name__ == "__main__":
    unittest.main()
