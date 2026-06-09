#!/usr/bin/env python3
"""Stdlib validation for local education adaptation card fixtures.

This intentionally validates the current mock contract without installing or
importing any third-party JSON Schema package.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = Path("/home/aware1/.hermes/content-empire").resolve()
SCHEMA = ROOT / "schemas" / "education_adaptation_cards.schema.json"
EXAMPLES = sorted((ROOT / "examples").glob("education_cards*.json"))

TARGET_SYSTEMS = {"ipublishos", "agent_os", "ipublishos_agent_os_bridge"}
PACKET_STATUSES = {"draft_only", "needs_human_review", "approved_for_internal_review", "rejected"}
CARD_TYPES = {"teacher_card", "student_card", "assessment_gate_card"}
AUDIENCES = {"teacher", "student", "reviewer", "curriculum_reviewer"}
GRADE_BANDS = {"adult_professional", "higher_ed", "high_school", "middle_school", "elementary", "mixed", "unspecified"}
SOURCE_POLICIES = {"packet_sources_only", "approved_references_only", "no_new_claims"}
RISK_LEVELS = {"low", "medium", "high", "unknown"}
REVIEW_ROLES = {"author", "editor", "teacher", "curriculum_reviewer", "legal_or_policy"}
OUTPUT_TYPES = {"lesson_plan", "discussion_prompt", "student_activity", "rubric", "gate_report", "review_note"}
GATE_STATUSES = {"pass", "fail", "needs_review", "not_run"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{2,120}$")


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


def assert_under_content_root(path_value: str, label: str) -> None:
    p = Path(path_value)
    if not p.is_absolute():
        p = (CONTENT_ROOT / p).resolve()
    else:
        p = p.resolve()
    require(p == CONTENT_ROOT or CONTENT_ROOT in p.parents, f"{label} escapes content root: {path_value}")


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
    require(isinstance(binding["blocked_claims_policy"], str) and binding["blocked_claims_policy"].strip(), f"{label}.blocked_claims_policy empty")


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


def validate_gate(gate: Any, label: str) -> None:
    required = {"gate_id", "gate_name", "gate_status", "evidence_required"}
    require(isinstance(gate, dict), f"{label} must be object")
    require(set(gate) == required, f"{label} keys mismatch: {sorted(set(gate))}")
    require_slug(gate["gate_id"], f"{label}.gate_id")
    require(isinstance(gate["gate_name"], str) and gate["gate_name"].strip(), f"{label}.gate_name empty")
    require(gate["gate_status"] in GATE_STATUSES, f"{label}.gate_status invalid")
    require_string_list(gate["evidence_required"], f"{label}.evidence_required", min_items=1)


def validate_card(card: Any, label: str) -> str:
    required = {"card_id", "card_type", "title", "audience", "purpose", "source_binding", "adaptation_actions", "risks", "human_review", "outputs"}
    allowed = required | {"grade_band", "assessment_gates"}
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
    require(isinstance(packet["packet_title"], str) and packet["packet_title"].strip(), f"{label}.review_packet.packet_title empty")
    require(isinstance(packet["packet_path"], str) and packet["packet_path"].strip(), f"{label}.review_packet.packet_path empty")
    assert_under_content_root(packet["packet_path"], f"{label}.review_packet.packet_path")
    require(packet["packet_status"] in PACKET_STATUSES, f"{label}.review_packet.packet_status invalid")

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
    require(counts == {"teacher_card": 1, "student_card": 1, "assessment_gate_card": 1}, f"{label} must contain exactly one of each card type, got {counts}")
    return counts


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
    print("validation=ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"validation=failed error={exc}", file=sys.stderr)
        raise SystemExit(1)
