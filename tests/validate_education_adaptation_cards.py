#!/usr/bin/env python3
"""Stdlib validation for local education adaptation card fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from education_adaptation_cards import EXAMPLES, INVALID_EXAMPLES, SCHEMA, expect_invalid_doc, load_json, require, validate_doc

EXPECTED_INVALID_FAILURES = {
    "dossier_review_gate_without_evidence.json": "review_gate.evidence_required_ids must contain at least 1 item",
    "final_grade_without_review_card.json": "must not claim final grading authority",
    "human_review_status_approved_card.json": "human_review.status must remain local-review-only",
    "learner_question_source_bound_without_source_ids.json": (
        "learner_questions[0].source_ids must be non-empty for source_bound learner question"
    ),
    "learner_questions_without_misconception_evidence.json": "misconception_evidence required when learner_questions are present",
    "misconception_evidence_undeclared_source_id.json": (
        "misconception_evidence[0].source_ids undeclared source_id: S999"
    ),
}


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
        expected = EXPECTED_INVALID_FAILURES.get(path.name)
        if expected:
            require(expected in failure, f"{path.name} failed for unexpected reason: {failure}")
        print(f"validated_invalid_fixture={rel} failure={failure}")
    missing_expected = set(EXPECTED_INVALID_FAILURES) - {path.name for path in INVALID_EXAMPLES}
    require(not missing_expected, f"missing expected invalid fixtures: {sorted(missing_expected)}")
    print("validation=ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"validation=failed error={exc}", file=sys.stderr)
        raise SystemExit(1)
