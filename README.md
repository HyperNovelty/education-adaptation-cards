# iPublishOS / Agent OS Education Adaptation Cards

Local-only mock contract for attaching teacher, student, and assessment/gate education adaptation cards to iPublishOS / Agent OS review packets.

JSON schema and fixtures for AI-era education adaptation cards: source-bound learner questions, misconception evidence, assessment gates, and human review.

## Included

- `schemas/education_adaptation_cards.schema.json` — documentation-facing JSON Schema contract.
- `examples/education_cards.minimal.json` — smallest complete card lane fixture.
- `examples/education_cards.public_domain_folder_dossier.json` — complete folder-based learning dossier tied to a pre-1929 public-domain source.
- `examples/education_cards.review_packet_fixture.json` — fuller fixture referencing the existing Voice-to-Source review packet output.
- `examples/rendered/education_demo_dossier.md` — generated markdown demo from the review packet fixture.
- `examples/rendered/public_domain_learning_dossier.md` — generated markdown demo from the public-domain folder dossier fixture.
- `examples/rendered/public_domain_review_boundaries.json` — checked-in deterministic review-boundary report for the public-domain folder dossier.
- `examples/rendered/review_packet_review_boundaries.json` — checked-in deterministic review-boundary report for the review-packet fixture.
- `examples/rendered/minimal_review_boundaries.json` — checked-in deterministic review-boundary report for the minimal fixture.
- `examples/rendered/forbidden_authority_fields.json` — checked-in deterministic inventory of named future-authority fields that fail closed.
- `examples/invalid/assessment_gate_gradebook_write.json` — negative fixture proving assessment gates cannot add gradebook-write authority.
- `examples/invalid/card_lms_export.json` — negative fixture proving cards cannot add LMS export authority.
- `examples/invalid/dossier_classroom_deployment.json` — negative fixture proving dossiers cannot add classroom deployment authority.
- `examples/invalid/dossier_learning_mission_review_state_approved.json` — negative fixture proving dossier mission review state cannot move beyond local review.
- `examples/invalid/dossier_review_gate_status_approved.json` — negative fixture proving dossier review gates cannot move beyond local review.
- `examples/invalid/dossier_review_gate_without_evidence.json` — negative fixture proving dossier review gates must name required evidence.
- `examples/invalid/human_review_status_approved_card.json` — negative fixture proving local-review-only human review states are enforced.
- `examples/invalid/learner_question_source_bound_without_source_ids.json` — negative fixture proving source-bound learner questions must name source IDs.
- `examples/invalid/learner_questions_without_misconception_evidence.json` — negative fixture proving learner questions require misconception evidence.
- `examples/invalid/misconception_evidence_undeclared_source_id.json` — negative fixture proving misconception evidence source IDs must be declared by the card.
- `examples/invalid/packet_status_approved_internal_review.json` — negative fixture proving packet status cannot move beyond local review.
- `examples/invalid/packet_student_id.json` — negative fixture proving review packets cannot collect learner identity.
- `docs/education_adaptation_cards_contract.md` — implementation notes and review-packet integration guidance.
- `docs/DEMO_WALKTHROUGH.md` — plain-language reviewer walkthrough.
- `tests/validate_education_adaptation_cards.py` — Python standard-library validator; no third-party installs.
- `scripts/report_forbidden_authority_fields.py` — deterministic stdlib CLI that inventories and scans forbidden future-authority fields.
- `scripts/report_review_boundaries.py` — deterministic stdlib CLI that inventories packet, dossier, and card review states.
- `scripts/render_learning_dossier.py` — deterministic stdlib renderer for local markdown learning dossiers/review packets.

## Safety boundary

This prototype is local review material only. It does not publish, contact anyone, create accounts, install packages, call networks, integrate with an LMS, or collect student data.

The only allowed review authority states in runnable local fixtures are `draft_only` and `needs_human_review`. Packet status, dossier mission review state, dossier review gate status, and every card `human_review.status` fail closed if promoted beyond that boundary.

Named future-authority fields fail before generic key-mismatch checks. Fields for learner identity, student records, LMS export/sync/course IDs, classroom deployment, gradebook writes, automated grading, and auto-publish produce `forbidden_future_authority_field=<field>` with a specific reason.

The markdown renderer also fails closed before writing output: malformed JSON, non-object JSON, validation failures, and promoted review states exit nonzero with a labeled `render_boundary=failed` line. Successful renders do not add banners or extra sections beyond the deterministic dossier markdown.

Assessment artifacts are review aids, not grading automation, diagnosis, or student surveillance; see `docs/ASSESSMENT_BOUNDARY.md`.

Learner questions and misconception evidence are synthetic, source-bound review objects. Question and evidence source IDs must be unique and declared in the card's source binding. They are not student records, learner profiles, grading inputs, or classroom-clearance claims.

## Try it in 2 minutes

```bash
python3 tests/validate_education_adaptation_cards.py
python3 scripts/report_review_boundaries.py --input examples/education_cards.public_domain_folder_dossier.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.public_domain_folder_dossier.json --check examples/rendered/public_domain_review_boundaries.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.review_packet_fixture.json --check examples/rendered/review_packet_review_boundaries.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.minimal.json --check examples/rendered/minimal_review_boundaries.json
python3 scripts/report_forbidden_authority_fields.py --check examples/rendered/forbidden_authority_fields.json
python3 scripts/render_learning_dossier.py --input examples/education_cards.review_packet_fixture.json --output /tmp/education_demo_dossier.md
python3 scripts/render_learning_dossier.py --input examples/education_cards.public_domain_folder_dossier.json --output /tmp/public_domain_learning_dossier.md
sed -n '1,80p' /tmp/education_demo_dossier.md
```

For a guided review, see `docs/DEMO_WALKTHROUGH.md`.

## Verify

```bash
python3 -m json.tool schemas/education_adaptation_cards.schema.json >/tmp/education_adaptation_cards.schema.validated.json
python3 -m json.tool examples/education_cards.minimal.json >/tmp/education_cards.minimal.validated.json
python3 -m json.tool examples/education_cards.review_packet_fixture.json >/tmp/education_cards.review_packet_fixture.validated.json
python3 -m json.tool examples/education_cards.public_domain_folder_dossier.json >/tmp/education_cards.public_domain_folder_dossier.validated.json
python3 tests/validate_education_adaptation_cards.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/report_forbidden_authority_fields.py --check examples/rendered/forbidden_authority_fields.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.public_domain_folder_dossier.json --check examples/rendered/public_domain_review_boundaries.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.review_packet_fixture.json --check examples/rendered/review_packet_review_boundaries.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.minimal.json --check examples/rendered/minimal_review_boundaries.json
python3 scripts/render_learning_dossier.py --input examples/education_cards.public_domain_folder_dossier.json --check examples/rendered/public_domain_learning_dossier.md
```


## Development

Run the validators with:

```bash
python3 tests/validate_education_adaptation_cards.py
python3 scripts/report_forbidden_authority_fields.py
python3 scripts/report_forbidden_authority_fields.py --input examples/education_cards.minimal.json
python3 scripts/report_forbidden_authority_fields.py --check examples/rendered/forbidden_authority_fields.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.public_domain_folder_dossier.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.public_domain_folder_dossier.json --format json
python3 scripts/report_review_boundaries.py --input examples/education_cards.public_domain_folder_dossier.json --check examples/rendered/public_domain_review_boundaries.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.review_packet_fixture.json --check examples/rendered/review_packet_review_boundaries.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.minimal.json --check examples/rendered/minimal_review_boundaries.json
python3 scripts/render_learning_dossier.py examples/education_cards.review_packet_fixture.json
python3 scripts/render_learning_dossier.py examples/education_cards.public_domain_folder_dossier.json
python3 scripts/render_learning_dossier.py --input examples/education_cards.public_domain_folder_dossier.json --check examples/rendered/public_domain_learning_dossier.md
python3 tests/test_render_learning_dossier_smoke.py
```
