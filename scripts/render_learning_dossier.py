#!/usr/bin/env python3
"""Render a deterministic local learning dossier from a card fixture."""
from __future__ import annotations

import argparse
from json import JSONDecodeError
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from education_adaptation_cards import card_sort_key, load_json, validate_doc
from scripts.report_review_boundaries import report_review_boundaries


def render_bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def render_indented_bullets(items: list[str]) -> list[str]:
    return [f"  - {item}" for item in items]


def render_learning_dossier(dossier: dict[str, Any]) -> list[str]:
    mission = dossier["learning_mission"]
    task = dossier["practice_task"]
    gate = dossier["review_gate"]
    lines = [
        "## Folder-Based Learning Dossier",
        "",
        f"- Dossier ID: `{dossier['dossier_id']}`",
        f"- Dossier title: {dossier['dossier_title']}",
        "- Folder layout:",
        *render_indented_bullets(dossier["folder_layout"]),
        "",
        "### Learning Mission",
        "",
        f"- Mission ID: `{mission['mission_id']}`",
        f"- Audience: {mission['audience']}",
        f"- Review state: `{mission['review_state']}`",
        f"- Objective: {mission['objective']}",
        "",
        "### Source/Reference Sheet",
        "",
    ]
    for source in dossier["source_reference_sheet"]:
        lines.extend(
            [
                f"- `{source['source_id']}`: {source['title']} ({source['publication_year']}), {source['creator']}",
                f"  Public-domain status: `{source['public_domain_status']}`",
                f"  Public-domain basis: {source['public_domain_basis']}",
                f"  URL: {source['url']}",
                f"  Minimal excerpt: \"{source['excerpt']}\"",
            ]
        )
    lines.extend(["", "### Question Map", ""])
    for question in dossier["question_map"]:
        lines.extend(
            [
                f"- `{question['question_id']}`: {question['question']}",
                f"  Source IDs: {', '.join(question['source_ids'])}",
                f"  Reviewer note: {question['reviewer_note']}",
            ]
        )
    lines.extend(
        [
            "",
            "### Practice Task",
            "",
            f"- Task ID: `{task['task_id']}`",
            f"- Prompt: {task['prompt']}",
            f"- Source IDs: {', '.join(task['source_ids'])}",
            f"- Evidence output IDs: {', '.join(task['evidence_output_ids'])}",
            f"- Reviewer note: {task['reviewer_note']}",
            "",
            "### Evidence Checklist",
            "",
        ]
    )
    for evidence in dossier["evidence_checklist"]:
        lines.extend(
            [
                f"- `{evidence['evidence_id']}`: {evidence['evidence_item']}",
                f"  Source IDs: {', '.join(evidence['source_ids'])}",
                f"  Reviewer note: {evidence['reviewer_note']}",
            ]
        )
    lines.extend(
        [
            "",
            "### Review Gate",
            "",
            f"- Gate ID: `{gate['gate_id']}`",
            f"- Status: `{gate['status']}`",
            f"- Required roles: {', '.join(gate['required_roles'])}",
            f"- Evidence required IDs: {', '.join(gate['evidence_required_ids'])}",
            f"- Reviewer note: {gate['reviewer_note']}",
            "",
        ]
    )
    return lines


def render_card(card: dict[str, Any]) -> list[str]:
    lines = [
        f"## {card['title']}",
        "",
        f"- Card ID: `{card['card_id']}`",
        f"- Card type: `{card['card_type']}`",
        f"- Audience: `{card['audience']}`",
        f"- Grade band: `{card.get('grade_band', 'unspecified')}`",
        "",
        "### Purpose",
        "",
        card["purpose"],
        "",
        "### Source Binding",
        "",
        f"- Source policy: `{card['source_binding']['source_policy']}`",
        f"- Allowed source IDs: {', '.join(card['source_binding']['allowed_source_ids'])}",
        f"- Blocked claims policy: {card['source_binding']['blocked_claims_policy']}",
        "",
        "### Adaptation Actions",
        "",
        *render_bullets(card["adaptation_actions"]),
        "",
        "### Risks",
        "",
    ]
    for risk in card["risks"]:
        lines.extend(
            [
                f"- `{risk['risk_id']}` [{risk['risk_level']}]: {risk['risk_text']}",
                f"  Mitigation: {risk['mitigation']}",
            ]
        )
    lines.extend(
        [
            "",
            "### Human Review",
            "",
            f"- Status: `{card['human_review']['status']}`",
            f"- Required roles: {', '.join(card['human_review']['required_roles'])}",
            "- Review notes:",
            *render_indented_bullets(card["human_review"]["review_notes"]),
            "",
            "### Outputs",
            "",
        ]
    )
    for output in card["outputs"]:
        lines.append(f"- `{output['output_id']}` [{output['output_type']}]: {output['description']}")
    learner_questions = card.get("learner_questions", [])
    if learner_questions:
        lines.extend(["", "### Learner Questions", ""])
        for question in learner_questions:
            source_ids = ", ".join(question["source_ids"]) or "none"
            lines.extend(
                [
                    f"- `{question['question_id']}` [{question['question_status']}]: {question['question_text']}",
                    f"  Source IDs: {source_ids}",
                    f"  Reviewer note: {question['reviewer_note']}",
                ]
            )
    misconception_evidence = card.get("misconception_evidence", [])
    if misconception_evidence:
        lines.extend(["", "### Misconception Evidence", ""])
        for evidence in misconception_evidence:
            lines.extend(
                [
                    f"- `{evidence['misconception_id']}` [{evidence['severity']}]: {evidence['misconception_text']}",
                    f"  Evidence signal: {evidence['evidence_signal']}",
                    f"  Source IDs: {', '.join(evidence['source_ids'])}",
                    f"  Teacher response: {evidence['teacher_response']}",
                    f"  Reviewer note: {evidence['reviewer_note']}",
                ]
            )
    gates = card.get("assessment_gates", [])
    if gates:
        lines.extend(["", "### Assessment Gates", ""])
        for gate in gates:
            lines.extend(
                [
                    f"- `{gate['gate_id']}` [{gate['gate_status']}]: {gate['gate_name']}",
                    "  Evidence required:",
                    *render_indented_bullets(gate["evidence_required"]),
                ]
            )
    lines.append("")
    return lines


def render_dossier(doc: dict[str, Any], source_path: Path) -> str:
    validate_doc(doc, source_path.name)
    packet = doc["review_packet"]
    cards = sorted(doc["education_adaptation_cards"], key=card_sort_key)
    lines = [
        "# Local Learning Dossier",
        "",
        "Local review material only. Not classroom-cleared. No LMS, network, account, publish, or student-data actions are authorized by this artifact.",
        "",
        "## Packet Context",
        "",
        f"- Source fixture: `{source_path.relative_to(ROOT)}`",
        f"- Generated at: `{doc['generated_at']}`",
        f"- Safety mode: `{doc['safety_mode']}`",
        f"- Target system: `{doc['target_system']}`",
        f"- Packet ID: `{packet['packet_id']}`",
        f"- Packet title: {packet['packet_title']}",
        f"- Packet path: `{packet['packet_path']}`",
        f"- Packet status: `{packet['packet_status']}`",
        "",
        "## Review Gate Summary",
        "",
        "- Lane completeness: exactly one teacher card, one student card, and one assessment/gate card validated before rendering.",
        "- Release boundary: all human review statuses must remain `draft_only` or `needs_human_review`.",
        "- Rendering mode: deterministic markdown generated from local fixture content only.",
        "",
    ]
    if "learning_dossier" in doc:
        lines.extend(render_learning_dossier(doc["learning_dossier"]))
    for card in cards:
        lines.extend(render_card(card))
    return "\n".join(lines).rstrip() + "\n"


def boundary_failure_line(source_path: Path, reason: str, detail: str) -> str:
    return f"render_boundary=failed input={source_path} reason={reason} detail={detail}"


def review_boundary_failure_line(source_path: Path, doc: dict[str, Any]) -> str | None:
    report = report_review_boundaries(doc, source_path)
    violations = [item for item in report["items"] if item["result"] == "violation"]
    if not violations:
        return None
    violation = violations[0]
    return (
        f"render_boundary=failed input={source_path} reason=review_boundary_violation "
        f"layer={violation['label']} location={violation['location']} "
        f"status={violation['observed_status']!r} allowed={','.join(violation['allowed_statuses'])}"
    )


def load_valid_renderable_doc(source_path: Path) -> dict[str, Any] | None:
    try:
        doc = load_json(source_path)
    except (OSError, JSONDecodeError) as exc:
        print(boundary_failure_line(source_path, "json_load_failed", str(exc)), file=sys.stderr)
        return None
    if not isinstance(doc, dict):
        print(
            boundary_failure_line(source_path, "top_level_json_not_object", "top-level JSON must be object"),
            file=sys.stderr,
        )
        return None

    try:
        validate_doc(doc, source_path.name)
    except AssertionError as exc:
        boundary_failure = review_boundary_failure_line(source_path, doc)
        if boundary_failure:
            print(boundary_failure, file=sys.stderr)
        else:
            print(boundary_failure_line(source_path, "validation_failed", str(exc)), file=sys.stderr)
        return None
    return doc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", nargs="?", type=Path, help="Path to an education adaptation card JSON fixture")
    parser.add_argument("--input", dest="input_path", type=Path, help="Path to an education adaptation card JSON fixture")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("-o", "--output", type=Path, help="Write markdown to a file instead of stdout")
    output_group.add_argument("--check", type=Path, help="Compare markdown to a checked-in render without writing files")
    args = parser.parse_args()
    if args.fixture and args.input_path:
        parser.error("use either positional fixture or --input, not both")
    if not args.fixture and not args.input_path:
        parser.error("provide a fixture path or --input")
    return args


def main() -> int:
    args = parse_args()
    fixture = (args.input_path or args.fixture).resolve()
    doc = load_valid_renderable_doc(fixture)
    if doc is None:
        return 1
    rendered = render_dossier(doc, fixture)
    if args.check:
        target = args.check
        if not target.exists():
            print(f"render_check=missing target={target}", file=sys.stderr)
            return 1
        checked_in = target.read_text(encoding="utf-8")
        if checked_in != rendered:
            print(f"render_check=stale target={target}", file=sys.stderr)
            return 1
        print(f"render_check=ok target={target}")
        return 0
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
