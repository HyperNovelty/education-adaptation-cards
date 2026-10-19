#!/usr/bin/env python3
"""Regression tests for deterministic learner-inquiry status reporting."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from education_adaptation_cards import load_json

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "report_learner_inquiry_status.py"
FIXTURES = [ROOT / name for name in (
    "examples/education_cards.minimal.json",
    "examples/education_cards.review_packet_fixture.json",
    "examples/education_cards.public_domain_folder_dossier.json",
)]
REPORTS = [ROOT / name for name in (
    "examples/rendered/minimal_learner_inquiry_status.json",
    "examples/rendered/review_packet_learner_inquiry_status.json",
    "examples/rendered/public_domain_learner_inquiry_status.json",
)]


def run_report(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=ROOT, check=False)


class LearnerInquiryStatusReportTests(unittest.TestCase):
    def test_valid_reports_have_exact_stable_structure_order_and_counts(self) -> None:
        expected = [
            (["student_card_minimal"], ["question_source_confidence"], ["misconception_draft_as_fact"], 1, 1, 1),
            (["student_card_guided_source_check"], ["question_claim_support", "question_candidate_source"], ["misconception_candidate_as_approved", "misconception_generated_authority"], 2, 2, 2),
            (["student_card_alice_source_check"], ["question_alice_supported_claim"], ["misconception_inference_as_fact"], 1, 1, 0),
        ]
        for fixture, checked, values in zip(FIXTURES, REPORTS, expected):
            result = run_report("--input", str(fixture), "--format", "json")
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            card_ids, question_ids, misconception_ids, question_count, misconception_count, attention_count = values
            self.assertEqual("education_adaptation_cards.learner_inquiry_status", report["report_type"])
            self.assertEqual("1.0", report["report_version"])
            self.assertEqual(fixture.relative_to(ROOT).as_posix(), report["source_path"])
            self.assertEqual(
                [
                    "teacher_card_minimal", "student_card_minimal", "assessment_gate_card_minimal"
                ] if fixture.name == "education_cards.minimal.json" else (
                    ["teacher_card_source_locked_lesson", "student_card_guided_source_check", "assessment_gate_card_review_packet_release"]
                    if fixture.name == "education_cards.review_packet_fixture.json" else
                    ["teacher_card_alice_source_folder", "student_card_alice_source_check", "assessment_gate_card_alice_folder"]
                ),
                [card["card_id"] for card in report["cards"]],
            )
            self.assertEqual(card_ids, [card["card_id"] for card in report["cards"] if card["learner_questions"]])
            self.assertEqual(question_ids, [item["question_id"] for card in report["cards"] for item in card["learner_questions"]])
            self.assertEqual(misconception_ids, [item["misconception_id"] for card in report["cards"] for item in card["misconception_evidence"]])
            self.assertEqual(question_count, report["counts"]["learner_questions"])
            self.assertEqual(misconception_count, report["counts"]["misconception_evidence"])
            self.assertEqual(attention_count, report["counts"]["attention_items"])
            self.assertIn("human inspection", report["boundary_statement"])
            self.assertIn("not scores", report["boundary_statement"])
            self.assertEqual(checked.read_text(encoding="utf-8"), result.stdout)

    def test_all_three_freshness_checks_pass_and_output_is_deterministic(self) -> None:
        for fixture, checked in zip(FIXTURES, REPORTS):
            first = run_report("--input", str(fixture), "--format", "json")
            second = run_report("--input", str(fixture), "--format", "json")
            self.assertEqual(first.stdout, second.stdout)
            checked_result = run_report("--input", str(fixture), "--check", str(checked))
            self.assertEqual(0, checked_result.returncode, checked_result.stderr)
            self.assertIn("learner_inquiry_status_check=ok", checked_result.stdout)

    def test_attention_semantics_cover_status_source_and_severity(self) -> None:
        doc = copy.deepcopy(load_json(FIXTURES[2]))
        question = doc["education_adaptation_cards"][1]["learner_questions"][0]
        question["question_status"], question["source_ids"] = "unanswered", []
        doc["education_adaptation_cards"][1]["misconception_evidence"][0]["severity"] = "unknown"
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "synthetic.json"
            fixture.write_text(json.dumps(doc), encoding="utf-8")
            result = run_report("--input", str(fixture), "--format", "json")
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(["unanswered", "empty_source_ids_without_source_binding", "unknown"], [item["reason"] for item in report["attention_items"]])
        self.assertEqual(3, report["counts"]["attention_items"])

    def test_out_of_scope_is_attention_only_and_paths_are_relative(self) -> None:
        doc = copy.deepcopy(load_json(FIXTURES[2]))
        question = doc["education_adaptation_cards"][1]["learner_questions"][0]
        question["question_status"], question["source_ids"] = "out_of_scope", []
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "synthetic.json"
            fixture.write_text(json.dumps(doc), encoding="utf-8")
            result = run_report("--input", str(fixture), "--format", "json")
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(["out_of_scope", "empty_source_ids_without_source_binding"], [item["reason"] for item in report["attention_items"]])
        self.assertNotIn(str(ROOT), report["source_path"])

    def test_malformed_invalid_and_stale_inputs_do_not_mutate_check_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target.json"
            original = "unchanged\n"
            target.write_text(original, encoding="utf-8")
            malformed = Path(tmpdir) / "malformed.json"
            malformed.write_text("{not json}\n", encoding="utf-8")
            invalid = Path(tmpdir) / "invalid.json"
            invalid.write_text("[]\n", encoding="utf-8")
            for fixture in (malformed, invalid):
                result = run_report("--input", str(fixture), "--check", str(target))
                self.assertNotEqual(0, result.returncode)
                self.assertIn("learner_inquiry_status_report=failed", result.stderr)
                self.assertEqual(original, target.read_text(encoding="utf-8"))
            validator_invalid = Path(tmpdir) / "validator_invalid.json"
            validator_invalid_doc = copy.deepcopy(load_json(FIXTURES[2]))
            validator_invalid_doc["safety_mode"] = "unsafe_mode"
            validator_invalid.write_text(json.dumps(validator_invalid_doc), encoding="utf-8")
            result = run_report("--input", str(validator_invalid), "--check", str(target))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("learner_inquiry_status_report=failed", result.stderr)
            self.assertIn("validation_error=", result.stderr)
            self.assertEqual(original, target.read_text(encoding="utf-8"))
            stale = run_report("--input", str(FIXTURES[2]), "--check", str(target))
            self.assertNotEqual(0, stale.returncode)
            self.assertIn("learner_inquiry_status_check=stale", stale.stderr)
            self.assertEqual(original, target.read_text(encoding="utf-8"))

    def test_output_and_check_are_mutually_exclusive(self) -> None:
        result = run_report("--input", str(FIXTURES[0]), "--output", "/tmp/inquiry.json", "--check", str(REPORTS[0]))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("not allowed with argument", result.stderr)


if __name__ == "__main__":
    unittest.main()
