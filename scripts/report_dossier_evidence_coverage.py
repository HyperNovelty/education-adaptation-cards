#!/usr/bin/env python3
"""Report source and evidence coverage for a learning dossier fixture."""
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

REPORT_TYPE = "education_adaptation_cards.dossier_evidence_coverage"
REPORT_VERSION = "1.0"
BOUNDARY_STATEMENT = (
    "Structural coverage does not mean approval, grading, classroom readiness, "
    "or deployment permission."
)


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return path.name


def string_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def append_missing_if_empty(findings: list[dict[str, str]], location: str, value: Any) -> None:
    if not string_items(value):
        findings.append({"location": location, "id": ""})


def append_unknowns(
    findings: list[dict[str, str]],
    location: str,
    values: Any,
    allowed: set[str],
) -> None:
    for item in string_items(values):
        if item not in allowed:
            findings.append({"location": location, "id": item})


def evidence_coverage_report(doc: dict[str, Any], source_path: Path) -> dict[str, Any]:
    packet = doc.get("review_packet", {})
    dossier = doc.get("learning_dossier")
    report: dict[str, Any] = {
        "report_type": REPORT_TYPE,
        "report_version": REPORT_VERSION,
        "source_path": display_path(source_path),
        "packet_id": packet.get("packet_id") if isinstance(packet, dict) else None,
        "dossier_id": None,
        "boundary_statement": BOUNDARY_STATEMENT,
        "declared_source_ids": [],
        "question_sources": [],
        "practice_task": None,
        "evidence_checklist": [],
        "review_gate": None,
        "coverage": {
            "missing_source_references": [],
            "unknown_source_references": [],
            "missing_evidence_references": [],
            "unknown_evidence_references": [],
            "unreferenced_declared_source_ids": [],
            "uncovered_evidence_checklist_ids": [],
        },
        "counts": {},
    }
    if not isinstance(dossier, dict):
        report["coverage"]["missing_learning_dossier"] = True
        report["counts"] = make_counts(report)
        return report

    report["dossier_id"] = dossier.get("dossier_id")

    sources = dossier.get("source_reference_sheet", [])
    if isinstance(sources, list):
        declared_source_ids = [
            source.get("source_id")
            for source in sources
            if isinstance(source, dict) and isinstance(source.get("source_id"), str)
        ]
    else:
        declared_source_ids = []
    report["declared_source_ids"] = declared_source_ids
    declared_source_set = set(declared_source_ids)

    referenced_source_ids: set[str] = set()
    evidence_ids: list[str] = []
    evidence_id_set: set[str] = set()
    referenced_evidence_ids: set[str] = set()

    questions = dossier.get("question_map", [])
    if isinstance(questions, list):
        for idx, question in enumerate(questions):
            if not isinstance(question, dict):
                continue
            location = f"learning_dossier.question_map[{idx}].source_ids"
            source_ids = string_items(question.get("source_ids"))
            referenced_source_ids.update(source_id for source_id in source_ids if source_id in declared_source_set)
            append_missing_if_empty(report["coverage"]["missing_source_references"], location, source_ids)
            append_unknowns(report["coverage"]["unknown_source_references"], location, source_ids, declared_source_set)
            report["question_sources"].append(
                {"question_id": question.get("question_id"), "source_ids": source_ids}
            )

    evidence = dossier.get("evidence_checklist", [])
    if isinstance(evidence, list):
        for idx, item in enumerate(evidence):
            if not isinstance(item, dict):
                continue
            evidence_id = item.get("evidence_id")
            if isinstance(evidence_id, str):
                evidence_ids.append(evidence_id)
                evidence_id_set.add(evidence_id)
            location = f"learning_dossier.evidence_checklist[{idx}].source_ids"
            source_ids = string_items(item.get("source_ids"))
            referenced_source_ids.update(source_id for source_id in source_ids if source_id in declared_source_set)
            append_missing_if_empty(report["coverage"]["missing_source_references"], location, source_ids)
            append_unknowns(report["coverage"]["unknown_source_references"], location, source_ids, declared_source_set)
            report["evidence_checklist"].append({"evidence_id": evidence_id, "source_ids": source_ids})

    task = dossier.get("practice_task", {})
    if isinstance(task, dict):
        source_location = "learning_dossier.practice_task.source_ids"
        evidence_location = "learning_dossier.practice_task.evidence_output_ids"
        source_ids = string_items(task.get("source_ids"))
        output_ids = string_items(task.get("evidence_output_ids"))
        referenced_source_ids.update(source_id for source_id in source_ids if source_id in declared_source_set)
        referenced_evidence_ids.update(evidence_id for evidence_id in output_ids if evidence_id in evidence_id_set)
        append_missing_if_empty(report["coverage"]["missing_source_references"], source_location, source_ids)
        append_unknowns(report["coverage"]["unknown_source_references"], source_location, source_ids, declared_source_set)
        append_missing_if_empty(report["coverage"]["missing_evidence_references"], evidence_location, output_ids)
        append_unknowns(report["coverage"]["unknown_evidence_references"], evidence_location, output_ids, evidence_id_set)
        report["practice_task"] = {
            "task_id": task.get("task_id"),
            "source_ids": source_ids,
            "evidence_output_ids": output_ids,
        }

    gate = dossier.get("review_gate", {})
    if isinstance(gate, dict):
        evidence_location = "learning_dossier.review_gate.evidence_required_ids"
        required_evidence_ids = string_items(gate.get("evidence_required_ids"))
        referenced_evidence_ids.update(evidence_id for evidence_id in required_evidence_ids if evidence_id in evidence_id_set)
        append_missing_if_empty(report["coverage"]["missing_evidence_references"], evidence_location, required_evidence_ids)
        append_unknowns(
            report["coverage"]["unknown_evidence_references"],
            evidence_location,
            required_evidence_ids,
            evidence_id_set,
        )
        report["review_gate"] = {
            "gate_id": gate.get("gate_id"),
            "status": gate.get("status"),
            "required_roles": string_items(gate.get("required_roles")),
            "evidence_required_ids": required_evidence_ids,
        }

    report["coverage"]["unreferenced_declared_source_ids"] = [
        source_id for source_id in declared_source_ids if source_id not in referenced_source_ids
    ]
    report["coverage"]["uncovered_evidence_checklist_ids"] = [
        evidence_id for evidence_id in evidence_ids if evidence_id not in referenced_evidence_ids
    ]
    report["counts"] = make_counts(report)
    return report


def make_counts(report: dict[str, Any]) -> dict[str, int]:
    coverage = report["coverage"]
    practice_task_count = 1 if report.get("practice_task") else 0
    return {
        "declared_sources": len(report.get("declared_source_ids", [])),
        "questions": len(report.get("question_sources", [])),
        "practice_tasks": practice_task_count,
        "practice_task_evidence_outputs": len((report.get("practice_task") or {}).get("evidence_output_ids", [])),
        "evidence_checklist_items": len(report.get("evidence_checklist", [])),
        "review_gate_required_evidence": len((report.get("review_gate") or {}).get("evidence_required_ids", [])),
        "missing_source_references": len(coverage.get("missing_source_references", [])),
        "unknown_source_references": len(coverage.get("unknown_source_references", [])),
        "missing_evidence_references": len(coverage.get("missing_evidence_references", [])),
        "unknown_evidence_references": len(coverage.get("unknown_evidence_references", [])),
        "unreferenced_declared_source_ids": len(coverage.get("unreferenced_declared_source_ids", [])),
        "uncovered_evidence_checklist_ids": len(coverage.get("uncovered_evidence_checklist_ids", [])),
    }


def coverage_is_complete(report: dict[str, Any]) -> bool:
    if report["coverage"].get("missing_learning_dossier"):
        return False
    return all(
        not report["coverage"].get(key)
        for key in [
            "missing_source_references",
            "unknown_source_references",
            "missing_evidence_references",
            "unknown_evidence_references",
            "unreferenced_declared_source_ids",
            "uncovered_evidence_checklist_ids",
        ]
    )


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False) + "\n"


def render_human(report: dict[str, Any], validation_error: str | None = None) -> str:
    lines = [
        "dossier_evidence_coverage_report",
        f"source={report['source_path']}",
        f"packet_id={report['packet_id']}",
        f"dossier_id={report['dossier_id']}",
        f"boundary={report['boundary_statement']}",
        f"declared_source_ids={','.join(report['declared_source_ids'])}",
    ]
    for item in report["question_sources"]:
        lines.append(f"- question {item['question_id']} sources={','.join(item['source_ids'])}")
    if report["practice_task"]:
        task = report["practice_task"]
        lines.append(
            f"- practice_task {task['task_id']} sources={','.join(task['source_ids'])} "
            f"evidence_outputs={','.join(task['evidence_output_ids'])}"
        )
    for item in report["evidence_checklist"]:
        lines.append(f"- evidence {item['evidence_id']} sources={','.join(item['source_ids'])}")
    if report["review_gate"]:
        gate = report["review_gate"]
        lines.append(
            f"- review_gate {gate['gate_id']} status={gate['status']} "
            f"roles={','.join(gate['required_roles'])} evidence={','.join(gate['evidence_required_ids'])}"
        )
    counts = " ".join(f"{key}={value}" for key, value in report["counts"].items())
    lines.append(f"counts {counts}")
    lines.append(f"coverage_complete={str(coverage_is_complete(report)).lower()}")
    if validation_error:
        lines.append(f"validation_error={validation_error}")
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
        print(f"dossier_evidence_coverage_report=failed input={source_path} error={exc}", file=sys.stderr)
        return 1
    if not isinstance(doc, dict):
        print(
            f"dossier_evidence_coverage_report=failed input={source_path} error=top-level JSON must be object",
            file=sys.stderr,
        )
        return 1

    report = evidence_coverage_report(doc, source_path)
    validation_error = None
    try:
        validate_doc(doc, source_path.name)
    except AssertionError as exc:
        validation_error = str(exc)

    rendered_json = render_json(report)
    if args.check:
        if not args.check.exists():
            print(f"dossier_evidence_coverage_check=missing target={args.check}", file=sys.stderr)
            return 1
        checked_in = args.check.read_text(encoding="utf-8")
        if checked_in != rendered_json:
            print(f"dossier_evidence_coverage_check=stale target={args.check}", file=sys.stderr)
            return 1
        if validation_error:
            print(f"dossier_evidence_coverage_check=validation_failed error={validation_error}", file=sys.stderr)
            return 1
        if not coverage_is_complete(report):
            print(f"dossier_evidence_coverage_check=incomplete target={args.check}", file=sys.stderr)
            return 1
        print(f"dossier_evidence_coverage_check=ok target={args.check}")
        return 0

    rendered = rendered_json if args.format == "json" else render_human(report, validation_error)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if validation_error:
        print(f"dossier_evidence_coverage_report=validation_failed error={validation_error}", file=sys.stderr)
        return 1
    if not coverage_is_complete(report):
        print("dossier_evidence_coverage_report=incomplete", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
