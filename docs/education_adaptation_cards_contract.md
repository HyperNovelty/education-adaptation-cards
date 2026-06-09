# Education Adaptation Cards Contract

Local-only implementation-facing mock contract for adding education adaptation cards to iPublishOS / Agent OS review packets.

## Boundary

- Work stays under `/home/aware1/.hermes/content-empire`.
- Artifacts are review-packet attachments, not classroom deployment artifacts.
- No network calls, third-party package installs, public publishing, LMS/account actions, credentials, outreach, or student data handling.
- All cards remain `draft_only` or `needs_human_review` until explicit human approval.

## Primary artifact

Schema:

`products/ipublishos_education_adaptation_cards/schemas/education_adaptation_cards.schema.json`

Fixtures:

- `examples/education_cards.minimal.json` — minimal complete lane with one teacher card, one student card, and one assessment/gate card.
- `examples/education_cards.review_packet_fixture.json` — fuller mock attachment targeting the existing Voice-to-Source review packet fixture.

## Contract shape

Top-level fields:

| Field | Meaning |
| --- | --- |
| `generated_at` | UTC-ish ISO timestamp for fixture generation. |
| `safety_mode` | Must be `local_review_only`. |
| `target_system` | `ipublishos`, `agent_os`, or `ipublishos_agent_os_bridge`. |
| `review_packet` | Local packet reference that cards attach to. |
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
| `source_binding` | Policy for limiting claims to packet sources. |
| `adaptation_actions` | Implementation-facing actions a renderer/builder may take. |
| `risks` | Known failure modes and mitigations. |
| `human_review` | Review status, required roles, and notes. |
| `outputs` | Intended review-packet output sections. |
| `assessment_gates` | Required for `assessment_gate_card`; omitted or empty for ordinary teacher/student cards. |

## Suggested renderer integration

1. Load the packet's existing source ledger or approved citation candidates.
2. Load an education card fixture conforming to this contract.
3. Verify exactly one `teacher_card`, one `student_card`, and one `assessment_gate_card`.
4. Render teacher/student sections only as draft review material.
5. Render the assessment/gate summary near the packet's top-level review decision area.
6. Block external/classroom release unless human review statuses are upgraded outside this local mock.

## Learning dossier extension

Added 2026-06-09 after Jordan approved the **Future of Education** monitoring/development track and the angle **The Next Classroom May Be a Folder**.

Use this extension when adapting iPublishOS review packets into teaching/workbook/course material. The core pattern is:

`Source Packet → Mission → Question Map → Lesson Unit → Reference Sheet → Practice Task → Evidence Packet → Human Review Gate`

Recommended future card type or companion object:

- `learning_dossier_card` or `proof_of_learning_card`

Required verification concepts for that future card:

- learner mission / why this lesson exists;
- source-to-lesson trace;
- likely misconceptions;
- practice task;
- expected evidence;
- rubric / competence level;
- human reviewer role;
- release status.

Boundary: this does **not** authorize LMS integration, student data collection, grading, account actions, classroom deployment, or public education claims. It is a local review-packet pattern until separately approved.

## Local verification

Run from `products/ipublishos_education_adaptation_cards`:

```bash
python3 -m json.tool schemas/education_adaptation_cards.schema.json >/tmp/education_adaptation_cards.schema.validated.json
python3 -m json.tool examples/education_cards.minimal.json >/tmp/education_cards.minimal.validated.json
python3 -m json.tool examples/education_cards.review_packet_fixture.json >/tmp/education_cards.review_packet_fixture.validated.json
python3 tests/validate_education_adaptation_cards.py
```

The validator intentionally uses only the Python standard library. It is not a general JSON Schema engine; it validates this prototype's current schema markers, fixture structure, local path boundary, complete card-type set, review states, and assessment gate requirements.
