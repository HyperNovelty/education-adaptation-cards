#!/usr/bin/env python3
"""Stdlib validation for local education adaptation card fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from education_adaptation_cards import EXAMPLES, INVALID_EXAMPLES, SCHEMA, expect_invalid_doc, load_json, require, validate_doc


def main() -> int:
    schema = load_json(SCHEMA)
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "schema draft marker changed")
    require(schema.get("properties", {}).get("safety_mode", {}).get("const") == "local_review_only", "schema safety const missing")
    require(EXAMPLES, "no education card examples found")

    print(f"schema={SCHEMA}")
    for path in EXAMPLES:
        counts = validate_doc(load_json(path), path.name)
        rel = path.relative_to(ROOT)
        print(
            "validated_fixture="
            f"{rel} teacher_card={counts['teacher_card']} "
            f"student_card={counts['student_card']} "
            f"assessment_gate_card={counts['assessment_gate_card']}"
        )
    for path in INVALID_EXAMPLES:
        failure = expect_invalid_doc(path)
        rel = path.relative_to(ROOT)
        print(f"validated_invalid_fixture={rel} failure={failure}")
    print("validation=ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"validation=failed error={exc}", file=sys.stderr)
        raise SystemExit(1)
