#!/usr/bin/env python3
"""Renderer fail-closed regressions for review-boundary inputs."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_learning_dossier.py"
PUBLIC_DOMAIN_FIXTURE = ROOT / "examples" / "education_cards.public_domain_folder_dossier.json"
PUBLIC_DOMAIN_RENDER = ROOT / "examples" / "rendered" / "public_domain_learning_dossier.md"
INVALID = ROOT / "examples" / "invalid"


def run_renderer(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class RenderReviewBoundaryRegressionTests(unittest.TestCase):
    def assert_promoted_fixture_fails(
        self,
        fixture_name: str,
        expected_layer: str,
        expected_status: str,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "rendered.md"
            result = run_renderer("--input", str(INVALID / fixture_name), "--output", str(output))

            self.assertNotEqual(0, result.returncode)
            self.assertIn("render_boundary=failed", result.stderr)
            self.assertIn("reason=review_boundary_violation", result.stderr)
            self.assertIn(f"layer={expected_layer}", result.stderr)
            self.assertIn(f"status='{expected_status}'", result.stderr)
            self.assertFalse(output.exists())
            self.assertEqual("", result.stdout)

    def test_promoted_packet_dossier_gate_and_card_states_fail_labeled(self) -> None:
        cases = [
            (
                "packet_status_approved_internal_review.json",
                "review_packet.packet_status",
                "approved_for_internal_review",
            ),
            (
                "dossier_learning_mission_review_state_approved.json",
                "learning_dossier.learning_mission.review_state",
                "approved_for_internal_review",
            ),
            (
                "dossier_review_gate_status_approved.json",
                "learning_dossier.review_gate.status",
                "approved_for_internal_review",
            ),
            (
                "human_review_status_approved_card.json",
                "card:teacher_card_invalid_approved_status.human_review.status",
                "approved_for_internal_review",
            ),
        ]
        for fixture_name, expected_layer, expected_status in cases:
            with self.subTest(fixture=fixture_name):
                self.assert_promoted_fixture_fails(fixture_name, expected_layer, expected_status)

    def test_existing_output_file_is_not_overwritten_on_boundary_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "rendered.md"
            original = "existing render must survive\n"
            output.write_text(original, encoding="utf-8")

            result = run_renderer(
                "--input",
                str(INVALID / "packet_status_approved_internal_review.json"),
                "--output",
                str(output),
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("render_boundary=failed", result.stderr)
            self.assertEqual(original, output.read_text(encoding="utf-8"))

    def test_malformed_and_non_object_json_fail_labeled_without_writing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            malformed = tmp / "malformed.json"
            malformed.write_text("{not json}\n", encoding="utf-8")
            non_object = tmp / "array.json"
            non_object.write_text("[]\n", encoding="utf-8")

            for fixture, reason in [
                (malformed, "reason=json_load_failed"),
                (non_object, "reason=top_level_json_not_object"),
            ]:
                with self.subTest(fixture=fixture.name):
                    output = tmp / f"{fixture.stem}.md"
                    result = run_renderer("--input", str(fixture), "--output", str(output))

                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("render_boundary=failed", result.stderr)
                    self.assertIn(reason, result.stderr)
                    self.assertFalse(output.exists())

    def test_validation_failure_is_labeled_without_writing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "rendered.md"
            result = run_renderer(
                "--input",
                str(INVALID / "dossier_review_gate_without_evidence.json"),
                "--output",
                str(output),
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("render_boundary=failed", result.stderr)
            self.assertIn("reason=validation_failed", result.stderr)
            self.assertIn("review_gate.evidence_required_ids must contain at least 1 item", result.stderr)
            self.assertFalse(output.exists())

    def test_check_mode_valid_public_domain_render_still_passes(self) -> None:
        result = run_renderer(
            "--input",
            str(PUBLIC_DOMAIN_FIXTURE),
            "--check",
            str(PUBLIC_DOMAIN_RENDER),
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("render_check=ok", result.stdout)
        self.assertEqual("", result.stderr)

    def test_check_mode_invalid_fixture_does_not_mutate_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "checked.md"
            original = PUBLIC_DOMAIN_RENDER.read_text(encoding="utf-8")
            target.write_text(original, encoding="utf-8")

            result = run_renderer(
                "--input",
                str(INVALID / "human_review_status_approved_card.json"),
                "--check",
                str(target),
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("render_boundary=failed", result.stderr)
            self.assertIn("card:teacher_card_invalid_approved_status.human_review.status", result.stderr)
            self.assertEqual(original, target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
