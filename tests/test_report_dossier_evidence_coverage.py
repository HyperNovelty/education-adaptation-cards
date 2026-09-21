#!/usr/bin/env python3
"""Regression tests for deterministic dossier evidence-coverage reporting."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "report_dossier_evidence_coverage.py"
PUBLIC_DOMAIN_FIXTURE = ROOT / "examples" / "education_cards.public_domain_folder_dossier.json"
MINIMAL_FIXTURE = ROOT / "examples" / "education_cards.minimal.json"
PUBLIC_DOMAIN_REPORT = ROOT / "examples" / "rendered" / "public_domain_dossier_evidence_coverage.json"


def run_report(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class DossierEvidenceCoverageReportTests(unittest.TestCase):
    def test_json_output_is_deterministic_and_check_passes(self) -> None:
        first = run_report("--input", str(PUBLIC_DOMAIN_FIXTURE), "--format", "json")
        second = run_report("--input", str(PUBLIC_DOMAIN_FIXTURE), "--format", "json")

        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(PUBLIC_DOMAIN_REPORT.read_text(encoding="utf-8"), first.stdout)

        checked = run_report("--input", str(PUBLIC_DOMAIN_FIXTURE), "--check", str(PUBLIC_DOMAIN_REPORT))
        self.assertEqual(0, checked.returncode, checked.stderr)
        self.assertIn("dossier_evidence_coverage_check=ok", checked.stdout)

    def test_valid_public_domain_fixture_inventories_expected_links(self) -> None:
        result = run_report("--input", str(PUBLIC_DOMAIN_FIXTURE), "--format", "json")
        report = json.loads(result.stdout)

        self.assertEqual("1.0", report["report_version"])
        self.assertEqual("alice_public_domain_folder_dossier", report["packet_id"])
        self.assertEqual("alice_source_check_folder", report["dossier_id"])
        self.assertEqual(["PD001"], report["declared_source_ids"])
        self.assertEqual(
            ["question_observable_setting", "question_claim_boundary"],
            [item["question_id"] for item in report["question_sources"]],
        )
        self.assertEqual("task_claim_evidence_table", report["practice_task"]["task_id"])
        self.assertEqual(
            ["evidence_source_id_present", "evidence_boundary_label_present"],
            report["practice_task"]["evidence_output_ids"],
        )
        self.assertEqual("needs_human_review", report["review_gate"]["status"])
        self.assertEqual(["teacher", "curriculum_reviewer"], report["review_gate"]["required_roles"])
        self.assertEqual(
            "Structural coverage does not mean approval, grading, classroom readiness, or deployment permission.",
            report["boundary_statement"],
        )
        self.assertEqual(
            {
                "missing_source_references": [],
                "unknown_source_references": [],
                "missing_evidence_references": [],
                "unknown_evidence_references": [],
                "unreferenced_declared_source_ids": [],
                "uncovered_evidence_checklist_ids": [],
            },
            report["coverage"],
        )

    def test_missing_dossier_fails_as_incomplete_without_validation_failure(self) -> None:
        result = run_report("--input", str(MINIMAL_FIXTURE), "--format", "json")

        self.assertNotEqual(0, result.returncode)
        report = json.loads(result.stdout)
        self.assertTrue(report["coverage"]["missing_learning_dossier"])
        self.assertIn("dossier_evidence_coverage_report=incomplete", result.stderr)
        self.assertNotIn("validation_failed", result.stderr)

    def test_malformed_and_non_object_inputs_fail_labeled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            malformed = Path(tmpdir) / "malformed.json"
            malformed.write_text("{not json}\n", encoding="utf-8")
            malformed_result = run_report("--input", str(malformed), "--format", "json")
            self.assertNotEqual(0, malformed_result.returncode)
            self.assertIn("dossier_evidence_coverage_report=failed", malformed_result.stderr)

            non_object = Path(tmpdir) / "array.json"
            non_object.write_text("[]\n", encoding="utf-8")
            non_object_result = run_report("--input", str(non_object), "--format", "json")
            self.assertNotEqual(0, non_object_result.returncode)
            self.assertIn("top-level JSON must be object", non_object_result.stderr)

    def test_invalid_references_fail_validation_and_show_exact_unknowns(self) -> None:
        fixture = json.loads(PUBLIC_DOMAIN_FIXTURE.read_text(encoding="utf-8"))
        dossier = fixture["learning_dossier"]
        dossier["question_map"][0]["source_ids"] = ["PD404"]
        dossier["practice_task"]["evidence_output_ids"] = ["evidence_missing"]

        with tempfile.TemporaryDirectory() as tmpdir:
            invalid = Path(tmpdir) / "invalid_references.json"
            invalid.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
            result = run_report("--input", str(invalid), "--format", "json")

        self.assertNotEqual(0, result.returncode)
        report = json.loads(result.stdout)
        self.assertEqual(
            [{"location": "learning_dossier.question_map[0].source_ids", "id": "PD404"}],
            report["coverage"]["unknown_source_references"],
        )
        self.assertEqual(
            [{"location": "learning_dossier.practice_task.evidence_output_ids", "id": "evidence_missing"}],
            report["coverage"]["unknown_evidence_references"],
        )
        self.assertIn("dossier_evidence_coverage_report=validation_failed", result.stderr)

    def test_stale_check_fails_without_mutating_target(self) -> None:
        checked_in_before = PUBLIC_DOMAIN_REPORT.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmpdir:
            stale_report = Path(tmpdir) / "public_domain_dossier_evidence_coverage.json"
            stale_content = checked_in_before + "\nSTALE\n"
            stale_report.write_text(stale_content, encoding="utf-8")

            result = run_report("--input", str(PUBLIC_DOMAIN_FIXTURE), "--check", str(stale_report))

            self.assertNotEqual(0, result.returncode)
            self.assertIn("dossier_evidence_coverage_check=stale", result.stderr)
            self.assertEqual(stale_content, stale_report.read_text(encoding="utf-8"))

        self.assertEqual(checked_in_before, PUBLIC_DOMAIN_REPORT.read_text(encoding="utf-8"))

    def test_output_and_check_are_mutually_exclusive(self) -> None:
        result = run_report(
            "--input",
            str(PUBLIC_DOMAIN_FIXTURE),
            "--output",
            "/tmp/should-not-be-written-dossier-evidence-coverage.json",
            "--check",
            str(PUBLIC_DOMAIN_REPORT),
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("not allowed with argument", result.stderr)

    def test_report_has_no_private_absolute_path_or_authority_claims(self) -> None:
        report_text = PUBLIC_DOMAIN_REPORT.read_text(encoding="utf-8")

        self.assertNotIn(str(ROOT), report_text)
        self.assertNotIn("approved_for_internal_review", report_text)
        self.assertNotIn("approved for classroom use", report_text.lower())
        self.assertNotIn("classroom-ready", report_text.lower())
        self.assertNotIn("deployable", report_text.lower())
        self.assertNotIn("generated_at", report_text)


if __name__ == "__main__":
    unittest.main()
