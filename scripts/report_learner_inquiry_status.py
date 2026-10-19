#!/usr/bin/env python3
"""Report learner-question status and misconception evidence for local review."""
from __future__ import annotations

import argparse
import json
import sys
from json import JSONDecodeError
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from education_adaptation_cards import load_json, validate_doc

REPORT_TYPE = "education_adaptation_cards.learner_inquiry_status"
REPORT_VERSION = "1.0"
BOUNDARY_STATEMENT = (
    "This is a local reviewer decision surface only; attention items require human inspection and are not "
    "scores, grades, diagnoses, profiles, readiness claims, approvals, or deployment authorization."
)
ATTENTION_STATUSES = {"unanswered", "partially_sourced", "out_of_scope"}


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return path.name


def string_list(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def attention_items_for_question(card_id: str, question: dict[str, Any], index: int) -> list[dict[str, Any]]:
    status = question.get("question_status")
    source_ids = string_list(question.get("source_ids"))
    location = f"card:{card_id}.learner_questions[{index}]"
    items: list[dict[str, Any]] = []
    if status in ATTENTION_STATUSES:
        items.append({"kind": "learner_question", "id": question.get("question_id"), "reason": status, "location": location})
    if not source_ids and status in {"unanswered", "out_of_scope"}:
        items.append({"kind": "learner_question", "id": question.get("question_id"), "reason": "empty_source_ids_without_source_binding", "location": location})
    return items


def learner_inquiry_status_report(doc: dict[str, Any], source_path: Path) -> dict[str, Any]:
    packet = doc.get("review_packet", {})
    report: dict[str, Any] = {
        "report_type": REPORT_TYPE,
        "report_version": REPORT_VERSION,
        "source_path": display_path(source_path),
        "packet_id": packet.get("packet_id") if isinstance(packet, dict) else None,
        "boundary_statement": BOUNDARY_STATEMENT,
        "cards": [],
        "attention_items": [],
        "counts": {},
    }
    cards = doc.get("education_adaptation_cards", [])
    for card_index, card in enumerate(cards if isinstance(cards, list) else []):
        if not isinstance(card, dict):
            continue
        card_id = card.get("card_id")
        card_report = {
            "card_id": card_id,
            "card_type": card.get("card_type"),
            "learner_questions": [],
            "misconception_evidence": [],
        }
        questions = card.get("learner_questions", [])
        for question_index, question in enumerate(questions if isinstance(questions, list) else []):
            if not isinstance(question, dict):
                continue
            item = {
                "question_id": question.get("question_id"),
                "question_status": question.get("question_status"),
                "source_ids": string_list(question.get("source_ids")),
                "reviewer_note": question.get("reviewer_note"),
            }
            card_report["learner_questions"].append(item)
            report["attention_items"].extend(attention_items_for_question(card_id, question, question_index))
        evidence = card.get("misconception_evidence", [])
        for evidence_index, misconception in enumerate(evidence if isinstance(evidence, list) else []):
            if not isinstance(misconception, dict):
                continue
            item = {
                "misconception_id": misconception.get("misconception_id"),
                "severity": misconception.get("severity"),
                "source_ids": string_list(misconception.get("source_ids")),
                "teacher_response": misconception.get("teacher_response"),
                "reviewer_note": misconception.get("reviewer_note"),
            }
            card_report["misconception_evidence"].append(item)
            if misconception.get("severity") in {"high", "unknown"}:
                report["attention_items"].append({
                    "kind": "misconception_evidence",
                    "id": misconception.get("misconception_id"),
                    "reason": misconception.get("severity"),
                    "location": f"card:{card_id}.misconception_evidence[{evidence_index}]",
                })
        report["cards"].append(card_report)

    question_items = [question for card in report["cards"] for question in card["learner_questions"]]
    misconception_items = [item for card in report["cards"] for item in card["misconception_evidence"]]
    report["counts"] = {
        "cards": len(report["cards"]),
        "learner_questions": len(question_items),
        "misconception_evidence": len(misconception_items),
        "attention_items": len(report["attention_items"]),
        "questions_by_status": {
            status: sum(1 for item in question_items if item["question_status"] == status)
            for status in ("unanswered", "partially_sourced", "source_bound", "out_of_scope")
        },
        "misconceptions_by_severity": {
            severity: sum(1 for item in misconception_items if item["severity"] == severity)
            for severity in ("low", "medium", "high", "unknown")
        },
    }
    return report


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False) + "\n"


def render_human(report: dict[str, Any]) -> str:
    lines = [
        "learner_inquiry_status_report",
        f"source={report['source_path']}",
        f"packet_id={report['packet_id']}",
        f"boundary={report['boundary_statement']}",
    ]
    for card in report["cards"]:
        lines.append(f"- card {card['card_id']} type={card['card_type']}")
        for question in card["learner_questions"]:
            lines.append(f"  - question {question['question_id']} status={question['question_status']} sources={','.join(question['source_ids'])}")
        for evidence in card["misconception_evidence"]:
            lines.append(f"  - misconception {evidence['misconception_id']} severity={evidence['severity']} sources={','.join(evidence['source_ids'])}")
    for item in report["attention_items"]:
        lines.append(f"attention kind={item['kind']} id={item['id']} reason={item['reason']} location={item['location']}")
    lines.append(f"counts={json.dumps(report['counts'], sort_keys=True)}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to an education adaptation card JSON fixture")
    parser.add_argument("--format", choices=["human", "json"], default="human", help="Output format")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--output", type=Path, help="Write output to a file instead of stdout")
    output_group.add_argument("--check", type=Path, help="Compare deterministic JSON to a checked-in report without writing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = args.input.resolve()
    try:
        doc = load_json(source_path)
    except (OSError, JSONDecodeError) as exc:
        print(f"learner_inquiry_status_report=failed input={source_path} error={exc}", file=sys.stderr)
        return 1
    if not isinstance(doc, dict):
        print(f"learner_inquiry_status_report=failed input={source_path} error=top-level JSON must be object", file=sys.stderr)
        return 1
    try:
        validate_doc(doc, source_path.name)
    except AssertionError as exc:
        print(f"learner_inquiry_status_report=failed input={source_path} validation_error={exc}", file=sys.stderr)
        return 1

    report = learner_inquiry_status_report(doc, source_path)
    rendered_json = render_json(report)
    if args.check:
        try:
            checked_in = args.check.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"learner_inquiry_status_check=failed target={args.check} error={exc}", file=sys.stderr)
            return 1
        if checked_in != rendered_json:
            print(f"learner_inquiry_status_check=stale target={args.check}", file=sys.stderr)
            return 1
        print(f"learner_inquiry_status_check=ok target={args.check}")
        return 0

    rendered = rendered_json if args.format == "json" else render_human(report)
    if args.output:
        try:
            args.output.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(f"learner_inquiry_status_report=failed target={args.output} error={exc}", file=sys.stderr)
            return 1
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
