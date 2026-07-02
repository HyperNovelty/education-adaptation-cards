#!/usr/bin/env python3
"""Shared stdlib helpers for education adaptation card validation."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "schemas" / "education_adaptation_cards.schema.json"
EXAMPLES = sorted((ROOT / "examples").glob("education_cards*.json"))
INVALID_EXAMPLES = sorted((ROOT / "examples" / "invalid").glob("*.json"))

TARGET_SYSTEMS = {"ipublishos", "agent_os", "ipublishos_agent_os_bridge"}
PACKET_STATUSES = {"draft_only", "needs_human_review", "approved_for_internal_review", "rejected"}
LOCAL_REVIEW_ONLY_STATUSES = {"draft_only", "needs_human_review"}
CARD_TYPES = {"teacher_card", "student_card", "assessment_gate_card"}
CARD_RENDER_ORDER = ["teacher_card", "student_card", "assessment_gate_card"]
AUDIENCES = {"teacher", "student", "reviewer", "curriculum_reviewer"}
GRADE_BANDS = {
    "adult_professional",
    "higher_ed",
    "high_school",
    "middle_school",
    "elementary",
    "mixed",
    "unspecified",
}
SOURCE_POLICIES = {"packet_sources_only", "approved_references_only", "no_new_claims"}
RISK_LEVELS = {"low", "medium", "high", "unknown"}
REVIEW_ROLES = {"author", "editor", "teacher", "curriculum_reviewer", "legal_or_policy"}
OUTPUT_TYPES = {"lesson_plan", "discussion_prompt", "student_activity", "rubric", "gate_report", "review_note"}
GATE_STATUSES = {"pass", "fail", "needs_review", "not_run"}
QUESTION_STATUSES = {"unanswered", "partially_sourced", "source_bound", "out_of_scope"}
MISCONCEPTION_SEVERITIES = {"low", "medium", "high", "unknown"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{2,120}$")
FORBIDDEN_RESPONSIBLE_USE_PATTERNS = [
    (
        re.compile(r"\b(assign|issue|calculate|produce)\s+(a\s+)?final\s+grade\b", re.IGNORECASE),
        "must not claim final grading authority",
    ),
    (
        re.compile(r"\b(final|automated)\s+approval\b.{0,80}\bwithout\s+human\s+review\b", re.IGNORECASE),
        "must not claim final approval without human review",
    ),
    (
        re.compile(r"\bdiagnos(?:e|es|ed|ing|is|tic)\b", re.IGNORECASE),
        "must not claim diagnosis or diagnostic authority",
    ),
    (
        re.compile(r"\b(student|learner)\s+surveillance\b|\bsurveil(?:lance|led|ling)?\b", re.IGNORECASE),
        "must not claim student surveillance",
    ),
    (
        re.compile(r"\b(?<!not[\s-])classroom[\s-]+cleared\b|\bapproved\s+for\s+classroom\s+use\b", re.IGNORECASE),
        "must not claim classroom clearance",
    ),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_timestamp(value: Any, label: str) -> None:
    require(isinstance(value, str) and value.strip(), f"{label}.generated_at must be non-empty string")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AssertionError(f"{label}.generated_at is not ISO-like: {value!r}") from exc


def require_slug(value: Any, label: str) -> None:
    require(isinstance(value, str) and SLUG_RE.match(value), f"{label} invalid slug: {value!r}")


def assert_repo_local_path(path_value: str, label: str) -> None:
    p = Path(path_value)
    if not p.is_absolute():
        p = (ROOT / p).resolve()
    else:
        p = p.resolve()
    require(p == ROOT or ROOT in p.parents, f"{label} escapes repository root: {path_value}")
    require(p.exists(), f"{label} does not exist in repository: {path_value}")


def require_string_list(value: Any, label: str, *, min_items: int = 0) -> None:
    require(isinstance(value, list), f"{label} must be array")
    require(len(value) >= min_items, f"{label} must contain at least {min_items} item(s)")
    require(all(isinstance(item, str) and item.strip() for item in value), f"{label} must contain non-empty strings")


def validate_source_binding(binding: Any, label: str) -> None:
    required = {"source_policy", "allowed_source_ids", "blocked_claims_policy"}
    require(isinstance(binding, dict), f"{label} must be object")
    require(set(binding) == required, f"{label} keys mismatch: {sorted(set(binding))}")
    require(binding["source_policy"] in SOURCE_POLICIES, f"{label}.source_policy invalid")
    require_string_list(binding["allowed_source_ids"], f"{label}.allowed_source_ids")
    require(
        isinstance(binding["blocked_claims_policy"], str) and binding["blocked_claims_policy"].strip(),
        f"{label}.blocked_claims_policy empty",
    )


def validate_risk(risk: Any, label: str) -> None:
    required = {"risk_id", "risk_level", "risk_text", "mitigation"}
    require(isinstance(risk, dict), f"{label} must be object")
    require(set(risk) == required, f"{label} keys mismatch: {sorted(set(risk))}")
    require_slug(risk["risk_id"], f"{label}.risk_id")
    require(risk["risk_level"] in RISK_LEVELS, f"{label}.risk_level invalid")
    require(isinstance(risk["risk_text"], str) and risk["risk_text"].strip(), f"{label}.risk_text empty")
    require(isinstance(risk["mitigation"], str) and risk["mitigation"].strip(), f"{label}.mitigation empty")


def validate_human_review(review: Any, label: str) -> None:
    required = {"status", "required_roles", "review_notes"}
    require(isinstance(review, dict), f"{label} must be object")
    require(set(review) == required, f"{label} keys mismatch: {sorted(set(review))}")
    require(review["status"] in PACKET_STATUSES, f"{label}.status invalid")
    require(
        review["status"] in LOCAL_REVIEW_ONLY_STATUSES,
        f"{label}.status must remain local-review-only until separate approval",
    )
    roles = review["required_roles"]
    require(isinstance(roles, list) and roles, f"{label}.required_roles must be non-empty array")
    require(all(role in REVIEW_ROLES for role in roles), f"{label}.required_roles invalid: {roles!r}")
    require_string_list(review["review_notes"], f"{label}.review_notes")


def validate_output(output: Any, label: str) -> None:
    required = {"output_id", "output_type", "description"}
    require(isinstance(output, dict), f"{label} must be object")
    require(set(output) == required, f"{label} keys mismatch: {sorted(set(output))}")
    require_slug(output["output_id"], f"{label}.output_id")
    require(output["output_type"] in OUTPUT_TYPES, f"{label}.output_type invalid")
    require(isinstance(output["description"], str) and output["description"].strip(), f"{label}.description empty")


def validate_learner_question(question: Any, label: str) -> None:
    required = {"question_id", "question_text", "question_status", "source_ids", "reviewer_note"}
    require(isinstance(question, dict), f"{label} must be object")
    require(set(question) == required, f"{label} keys mismatch: {sorted(set(question))}")
    require_slug(question["question_id"], f"{label}.question_id")
    require(isinstance(question["question_text"], str) and question["question_text"].strip(), f"{label}.question_text empty")
    require(question["question_status"] in QUESTION_STATUSES, f"{label}.question_status invalid")
    require_string_list(question["source_ids"], f"{label}.source_ids")
    require(isinstance(question["reviewer_note"], str) and question["reviewer_note"].strip(), f"{label}.reviewer_note empty")


def validate_misconception_evidence(evidence: Any, label: str) -> None:
    required = {
        "misconception_id",
        "misconception_text",
        "evidence_signal",
        "source_ids",
        "severity",
        "teacher_response",
        "reviewer_note",
    }
    require(isinstance(evidence, dict), f"{label} must be object")
    require(set(evidence) == required, f"{label} keys mismatch: {sorted(set(evidence))}")
    require_slug(evidence["misconception_id"], f"{label}.misconception_id")
    require(
        isinstance(evidence["misconception_text"], str) and evidence["misconception_text"].strip(),
        f"{label}.misconception_text empty",
    )
    require(
        isinstance(evidence["evidence_signal"], str) and evidence["evidence_signal"].strip(),
        f"{label}.evidence_signal empty",
    )
    require_string_list(evidence["source_ids"], f"{label}.source_ids", min_items=1)
    require(evidence["severity"] in MISCONCEPTION_SEVERITIES, f"{label}.severity invalid")
    require(
        isinstance(evidence["teacher_response"], str) and evidence["teacher_response"].strip(),
        f"{label}.teacher_response empty",
    )
    require(isinstance(evidence["reviewer_note"], str) and evidence["reviewer_note"].strip(), f"{label}.reviewer_note empty")


def validate_responsible_use_text(card: dict[str, Any], label: str) -> None:
    text = json.dumps(card, sort_keys=True)
    for pattern, message in FORBIDDEN_RESPONSIBLE_USE_PATTERNS:
        require(not pattern.search(text), f"{label} {message}: {pattern.pattern}")


def validate_gate(gate: Any, label: str) -> None:
    required = {"gate_id", "gate_name", "gate_status", "evidence_required"}
    require(isinstance(gate, dict), f"{label} must be object")
    require(set(gate) == required, f"{label} keys mismatch: {sorted(set(gate))}")
    require_slug(gate["gate_id"], f"{label}.gate_id")
    require(isinstance(gate["gate_name"], str) and gate["gate_name"].strip(), f"{label}.gate_name empty")
    require(gate["gate_status"] in GATE_STATUSES, f"{label}.gate_status invalid")
    require_string_list(gate["evidence_required"], f"{label}.evidence_required", min_items=1)


def validate_card(card: Any, label: str) -> str:
    required = {
        "card_id",
        "card_type",
        "title",
        "audience",
        "purpose",
        "source_binding",
        "adaptation_actions",
        "risks",
        "human_review",
        "outputs",
    }
    allowed = required | {"grade_band", "learner_questions", "misconception_evidence", "assessment_gates"}
    require(isinstance(card, dict), f"{label} must be object")
    require(required.issubset(card), f"{label} missing required keys: {sorted(required - set(card))}")
    require(set(card).issubset(allowed), f"{label} has unexpected keys: {sorted(set(card) - allowed)}")
    require_slug(card["card_id"], f"{label}.card_id")
    card_type = card["card_type"]
    require(card_type in CARD_TYPES, f"{label}.card_type invalid")
    require(isinstance(card["title"], str) and card["title"].strip(), f"{label}.title empty")
    require(card["audience"] in AUDIENCES, f"{label}.audience invalid")
    if "grade_band" in card:
        require(card["grade_band"] in GRADE_BANDS, f"{label}.grade_band invalid")
    require(isinstance(card["purpose"], str) and card["purpose"].strip(), f"{label}.purpose empty")
    validate_source_binding(card["source_binding"], f"{label}.source_binding")
    require_string_list(card["adaptation_actions"], f"{label}.adaptation_actions", min_items=1)
    risks = card["risks"]
    require(isinstance(risks, list), f"{label}.risks must be array")
    for idx, risk in enumerate(risks):
        validate_risk(risk, f"{label}.risks[{idx}]")
    validate_human_review(card["human_review"], f"{label}.human_review")
    outputs = card["outputs"]
    require(isinstance(outputs, list) and outputs, f"{label}.outputs must be non-empty array")
    for idx, output in enumerate(outputs):
        validate_output(output, f"{label}.outputs[{idx}]")
    learner_questions = card.get("learner_questions", [])
    require(isinstance(learner_questions, list), f"{label}.learner_questions must be array when present")
    for idx, question in enumerate(learner_questions):
        validate_learner_question(question, f"{label}.learner_questions[{idx}]")
    misconception_evidence = card.get("misconception_evidence", [])
    require(isinstance(misconception_evidence, list), f"{label}.misconception_evidence must be array when present")
    for idx, evidence in enumerate(misconception_evidence):
        validate_misconception_evidence(evidence, f"{label}.misconception_evidence[{idx}]")
    require(
        not learner_questions or misconception_evidence,
        f"{label}.misconception_evidence required when learner_questions are present",
    )
    validate_responsible_use_text(card, label)
    gates = card.get("assessment_gates", [])
    require(isinstance(gates, list), f"{label}.assessment_gates must be array when present")
    if card_type == "assessment_gate_card":
        require(gates, f"{label}.assessment_gates required for assessment_gate_card")
    else:
        require(not gates, f"{label}.assessment_gates should only appear on assessment_gate_card")
    for idx, gate in enumerate(gates):
        validate_gate(gate, f"{label}.assessment_gates[{idx}]")
    return card_type


def validate_doc(doc: Any, label: str) -> dict[str, int]:
    required = {"generated_at", "safety_mode", "target_system", "review_packet", "education_adaptation_cards"}
    require(isinstance(doc, dict), f"{label} must be object")
    require(set(doc) == required, f"{label} top-level keys mismatch: {sorted(set(doc))}")
    parse_timestamp(doc["generated_at"], label)
    require(doc["safety_mode"] == "local_review_only", f"{label}.safety_mode must be local_review_only")
    require(doc["target_system"] in TARGET_SYSTEMS, f"{label}.target_system invalid")

    packet = doc["review_packet"]
    packet_required = {"packet_id", "packet_title", "packet_path", "packet_status"}
    require(isinstance(packet, dict), f"{label}.review_packet must be object")
    require(set(packet) == packet_required, f"{label}.review_packet keys mismatch: {sorted(set(packet))}")
    require_slug(packet["packet_id"], f"{label}.review_packet.packet_id")
    require(
        isinstance(packet["packet_title"], str) and packet["packet_title"].strip(),
        f"{label}.review_packet.packet_title empty",
    )
    require(
        isinstance(packet["packet_path"], str) and packet["packet_path"].strip(),
        f"{label}.review_packet.packet_path empty",
    )
    assert_repo_local_path(packet["packet_path"], f"{label}.review_packet.packet_path")
    require(packet["packet_status"] in PACKET_STATUSES, f"{label}.review_packet.packet_status invalid")
    require(
        packet["packet_status"] in LOCAL_REVIEW_ONLY_STATUSES,
        f"{label}.review_packet.packet_status must remain local-review-only until separate approval",
    )

    cards = doc["education_adaptation_cards"]
    require(isinstance(cards, list), f"{label}.education_adaptation_cards must be array")
    counts = {card_type: 0 for card_type in CARD_TYPES}
    seen_ids: set[str] = set()
    for idx, card in enumerate(cards):
        card_id = card.get("card_id") if isinstance(card, dict) else None
        require(card_id not in seen_ids, f"{label}.education_adaptation_cards duplicate card_id: {card_id}")
        if isinstance(card_id, str):
            seen_ids.add(card_id)
        card_type = validate_card(card, f"{label}.education_adaptation_cards[{idx}]")
        counts[card_type] += 1
    require(
        counts == {"teacher_card": 1, "student_card": 1, "assessment_gate_card": 1},
        f"{label} must contain exactly one of each card type, got {counts}",
    )
    return counts


def expect_invalid_doc(path: Path) -> str:
    try:
        validate_doc(load_json(path), path.name)
    except AssertionError as exc:
        return str(exc)
    raise AssertionError(f"{path.name} was expected to fail validation")
