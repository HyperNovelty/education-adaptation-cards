# Education Adaptation Cards Contract

Local-only implementation-facing mock contract for adding education adaptation cards to iPublishOS / Agent OS review packets.

## Boundary

- Work stays inside this repository checkout.
- Artifacts are review-packet attachments, not classroom deployment artifacts.
- No network calls, third-party package installs, public publishing, LMS/account actions, credentials, outreach, or student data handling.
- Packet, dossier, review-gate, and card human-review states remain `draft_only` or `needs_human_review`. This repository does not promote, approve, publish, or clear artifacts for classroom use.

## Primary artifact

Schema:

`schemas/education_adaptation_cards.schema.json`

Fixtures:

- `examples/education_cards.minimal.json` — minimal complete lane with one teacher card, one student card, and one assessment/gate card.
- `examples/education_cards.public_domain_folder_dossier.json` — complete folder-based dossier using a pre-1929 public-domain text source.
- `examples/education_cards.review_packet_fixture.json` — fuller mock attachment targeting the existing Voice-to-Source review packet fixture.
- `examples/rendered/public_domain_review_boundaries.json` — deterministic JSON report generated from the public-domain fixture for freshness checks.

## Contract shape

Top-level fields:

| Field | Meaning |
| --- | --- |
| `generated_at` | UTC-ish ISO timestamp for fixture generation. |
| `safety_mode` | Must be `local_review_only`. |
| `target_system` | `ipublishos`, `agent_os`, or `ipublishos_agent_os_bridge`. |
| `review_packet` | Local packet reference that cards attach to. |
| `learning_dossier` | Optional strict folder-based dossier metadata. Required sections are mission, source/reference sheet, question map, practice task, evidence checklist, and review gate. |
| `education_adaptation_cards` | Array of card objects. A complete lane has exactly one teacher, one student, and one assessment/gate card. |

Required card fields:

| Field | Meaning |
| --- | --- |
| `card_id` | Stable local slug. |
| `card_type` | `teacher_card`, `student_card`, or `assessment_gate_card`. |
| `title` | Reviewer-facing card title. |
| `audience` | Primary audience for rendering/review. |
| `grade_band` | Coarse education/learner band; can be `unspecified`. |
| `purpose` | What the card is supposed to do. |
| `source_binding` | Policy for limiting claims to packet sources. `allowed_source_ids` must not contain duplicates. |
| `adaptation_actions` | Implementation-facing actions a renderer/builder may take. |
| `risks` | Known failure modes and mitigations. |
| `human_review` | Review status, required roles, and notes. |
| `outputs` | Intended review-packet output sections. |
| `learner_questions` | Optional source-bound learner questions for local review. If present, the card must also include `misconception_evidence`. |
| `misconception_evidence` | Optional evidence signals for likely misconceptions, with source IDs, severity, teacher response, and reviewer note. Required when `learner_questions` is present. |
| `assessment_gates` | Required for `assessment_gate_card`; omitted or empty for ordinary teacher/student cards. |

Learner question fields:

| Field | Meaning |
| --- | --- |
| `question_id` | Stable local slug. |
| `question_text` | Reviewer-facing unresolved or source-check question. |
| `question_status` | `unanswered`, `partially_sourced`, `source_bound`, or `out_of_scope`. |
| `source_ids` | Unique packet source IDs declared in the same card's `source_binding.allowed_source_ids`. Required for `source_bound` and `partially_sourced`; must be empty for `unanswered` and `out_of_scope`. |
| `reviewer_note` | Local reviewer note. Do not include learner identity or student data. |

Misconception evidence fields:

| Field | Meaning |
| --- | --- |
| `misconception_id` | Stable local slug. |
| `misconception_text` | Likely misconception phrased for teacher/reviewer planning, not a finding about a real learner. |
| `evidence_signal` | Source-bound signal that explains why the misconception should be reviewed. |
| `source_ids` | One or more unique packet source IDs supporting the evidence signal; every ID must be declared in the same card's `source_binding.allowed_source_ids`. |
| `severity` | `low`, `medium`, `high`, or `unknown`. |
| `teacher_response` | Suggested teacher/reviewer response. |
| `reviewer_note` | Local reviewer note. Do not include learner identity or student data. |

## Suggested renderer integration

1. Load the packet's existing source ledger or approved citation candidates.
2. Load an education card fixture conforming to this contract.
3. Verify exactly one `teacher_card`, one `student_card`, and one `assessment_gate_card`.
4. Render teacher/student sections only as draft review material.
5. Render the assessment/gate summary near the packet's top-level review decision area.
6. Block external/classroom release; this local mock only reports whether states remain within `local_review_only`.

## Review-boundary report

Run from the repository root:

```bash
python3 scripts/report_review_boundaries.py --input examples/education_cards.public_domain_folder_dossier.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.public_domain_folder_dossier.json --format json
python3 scripts/report_review_boundaries.py --input examples/education_cards.public_domain_folder_dossier.json --check examples/rendered/public_domain_review_boundaries.json
```

The report inventories `review_packet.packet_status`, optional `learning_dossier.learning_mission.review_state`, optional `learning_dossier.review_gate.status`, and each card's `human_review.status` in deterministic reviewer order. Each item includes a label, location, observed status, allowed status set, and pass/violation result. The command exits nonzero for malformed JSON, stale checked-in JSON, validation failures, or any state outside `draft_only` and `needs_human_review`.

## Learning dossier extension

Added 2026-06-09 after Jordan approved the **Future of Education** monitoring/development track and the angle **The Next Classroom May Be a Folder**.

Use this extension when adapting iPublishOS review packets into teaching/workbook/course material. The core pattern is:

`Source Packet → Mission → Question Map → Lesson Unit → Reference Sheet → Practice Task → Evidence Packet → Human Review Gate`

The implemented companion object is the top-level `learning_dossier` block. It is additive: older fixtures without it remain valid, but fixtures that include it must provide every required section.

Required folder dossier fields:

| Field | Meaning |
| --- | --- |
| `dossier_id` | Stable local slug for the folder dossier. |
| `dossier_title` | Reviewer-facing folder title. |
| `folder_layout` | Deterministic list of folder files such as `mission.md`, `source_reference_sheet.md`, `question_map.md`, `practice_task.md`, `evidence_checklist.md`, and `review_gate.md`. |
| `learning_mission` | Mission ID, audience, objective, and local-only review state. |
| `source_reference_sheet` | One or more explicit sources with source ID, title, creator, publication year, public-domain status/basis, URL, and a minimal excerpt. |
| `question_map` | Source-bound questions with reviewer notes. |
| `practice_task` | Local practice prompt with source IDs and evidence output IDs. |
| `evidence_checklist` | Evidence IDs and checklist items that reviewers can inspect without storing student records. |
| `review_gate` | Local-only status, required human roles, and required evidence IDs. |

Validation links `question_map`, `practice_task`, `evidence_checklist`, and `review_gate` to declared source/evidence IDs. A dossier review gate cannot silently omit evidence: `review_gate.evidence_required_ids` must be non-empty and must reference checklist entries.

Boundary: this does **not** authorize LMS integration, student data collection, grading, account actions, classroom deployment, or public education claims. It is a local review-packet pattern until separately approved.

## Local verification

Run from the repository root:

```bash
python3 -m json.tool schemas/education_adaptation_cards.schema.json >/tmp/education_adaptation_cards.schema.validated.json
python3 -m json.tool examples/education_cards.minimal.json >/tmp/education_cards.minimal.validated.json
python3 -m json.tool examples/education_cards.review_packet_fixture.json >/tmp/education_cards.review_packet_fixture.validated.json
python3 -m json.tool examples/education_cards.public_domain_folder_dossier.json >/tmp/education_cards.public_domain_folder_dossier.validated.json
python3 tests/validate_education_adaptation_cards.py
```

The validator and review-boundary reporter intentionally use only the Python standard library. They are not general JSON Schema or compliance engines; they validate this prototype's current schema markers, fixture structure, repo-local path boundary, complete card-type set, local-only review states, learner-question/misconception-evidence coupling, card-level source-binding uniqueness and source-reference declarations, dossier source/evidence links, blocked public-safety claims, and assessment gate requirements.
