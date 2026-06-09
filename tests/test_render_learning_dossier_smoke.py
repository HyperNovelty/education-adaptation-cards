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

EXPECTED_SHA256 = "9196bb857e8c1e8e3f3b1b87ba9f7d0e3282a90019cd2855fd7c23a6ed9a6540"


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
    assert "Local review material only. Not classroom-cleared." in rendered
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    assert digest == EXPECTED_SHA256, digest
    print(f"render_smoke=ok fixture={FIXTURE.relative_to(ROOT)} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
