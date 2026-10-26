#!/usr/bin/env python3
"""Focused tests for the deterministic offline HTML dossier renderer."""
from __future__ import annotations

import json
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_learning_dossier_html.py"
FIXTURE = ROOT / "examples" / "education_cards.public_domain_folder_dossier.json"
ARTIFACT = ROOT / "examples" / "rendered" / "public_domain_learning_dossier.html"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import render_learning_dossier_html as render_module


def run_renderer(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


class RenderLearningDossierHtmlTests(unittest.TestCase):
    def test_deterministic_render_and_check(self) -> None:
        first = run_renderer("--input", str(FIXTURE))
        second = run_renderer("--input", str(FIXTURE))
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertTrue(first.stdout.startswith("<!doctype html>\n<html lang=\"en\">"))
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "packet.html"
            written = run_renderer("--input", str(FIXTURE), "--output", str(output))
            self.assertEqual(0, written.returncode, written.stderr)
            self.assertIn("html_render=ok", written.stdout)
            checked = run_renderer("--input", str(FIXTURE), "--check", str(output))
            self.assertEqual(0, checked.returncode, checked.stderr)
            self.assertIn("html_render_check=ok", checked.stdout)

    def test_key_sections_content_ids_and_statuses_are_present(self) -> None:
        result = run_renderer("--input", str(FIXTURE))
        self.assertEqual(0, result.returncode, result.stderr)
        rendered = result.stdout.lower()
        for marker in (
            "Packet Metadata", "local review only", "Learning Mission", "Source/Reference Sheet",
            "Question Map", "Practice Task", "Evidence Checklist", "Review Gate",
            "Teacher Card: Alice Source Folder Review", "Student Card: Alice Source Check Draft",
            "Assessment/Gate Card: Alice Folder Evidence Review", "PD001", "needs_human_review",
            "teacher", "curriculum_reviewer",
        ):
            self.assertIn(marker.lower(), rendered)

    def test_fixture_strings_are_html_escaped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "synthetic.json"
            doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
            doc["review_packet"]["packet_title"] = "<Packet & \"review\">"
            doc["learning_dossier"]["dossier_title"] = "Dossier > one"
            doc["learning_dossier"]["source_reference_sheet"][0]["title"] = "<Alice & \"Source\">"
            doc["learning_dossier"]["source_reference_sheet"][0]["excerpt"] = "<excerpt> & 'quoted'"
            path.write_text(json.dumps(doc), encoding="utf-8")
            result = run_renderer("--input", str(path))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("&lt;Packet &amp; &quot;review&quot;&gt;", result.stdout)
        self.assertIn("&lt;Alice &amp; &quot;Source&quot;&gt;", result.stdout)
        self.assertIn("&lt;excerpt&gt; &amp; &#x27;quoted&#x27;", result.stdout)
        self.assertNotIn("<Packet &", result.stdout)

    def test_malformed_non_object_and_validator_invalid_inputs_fail_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            cases = {
                "malformed.json": "{",
                "array.json": "[]",
                "invalid.json": (ROOT / "examples/invalid/packet_status_approved_internal_review.json").read_text(encoding="utf-8"),
            }
            for name, contents in cases.items():
                input_path = directory / name
                output_path = directory / f"{name}.html"
                input_path.write_text(contents, encoding="utf-8")
                result = run_renderer("--input", str(input_path), "--output", str(output_path))
                self.assertNotEqual(0, result.returncode, name)
                self.assertIn("html_render=failed", result.stderr, name)
                self.assertFalse(output_path.exists(), name)

    def test_malformed_utf8_input_fails_labeled_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "malformed-utf8.json"
            input_path.write_bytes(b"{\"invalid\": \xff}\n")
            result = run_renderer("--input", str(input_path))

        self.assertNotEqual(0, result.returncode)
        self.assertIn("html_render=failed", result.stderr)
        self.assertIn("reason=json_load_failed", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_non_utf8_check_target_fails_labeled_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "non-utf8.html"
            target.write_bytes(b"<html>\xff</html>")
            result = run_renderer("--input", str(FIXTURE), "--check", str(target))

        self.assertNotEqual(0, result.returncode)
        self.assertIn("html_render_check=failed", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_atomic_output_replace_failure_preserves_target_and_cleans_temp(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "packet.html"
            original = b"existing output must survive byte-for-byte\xff"
            output.write_bytes(original)
            before = set(Path(tmpdir).iterdir())
            with mock.patch.object(render_module.os, "replace", side_effect=OSError("injected replace failure")):
                with self.assertRaisesRegex(OSError, "injected replace failure"):
                    render_module.write_output_atomically(output, "new rendered output")
            self.assertEqual(original, output.read_bytes())
            self.assertEqual(before, set(Path(tmpdir).iterdir()))

    def test_atomic_output_failure_is_labeled_and_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "packet.html"
            original = b"existing output\n"
            output.write_bytes(original)
            argv = ["render_learning_dossier_html.py", "--input", str(FIXTURE), "--output", str(output)]
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch.object(render_module.os, "replace", side_effect=OSError("injected replace failure")):
                with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    result = render_module.main()
            self.assertNotEqual(0, result)
            self.assertIn("html_render=failed", stderr.getvalue())
            self.assertIn("reason=output_write_failed", stderr.getvalue())
            self.assertEqual(original, output.read_bytes())

    def test_missing_dossier_fails_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "no-dossier.json"
            output_path = Path(tmpdir) / "no-dossier.html"
            doc = json.loads((ROOT / "examples/education_cards.minimal.json").read_text(encoding="utf-8"))
            input_path.write_text(json.dumps(doc), encoding="utf-8")
            result = run_renderer("--input", str(input_path), "--output", str(output_path))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("learning_dossier is required", result.stderr)
            self.assertFalse(output_path.exists())

    def test_stale_check_does_not_mutate_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "stale.html"
            target.write_text("stale\n", encoding="utf-8")
            result = run_renderer("--input", str(FIXTURE), "--check", str(target))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("html_render_check=stale", result.stderr)
            self.assertEqual("stale\n", target.read_text(encoding="utf-8"))

    def test_offline_artifact_has_no_scripts_external_resources_or_forms(self) -> None:
        html = ARTIFACT.read_text(encoding="utf-8").lower()
        self.assertNotIn("<script", html)
        self.assertNotIn("<form", html)
        for token in ("src=\"http:", "src=\"https:", "href=\"http:", "href=\"https:", "url(http:", "url(https:"):
            self.assertNotIn(token, html)
        self.assertIn("local review only", html)

    def test_output_and_check_are_mutually_exclusive(self) -> None:
        result = run_renderer("--input", str(FIXTURE), "--output", "/tmp/a.html", "--check", "/tmp/b.html")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("not allowed with argument", result.stderr)


if __name__ == "__main__":
    unittest.main()
