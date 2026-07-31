#!/usr/bin/env python3
"""Smoke test for deterministic learning dossier rendering."""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_learning_dossier.py"
FIXTURE = ROOT / "examples" / "education_cards.minimal.json"
PUBLIC_DOMAIN_FIXTURE = ROOT / "examples" / "education_cards.public_domain_folder_dossier.json"
PUBLIC_DOMAIN_RENDER = ROOT / "examples" / "rendered" / "public_domain_learning_dossier.md"

EXPECTED_SHA256 = "44a52d62e1f7c133ffaa14d06d9b75d7db302a8504c26a9f86af81d377b6a792"


def render_fixture(path: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(path)],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return result.stdout


class RenderLearningDossierSmokeTests(unittest.TestCase):
    def test_minimal_fixture_render_is_stable(self) -> None:
        rendered = render_fixture(FIXTURE)
        self.assertTrue(rendered.startswith("# Local Learning Dossier\n"))
        self.assertIn("Teacher Adaptation Card", rendered)
        self.assertIn("Student Adaptation Card", rendered)
        self.assertIn("Assessment and Gate Card", rendered)
        self.assertIn("### Learner Questions", rendered)
        self.assertIn("### Misconception Evidence", rendered)
        self.assertIn("Local review material only. Not classroom-cleared.", rendered)
        digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        self.assertEqual(EXPECTED_SHA256, digest)

    def test_public_domain_folder_dossier_render_matches_checked_in_demo(self) -> None:
        rendered = render_fixture(PUBLIC_DOMAIN_FIXTURE)
        checked_in = PUBLIC_DOMAIN_RENDER.read_text(encoding="utf-8")
        self.assertEqual(checked_in, rendered)
        self.assertIn("## Folder-Based Learning Dossier", rendered)
        self.assertIn("Alice's Adventures in Wonderland", rendered)
        self.assertIn("pre_1929_public_domain_us", rendered)
        self.assertIn("### Evidence Checklist", rendered)
        self.assertIn("### Review Gate", rendered)

    def test_check_mode_succeeds_when_checked_in_render_is_current(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--input",
                str(PUBLIC_DOMAIN_FIXTURE),
                "--check",
                str(PUBLIC_DOMAIN_RENDER),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("render_check=ok", result.stdout)
        self.assertEqual("", result.stderr)

    def test_check_mode_reports_stale_without_mutating_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stale_render = Path(tmpdir) / "public_domain_learning_dossier.md"
            stale_content = PUBLIC_DOMAIN_RENDER.read_text(encoding="utf-8") + "\nSTALE\n"
            stale_render.write_text(stale_content, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(PUBLIC_DOMAIN_FIXTURE),
                    "--check",
                    str(stale_render),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=ROOT,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("render_check=stale", result.stderr)
            self.assertEqual(stale_content, stale_render.read_text(encoding="utf-8"))

    def test_check_mode_reports_missing_without_creating_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_render = Path(tmpdir) / "missing" / "public_domain_learning_dossier.md"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(PUBLIC_DOMAIN_FIXTURE),
                    "--check",
                    str(missing_render),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=ROOT,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("render_check=missing", result.stderr)
            self.assertFalse(missing_render.parent.exists())

    def test_check_mode_is_mutually_exclusive_with_output(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--input",
                str(PUBLIC_DOMAIN_FIXTURE),
                "--check",
                str(PUBLIC_DOMAIN_RENDER),
                "--output",
                "/tmp/should-not-be-written.md",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("not allowed with argument", result.stderr)


def main() -> int:
    rendered = render_fixture(FIXTURE)
    assert rendered.startswith("# Local Learning Dossier\n")
    assert "Teacher Adaptation Card" in rendered
    assert "Student Adaptation Card" in rendered
    assert "Assessment and Gate Card" in rendered
    assert "### Learner Questions" in rendered
    assert "### Misconception Evidence" in rendered
    assert "Local review material only. Not classroom-cleared." in rendered
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    assert digest == EXPECTED_SHA256, digest
    print(f"render_smoke=ok fixture={FIXTURE.relative_to(ROOT)} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
