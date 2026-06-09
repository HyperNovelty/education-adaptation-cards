#!/usr/bin/env python3
"""Render a deterministic local learning dossier from a card fixture."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from education_adaptation_cards import CARD_RENDER_ORDER, load_json, validate_doc


def card_sort_key(card: dict[str, Any]) -> tuple[int, str]:
    return (CARD_RENDER_ORDER.index(card["card_type"]), card["card_id"])


def render_bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def render_indented_bullets(items: list[str]) -> list[str]:
    return [f"  - {item}" for item in items]


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
    for card in cards:
        lines.extend(render_card(card))
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="Path to an education adaptation card JSON fixture")
    parser.add_argument("-o", "--output", type=Path, help="Write markdown to a file instead of stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture = args.fixture.resolve()
    doc = load_json(fixture)
    rendered = render_dossier(doc, fixture)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
