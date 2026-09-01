#!/usr/bin/env python3
"""Report forbidden future authority fields for education card fixtures."""
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

from education_adaptation_cards import FORBIDDEN_FUTURE_AUTHORITY_FIELDS, find_forbidden_future_authority_fields, load_json


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def inventory() -> dict[str, Any]:
    return {
        "report_type": "education_adaptation_cards.forbidden_future_authority_fields",
        "fields": [
            {"field": field, "reason": FORBIDDEN_FUTURE_AUTHORITY_FIELDS[field]}
            for field in sorted(FORBIDDEN_FUTURE_AUTHORITY_FIELDS)
        ],
    }


def render_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def scan_fixture(path: Path) -> dict[str, Any]:
    doc = load_json(path)
    findings = find_forbidden_future_authority_fields(doc, path.name)
    return {
        "report_type": "education_adaptation_cards.forbidden_future_authority_scan",
        "source_path": display_path(path),
        "findings": findings,
        "summary": {"forbidden_fields": len(findings)},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Print forbidden field inventory")
    parser.add_argument("--check", type=Path, help="Compare forbidden field inventory to a checked-in JSON file")
    parser.add_argument("--input", type=Path, help="Scan one fixture and exit 1 if forbidden fields are present")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.input:
        source_path = args.input.resolve()
        try:
            rendered = render_json(scan_fixture(source_path))
        except (OSError, JSONDecodeError) as exc:
            print(f"forbidden_authority_scan=failed input={source_path} error={exc}", file=sys.stderr)
            return 1
        print(rendered, end="")
        report = json.loads(rendered)
        if report["summary"]["forbidden_fields"]:
            print(
                f"forbidden_authority_scan=forbidden_fields count={report['summary']['forbidden_fields']}",
                file=sys.stderr,
            )
            return 1
        return 0

    rendered = render_json(inventory())
    if args.check:
        target = args.check
        if not target.exists():
            print(f"forbidden_authority_check=missing target={target}", file=sys.stderr)
            return 1
        checked_in = target.read_text(encoding="utf-8")
        try:
            checked_object = json.loads(checked_in)
        except JSONDecodeError as exc:
            print(f"forbidden_authority_check=invalid_json target={target} error={exc}", file=sys.stderr)
            return 1
        if checked_object != inventory() or checked_in != rendered:
            print(f"forbidden_authority_check=stale target={target}", file=sys.stderr)
            return 1
        print(f"forbidden_authority_check=ok target={target}")
        return 0

    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
