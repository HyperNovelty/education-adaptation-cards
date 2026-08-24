#!/usr/bin/env python3
"""Report local-only review boundary states for an education card fixture."""
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

from education_adaptation_cards import (
    LOCAL_REVIEW_ONLY_STATUSES,
    LOCAL_REVIEW_ONLY_STATUS_ORDER,
    card_sort_key,
    load_json,
    validate_doc,
)


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def status_result(status: Any) -> str:
    return "pass" if status in LOCAL_REVIEW_ONLY_STATUSES else "violation"


def make_item(label: str, location: str, status: Any) -> dict[str, Any]:
    return {
        "label": label,
        "location": location,
        "observed_status": status,
        "allowed_statuses": LOCAL_REVIEW_ONLY_STATUS_ORDER,
        "result": status_result(status),
    }


def report_review_boundaries(doc: dict[str, Any], source_path: Path) -> dict[str, Any]:
    packet = doc.get("review_packet", {})
    items = [
        make_item(
            "review_packet.packet_status",
            "review_packet.packet_status",
            packet.get("packet_status") if isinstance(packet, dict) else None,
        )
    ]

    dossier = doc.get("learning_dossier")
    if isinstance(dossier, dict):
        mission = dossier.get("learning_mission", {})
        gate = dossier.get("review_gate", {})
        items.extend(
            [
                make_item(
                    "learning_dossier.learning_mission.review_state",
                    "learning_dossier.learning_mission.review_state",
                    mission.get("review_state") if isinstance(mission, dict) else None,
                ),
                make_item(
                    "learning_dossier.review_gate.status",
                    "learning_dossier.review_gate.status",
                    gate.get("status") if isinstance(gate, dict) else None,
                ),
            ]
        )

    indexed_cards = []
    cards = doc.get("education_adaptation_cards", [])
    if isinstance(cards, list):
        for idx, card in enumerate(cards):
            if not isinstance(card, dict):
                continue
            try:
                sort_key = card_sort_key(card)
            except (KeyError, ValueError):
                sort_key = (len(LOCAL_REVIEW_ONLY_STATUS_ORDER), str(card.get("card_id", idx)))
            indexed_cards.append((sort_key, idx, card))

    for _, idx, card in sorted(indexed_cards):
        card_id = card.get("card_id", f"index_{idx}")
        review = card.get("human_review", {})
        items.append(
            make_item(
                f"card:{card_id}.human_review.status",
                f"education_adaptation_cards[{idx}].human_review.status",
                review.get("status") if isinstance(review, dict) else None,
            )
        )

    return {
        "report_type": "education_adaptation_cards.review_boundaries",
        "source_path": display_path(source_path),
        "allowed_authority": "local_review_only",
        "items": items,
        "summary": {
            "total": len(items),
            "pass": sum(1 for item in items if item["result"] == "pass"),
            "violations": sum(1 for item in items if item["result"] == "violation"),
        },
    }


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False) + "\n"


def render_human(report: dict[str, Any], validation_error: str | None = None) -> str:
    lines = [
        "review_boundary_report",
        f"source={report['source_path']}",
        f"allowed_authority={report['allowed_authority']}",
    ]
    for item in report["items"]:
        lines.append(
            f"- {item['result']}: {item['label']} "
            f"location={item['location']} observed={item['observed_status']!r} "
            f"allowed={','.join(item['allowed_statuses'])}"
        )
    summary = report["summary"]
    lines.append(
        f"summary total={summary['total']} pass={summary['pass']} violations={summary['violations']}"
    )
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
        print(f"review_boundary_report=failed input={source_path} error={exc}", file=sys.stderr)
        return 1
    if not isinstance(doc, dict):
        print(f"review_boundary_report=failed input={source_path} error=top-level JSON must be object", file=sys.stderr)
        return 1

    report = report_review_boundaries(doc, source_path)
    validation_error = None
    try:
        validate_doc(doc, source_path.name)
    except AssertionError as exc:
        validation_error = str(exc)

    rendered_json = render_json(report)
    if args.check:
        if not args.check.exists():
            print(f"review_boundary_check=missing target={args.check}", file=sys.stderr)
            return 1
        checked_in = args.check.read_text(encoding="utf-8")
        if checked_in != rendered_json:
            print(f"review_boundary_check=stale target={args.check}", file=sys.stderr)
            return 1
        if validation_error:
            print(f"review_boundary_check=validation_failed error={validation_error}", file=sys.stderr)
            return 1
        print(f"review_boundary_check=ok target={args.check}")
        return 0

    rendered = rendered_json if args.format == "json" else render_human(report, validation_error)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if report["summary"]["violations"]:
        print(f"review_boundary_report=violations count={report['summary']['violations']}", file=sys.stderr)
        return 1
    if validation_error:
        print(f"review_boundary_report=validation_failed error={validation_error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
