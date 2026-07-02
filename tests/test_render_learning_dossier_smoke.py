#!/usr/bin/env python3
"""Smoke test for deterministic learning dossier rendering."""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_learning_dossier.py"
FIXTURE = ROOT / "examples" / "education_cards.minimal.json"

EXPECTED_SHA256 = "44a52d62e1f7c133ffaa14d06d9b75d7db302a8504c26a9f86af81d377b6a792"


def main() -> int:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURE)],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    rendered = result.stdout
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
