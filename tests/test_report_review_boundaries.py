#!/usr/bin/env python3
"""Regression tests for deterministic review-boundary reporting."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "report_review_boundaries.py"
MINIMAL_FIXTURE = ROOT / "examples" / "education_cards.minimal.json"
REVIEW_PACKET_FIXTURE = ROOT / "examples" / "education_cards.review_packet_fixture.json"
PUBLIC_DOMAIN_FIXTURE = ROOT / "examples" / "education_cards.public_domain_folder_dossier.json"
MINIMAL_REPORT = ROOT / "examples" / "rendered" / "minimal_review_boundaries.json"
REVIEW_PACKET_REPORT = ROOT / "examples" / "rendered" / "review_packet_review_boundaries.json"
PUBLIC_DOMAIN_REPORT = ROOT / "examples" / "rendered" / "public_domain_review_boundaries.json"
INVALID = ROOT / "examples" / "invalid"


def run_report(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class ReviewBoundaryReportTests(unittest.TestCase):
    def test_valid_fixture_inventories_every_layer_in_stable_order(self) -> None:
        result = run_report("--input", str(PUBLIC_DOMAIN_FIXTURE), "--format", "json")
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(
            [
                "review_packet.packet_status",
                "learning_dossier.learning_mission.review_state",
                "learning_dossier.review_gate.status",
                "card:teacher_card_alice_source_folder.human_review.status",
                "card:student_card_alice_source_check.human_review.status",
                "card:assessment_gate_card_alice_folder.human_review.status",
            ],
            [item["label"] for item in report["items"]],
        )
        self.assertEqual({"total": 6, "pass": 6, "violations": 0}, report["summary"])

    def test_json_output_is_deterministic_and_check_passes(self) -> None:
        first = run_report("--input", str(PUBLIC_DOMAIN_FIXTURE), "--format", "json")
        second = run_report("--input", str(PUBLIC_DOMAIN_FIXTURE), "--format", "json")
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(PUBLIC_DOMAIN_REPORT.read_text(encoding="utf-8"), first.stdout)

        checked = run_report("--input", str(PUBLIC_DOMAIN_FIXTURE), "--check", str(PUBLIC_DOMAIN_REPORT))
        self.assertEqual(0, checked.returncode, checked.stderr)
        self.assertIn("review_boundary_check=ok", checked.stdout)

    def test_remaining_valid_fixture_reports_are_deterministic_and_check_passes(self) -> None:
        cases = [
            (REVIEW_PACKET_FIXTURE, REVIEW_PACKET_REPORT),
            (MINIMAL_FIXTURE, MINIMAL_REPORT),
        ]
        for fixture, checked_in_report in cases:
            with self.subTest(fixture=fixture.name):
                first = run_report("--input", str(fixture), "--format", "json")
                second = run_report("--input", str(fixture), "--format", "json")
                self.assertEqual(0, first.returncode, first.stderr)
                self.assertEqual(first.stdout, second.stdout)
                self.assertEqual(checked_in_report.read_text(encoding="utf-8"), first.stdout)

                checked = run_report("--input", str(fixture), "--check", str(checked_in_report))
                self.assertEqual(0, checked.returncode, checked.stderr)
                self.assertIn("review_boundary_check=ok", checked.stdout)

    def assert_boundary_violation(self, fixture: str, label: str, status: str) -> None:
        result = run_report("--input", str(INVALID / fixture), "--format", "json")
        self.assertNotEqual(0, result.returncode)
        report = json.loads(result.stdout)
        violations = [item for item in report["items"] if item["result"] == "violation"]
        self.assertEqual(1, len(violations), report)
        self.assertEqual(label, violations[0]["label"])
        self.assertEqual(status, violations[0]["observed_status"])
        self.assertIn("review_boundary_report=violations count=1", result.stderr)

    def test_packet_dossier_gate_and_card_approval_states_fail_closed(self) -> None:
        self.assert_boundary_violation(
            "packet_status_approved_internal_review.json",
            "review_packet.packet_status",
            "approved_for_internal_review",
        )
        self.assert_boundary_violation(
            "dossier_learning_mission_review_state_approved.json",
            "learning_dossier.learning_mission.review_state",
            "approved_for_internal_review",
        )
        self.assert_boundary_violation(
            "dossier_review_gate_status_approved.json",
            "learning_dossier.review_gate.status",
            "approved_for_internal_review",
        )
        self.assert_boundary_violation(
            "human_review_status_approved_card.json",
            "card:teacher_card_invalid_approved_status.human_review.status",
            "approved_for_internal_review",
        )

    def test_malformed_input_and_stale_check_fail_without_mutating_report(self) -> None:
        checked_in_before = PUBLIC_DOMAIN_REPORT.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmpdir:
            malformed = Path(tmpdir) / "malformed.json"
            malformed.write_text("{not json}\n", encoding="utf-8")
            malformed_result = run_report("--input", str(malformed), "--format", "json")
            self.assertNotEqual(0, malformed_result.returncode)
            self.assertIn("review_boundary_report=failed", malformed_result.stderr)

            stale_report = Path(tmpdir) / "public_domain_review_boundaries.json"
            stale_content = checked_in_before + "\nSTALE\n"
            stale_report.write_text(stale_content, encoding="utf-8")
            stale_result = run_report("--input", str(PUBLIC_DOMAIN_FIXTURE), "--check", str(stale_report))
            self.assertNotEqual(0, stale_result.returncode)
            self.assertIn("review_boundary_check=stale", stale_result.stderr)
            self.assertEqual(stale_content, stale_report.read_text(encoding="utf-8"))

        self.assertEqual(checked_in_before, PUBLIC_DOMAIN_REPORT.read_text(encoding="utf-8"))

    def test_output_and_check_are_mutually_exclusive(self) -> None:
        result = run_report(
            "--input",
            str(PUBLIC_DOMAIN_FIXTURE),
            "--output",
            "/tmp/should-not-be-written-review-boundaries.json",
            "--check",
            str(PUBLIC_DOMAIN_REPORT),
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("not allowed with argument", result.stderr)


if __name__ == "__main__":
    unittest.main()
