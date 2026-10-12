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

from education_adaptation_cards import (
    EXAMPLES,
    FORBIDDEN_FUTURE_AUTHORITY_FIELDS,
    expect_invalid_doc,
    find_forbidden_future_authority_fields,
    load_json,
)

REPORT_SCRIPT = ROOT / "scripts" / "report_forbidden_authority_fields.py"
RENDER_SCRIPT = ROOT / "scripts" / "render_learning_dossier.py"
INVENTORY = ROOT / "examples" / "rendered" / "forbidden_authority_fields.json"
INVALID = ROOT / "examples" / "invalid"

FORBIDDEN_FIXTURES = {
    "assessment_gate_gradebook_write.json": {
        "field": "gradebook_write",
        "location": "assessment_gate_gradebook_write.json.education_adaptation_cards[2].assessment_gates[0].gradebook_write",
    },
    "assessment_gate_proctoring_recording.json": {
        "field": "proctoring_recording",
        "location": (
            "assessment_gate_proctoring_recording.json.education_adaptation_cards[2]."
            "assessment_gates[0].proctoring_recording"
        ),
    },
    "card_behavior_score.json": {
        "field": "behavior_score",
        "location": "card_behavior_score.json.education_adaptation_cards[0].behavior_score",
    },
    "card_biometric_data.json": {
        "field": "biometric_data",
        "location": (
            "card_biometric_data.json.education_adaptation_cards[1]."
            "misconception_evidence[0].biometric_data"
        ),
    },
    "card_emotion_inference.json": {
        "field": "emotion_inference",
        "location": "card_emotion_inference.json.education_adaptation_cards[1].learner_questions[0].emotion_inference",
    },
    "card_lms_export.json": {
        "field": "lms_export",
        "location": "card_lms_export.json.education_adaptation_cards[0].lms_export",
    },
    "dossier_classroom_deployment.json": {
        "field": "classroom_deployment",
        "location": "dossier_classroom_deployment.json.learning_dossier.classroom_deployment",
    },
    "packet_family_contact.json": {
        "field": "family_contact",
        "location": "packet_family_contact.json.review_packet.family_contact",
    },
    "packet_student_id.json": {
        "field": "student_id",
        "location": "packet_student_id.json.review_packet.student_id",
    },
}

SENSITIVE_LEARNER_DATA_FIELDS = {
    "behavior_score": "must not score learner behavior",
    "biometric_data": "must not collect learner biometric data",
    "emotion_inference": "must not infer learner emotions",
    "family_contact": "must not collect family contact data",
    "proctoring_recording": "must not collect proctoring recordings",
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
        for fixture_name, expected in FORBIDDEN_FIXTURES.items():
            with self.subTest(fixture=fixture_name):
                field = expected["field"]
                reason = FORBIDDEN_FUTURE_AUTHORITY_FIELDS[field]
                failure = expect_invalid_doc(INVALID / fixture_name)

                self.assertIn(f"forbidden_future_authority_field={field}", failure)
                self.assertIn(expected["location"], failure)
                self.assertIn(reason, failure)
                self.assertNotIn("unexpected keys", failure)
                self.assertNotIn("keys mismatch", failure)

    def test_sensitive_learner_data_fields_have_exact_public_safe_reasons(self) -> None:
        for field, reason in SENSITIVE_LEARNER_DATA_FIELDS.items():
            with self.subTest(field=field):
                self.assertEqual(reason, FORBIDDEN_FUTURE_AUTHORITY_FIELDS[field])

    def test_sensitive_learner_data_fixtures_report_exact_nested_locations(self) -> None:
        sensitive_fixtures = {
            fixture: expected
            for fixture, expected in FORBIDDEN_FIXTURES.items()
            if expected["field"] in SENSITIVE_LEARNER_DATA_FIELDS
        }
        for fixture_name, expected in sensitive_fixtures.items():
            with self.subTest(fixture=fixture_name):
                findings = find_forbidden_future_authority_fields(load_json(INVALID / fixture_name), fixture_name)

                self.assertEqual(
                    [
                        {
                            "field": expected["field"],
                            "location": expected["location"],
                            "reason": SENSITIVE_LEARNER_DATA_FIELDS[expected["field"]],
                        }
                    ],
                    findings,
                )

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
        for fixture_name, expected in FORBIDDEN_FIXTURES.items():
            with self.subTest(fixture=fixture_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    output = Path(tmpdir) / "rendered.md"
                    result = run_renderer("--input", str(INVALID / fixture_name), "--output", str(output))

                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("render_boundary=failed", result.stderr)
                    self.assertIn(f"forbidden_future_authority_field={expected['field']}", result.stderr)
                    self.assertFalse(output.exists())
                    self.assertEqual("", result.stdout)


if __name__ == "__main__":
    unittest.main()
