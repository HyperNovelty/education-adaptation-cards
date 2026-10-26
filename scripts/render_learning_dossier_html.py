#!/usr/bin/env python3
"""Render a deterministic, self-contained HTML learning-dossier review packet."""
from __future__ import annotations

import argparse
from html import escape
import os
import sys
import tempfile
from json import JSONDecodeError
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from education_adaptation_cards import card_sort_key, load_json, validate_doc
from scripts.report_review_boundaries import report_review_boundaries


def h(value: Any) -> str:
    """Escape a fixture value for HTML text or an attribute."""
    return escape(str(value), quote=True)


def text(value: Any) -> str:
    return f"<p>{h(value)}</p>"


def item(label: str, value: Any) -> str:
    return f"<div class=\"field\"><dt>{h(label)}</dt><dd>{h(value)}</dd></div>"


def list_items(values: list[Any]) -> str:
    return "".join(f"<li>{h(value)}</li>" for value in values)


def source_ids(values: list[str]) -> str:
    return ", ".join(str(value) for value in values) or "none"


def render_learning_dossier(dossier: dict[str, Any]) -> str:
    mission = dossier["learning_mission"]
    task = dossier["practice_task"]
    gate = dossier["review_gate"]
    sections = [
        f"<section><h2>Folder-Based Learning Dossier</h2><dl>{item('Dossier ID', dossier['dossier_id'])}{item('Dossier title', dossier['dossier_title'])}</dl>",
        "<h3>Folder layout</h3><ul>" + list_items(dossier["folder_layout"]) + "</ul>",
        f"<h3>Learning Mission</h3><dl>{item('Mission ID', mission['mission_id'])}{item('Audience', mission['audience'])}{item('Review state', mission['review_state'])}{item('Objective', mission['objective'])}</dl></section>",
        "<section><h2>Source/Reference Sheet</h2>",
    ]
    for source in dossier["source_reference_sheet"]:
        sections.append(
            f"<article class=\"source-card\"><h3><span class=\"id\">{h(source['source_id'])}</span> {h(source['title'])}</h3>"
            f"<dl>{item('Creator', source['creator'])}{item('Publication year', source['publication_year'])}{item('Public-domain status', source['public_domain_status'])}{item('Public-domain basis', source['public_domain_basis'])}{item('Source URL (plain text)', source['url'])}</dl>"
            f"<h4>Minimal excerpt</h4>{text(source['excerpt'])}</article>"
        )
    sections.append("</section><section><h2>Question Map</h2>")
    for question in dossier["question_map"]:
        sections.append(
            f"<article><h3><span class=\"id\">{h(question['question_id'])}</span></h3>{text(question['question'])}"
            f"<dl>{item('Source IDs', source_ids(question['source_ids']))}{item('Reviewer note', question['reviewer_note'])}</dl></article>"
        )
    sections.append(
        f"</section><section><h2>Practice Task</h2><dl>{item('Task ID', task['task_id'])}{item('Prompt', task['prompt'])}{item('Source IDs', source_ids(task['source_ids']))}{item('Evidence output IDs', source_ids(task['evidence_output_ids']))}{item('Reviewer note', task['reviewer_note'])}</dl></section>"
    )
    sections.append("<section><h2>Evidence Checklist</h2>")
    for evidence in dossier["evidence_checklist"]:
        sections.append(
            f"<article><h3><span class=\"id\">{h(evidence['evidence_id'])}</span> {h(evidence['evidence_item'])}</h3>"
            f"<dl>{item('Source IDs', source_ids(evidence['source_ids']))}{item('Reviewer note', evidence['reviewer_note'])}</dl></article>"
        )
    sections.append(
        f"</section><section><h2>Review Gate</h2><dl>{item('Gate ID', gate['gate_id'])}{item('Status', gate['status'])}{item('Required roles', source_ids(gate['required_roles']))}{item('Evidence required IDs', source_ids(gate['evidence_required_ids']))}{item('Reviewer note', gate['reviewer_note'])}</dl></section>"
    )
    return "".join(sections)


def render_card(card: dict[str, Any]) -> str:
    parts = [
        f"<section><h2>{h(card['title'])}</h2><div class=\"card-meta\"><span class=\"id\">{h(card['card_id'])}</span> · {h(card['card_type'])} · audience {h(card['audience'])} · grade band {h(card.get('grade_band', 'unspecified'))}</div>",
        "<h3>Purpose</h3>" + text(card["purpose"]),
        f"<h3>Source Binding</h3><dl>{item('Source policy', card['source_binding']['source_policy'])}{item('Allowed source IDs', source_ids(card['source_binding']['allowed_source_ids']))}{item('Blocked claims policy', card['source_binding']['blocked_claims_policy'])}</dl>",
        "<h3>Adaptation Actions</h3><ul>" + list_items(card["adaptation_actions"]) + "</ul>",
        "<h3>Risks</h3>",
    ]
    for risk in card["risks"]:
        parts.append(f"<article><h4><span class=\"id\">{h(risk['risk_id'])}</span> · {h(risk['risk_level'])}</h4>{text(risk['risk_text'])}<dl>{item('Mitigation', risk['mitigation'])}</dl></article>")
    review = card["human_review"]
    parts.append(f"<h3>Human Review</h3><dl>{item('Status', review['status'])}{item('Required roles', source_ids(review['required_roles']))}</dl><h4>Review notes</h4><ul>{list_items(review['review_notes'])}</ul>")
    parts.append("<h3>Outputs</h3><ul>" + "".join(f"<li><span class=\"id\">{h(output['output_id'])}</span> · {h(output['output_type'])}: {h(output['description'])}</li>" for output in card["outputs"]) + "</ul>")
    questions = card.get("learner_questions", [])
    if questions:
        parts.append("<h3>Learner Questions</h3>")
        for question in questions:
            parts.append(f"<article><h4><span class=\"id\">{h(question['question_id'])}</span> · {h(question['question_status'])}</h4>{text(question['question_text'])}<dl>{item('Source IDs', source_ids(question['source_ids']))}{item('Reviewer note', question['reviewer_note'])}</dl></article>")
    evidence = card.get("misconception_evidence", [])
    if evidence:
        parts.append("<h3>Misconception Evidence</h3>")
        for entry in evidence:
            parts.append(f"<article><h4><span class=\"id\">{h(entry['misconception_id'])}</span> · {h(entry['severity'])}</h4>{text(entry['misconception_text'])}<dl>{item('Evidence signal', entry['evidence_signal'])}{item('Source IDs', source_ids(entry['source_ids']))}{item('Teacher response', entry['teacher_response'])}{item('Reviewer note', entry['reviewer_note'])}</dl></article>")
    gates = card.get("assessment_gates", [])
    if gates:
        parts.append("<h3>Assessment Gates</h3>")
        for gate in gates:
            parts.append(f"<article><h4><span class=\"id\">{h(gate['gate_id'])}</span> · {h(gate['gate_status'])}</h4><p>{h(gate['gate_name'])}</p><h4>Evidence required</h4><ul>{list_items(gate['evidence_required'])}</ul></article>")
    parts.append("</section>")
    return "".join(parts)


def render_html(doc: dict[str, Any], source_path: Path) -> str:
    validate_doc(doc, source_path.name)
    dossier = doc.get("learning_dossier")
    if not isinstance(dossier, dict):
        raise AssertionError("learning_dossier is required for HTML rendering")
    packet = doc["review_packet"]
    cards = sorted(doc["education_adaptation_cards"], key=card_sort_key)
    try:
        source_label = source_path.relative_to(ROOT)
    except ValueError:
        source_label = source_path
    sections = [
        f"<header><p class=\"eyebrow\">OFFLINE HTML REVIEW PACKET</p><h1>{h(packet['packet_title'])}</h1><p class=\"boundary\">Local review only. Not classroom-cleared. No LMS, network, account, publish, student-data, grading, or deployment action is authorized by this artifact.</p></header>",
        f"<section><h2>Packet Metadata</h2><dl>{item('Source fixture', source_label)}{item('Generated at', doc['generated_at'])}{item('Safety mode', doc['safety_mode'])}{item('Target system', doc['target_system'])}{item('Packet ID', packet['packet_id'])}{item('Packet title', packet['packet_title'])}{item('Packet path', packet['packet_path'])}{item('Packet status', packet['packet_status'])}</dl></section>",
        "<section><h2>Review Boundary</h2><p>This packet is a deterministic, repository-local reviewer surface. Statuses and roles are shown as supplied; this renderer does not invent verdicts, collect responses, or promote review states.</p></section>",
        render_learning_dossier(dossier),
    ]
    sections.extend(render_card(card) for card in cards)
    css = """*{box-sizing:border-box}body{margin:0;background:#f4f1ea;color:#20252a;font:16px/1.55 Georgia,serif}main{max-width:1100px;margin:0 auto;padding:2rem 1.25rem 4rem}header,section,article{background:#fffdf8;border:1px solid #d8d1c4;border-radius:8px;padding:1.25rem;margin:0 0 1rem;box-shadow:0 2px 8px #20252a12}header{border-top:8px solid #315c58}.eyebrow,.id,.card-meta{font:600 .78rem/1.3 Consolas,monospace;letter-spacing:.04em}.eyebrow{color:#315c58}.boundary{background:#fff1c9;border-left:4px solid #b77718;padding:.75rem}h1,h2,h3,h4{font-family:Arial,sans-serif;line-height:1.2}h1{font-size:2.1rem}h2{color:#315c58;border-bottom:1px solid #ded7ca;padding-bottom:.4rem}h3{margin-top:1.3rem}h4{margin-bottom:.25rem}.card-meta,.id{color:#694f2e}.field{display:grid;grid-template-columns:minmax(10rem,25%) 1fr;gap:.75rem;border-bottom:1px solid #eee8dc;padding:.35rem 0}.field:last-child{border-bottom:0}dt{font-weight:bold}dd{margin:0;overflow-wrap:anywhere}ul{padding-left:1.5rem}.source-card{border-left:4px solid #739b82}article{background:#fffefa;box-shadow:none}p{margin:.6rem 0}@media print{body{background:white}main{max-width:none;padding:.25in}section,article,header{break-inside:avoid;box-shadow:none}}"""
    return "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n<title>" + h(packet["packet_title"]) + "</title>\n<style>" + css + "</style>\n</head>\n<body><main>" + "".join(sections) + "</main></body>\n</html>\n"


def failure_line(source_path: Path, reason: str, detail: str) -> str:
    return f"html_render=failed input={source_path} reason={reason} detail={detail}"


def write_output_atomically(output_path: Path, rendered: str) -> None:
    """Write rendered HTML via a same-directory temporary file and replacement."""
    output_path = output_path.resolve()
    temporary_path: Path | None = None
    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(rendered)
            handle.flush()
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def load_valid_doc(source_path: Path) -> dict[str, Any] | None:
    try:
        doc = load_json(source_path)
    except (OSError, UnicodeDecodeError, JSONDecodeError) as exc:
        print(failure_line(source_path, "json_load_failed", str(exc)), file=sys.stderr)
        return None
    if not isinstance(doc, dict):
        print(failure_line(source_path, "top_level_json_not_object", "top-level JSON must be object"), file=sys.stderr)
        return None
    try:
        validate_doc(doc, source_path.name)
        if not isinstance(doc.get("learning_dossier"), dict):
            raise AssertionError("learning_dossier is required for HTML rendering")
        boundary = report_review_boundaries(doc, source_path)
        violation = next((entry for entry in boundary["items"] if entry["result"] == "violation"), None)
        if violation:
            raise AssertionError(f"review_boundary_violation={violation['location']} status={violation['observed_status']}")
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        print(failure_line(source_path, "validation_failed", str(exc)), file=sys.stderr)
        return None
    return doc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, dest="input_path")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path)
    group.add_argument("--check", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = args.input_path.resolve()
    doc = load_valid_doc(source_path)
    if doc is None:
        return 1
    try:
        rendered = render_html(doc, source_path)
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        print(failure_line(source_path, "render_failed", str(exc)), file=sys.stderr)
        return 1
    if args.check:
        if not args.check.exists():
            print(f"html_render_check=missing target={args.check}", file=sys.stderr)
            return 1
        try:
            checked_in = args.check.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"html_render_check=failed target={args.check} detail={exc}", file=sys.stderr)
            return 1
        if checked_in != rendered:
            print(f"html_render_check=stale target={args.check}", file=sys.stderr)
            return 1
        print(f"html_render_check=ok target={args.check}")
        return 0
    if args.output:
        try:
            write_output_atomically(args.output, rendered)
        except (OSError, UnicodeError) as exc:
            print(failure_line(source_path, "output_write_failed", str(exc)), file=sys.stderr)
            return 1
        print(f"html_render=ok output={args.output}")
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
