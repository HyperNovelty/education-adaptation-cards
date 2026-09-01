# Demo Walkthrough

This repository shows a small local pattern for reviewing education adaptation
cards. It uses synthetic data only. It does not handle student data, issue
grades, connect to an LMS, publish anything, or make compliance claims.

## What to Look At First

Start with `examples/education_cards.review_packet_fixture.json`. It is a fuller
sample fixture that attaches three education cards to a draft review packet:

- a teacher card for source-locked lesson planning
- a student card for guided source checking
- an assessment/gate card for reviewer checks before any education-facing use

The fixture is deliberately labeled `local_review_only` and `draft_only`. Its
review statuses stay at `needs_human_review`, so the sample is useful as review
material but not as classroom approval.

Then open `examples/education_cards.public_domain_folder_dossier.json`. It adds
a top-level folder dossier around a clearly identified public-domain source:
Lewis Carroll's 1865 `Alice's Adventures in Wonderland`, referenced by Project
Gutenberg URL with a short excerpt only. The folder dossier makes the mission,
source/reference sheet, question map, practice task, evidence checklist, and
review gate visible before the three-card lane.

## Review the Boundary Surface

Run:

```bash
python3 scripts/report_review_boundaries.py --input examples/education_cards.public_domain_folder_dossier.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.public_domain_folder_dossier.json --check examples/rendered/public_domain_review_boundaries.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.review_packet_fixture.json --check examples/rendered/review_packet_review_boundaries.json
python3 scripts/report_review_boundaries.py --input examples/education_cards.minimal.json --check examples/rendered/minimal_review_boundaries.json
```

The report inventories packet status, dossier mission review state, dossier
review gate status, and each card's human review status. Every listed state must
be `draft_only` or `needs_human_review`; promoted states fail closed and are
reported as violations.

Then inspect the named future-authority inventory:

```bash
python3 scripts/report_forbidden_authority_fields.py
python3 scripts/report_forbidden_authority_fields.py --check examples/rendered/forbidden_authority_fields.json
```

Those names are reserved for unsupported authority layers: learner identity,
student records, LMS fields, classroom deployment, gradebook writes, automated
grading, and auto-publish. If a fixture includes one, validation fails with
`forbidden_future_authority_field=<field>` before generic key validation.

## What the Validator Checks

Run:

```bash
python3 tests/validate_education_adaptation_cards.py
```

The validator uses only the Python standard library. It checks the project's
current contract markers, including:

- the schema is the expected draft marker
- fixture safety mode is `local_review_only`
- each valid fixture has exactly one teacher card, one student card, and one
  assessment/gate card
- human review states remain review-only
- assessment gates are present where required
- folder dossiers, when present, link questions, practice tasks, evidence
  checklist items, and review-gate evidence IDs to declared sources/evidence
- named future-authority fields fail with specific forbidden-field reasons
- invalid fixtures fail for clear local-review reasons

It is not a general compliance checker or curriculum approval engine.

## What the Renderer Does

Run:

```bash
python3 scripts/render_learning_dossier.py --input examples/education_cards.review_packet_fixture.json --output /tmp/education_demo_dossier.md
python3 scripts/render_learning_dossier.py --input examples/education_cards.public_domain_folder_dossier.json --output /tmp/public_domain_learning_dossier.md
python3 scripts/render_learning_dossier.py --input examples/education_cards.public_domain_folder_dossier.json --check examples/rendered/public_domain_learning_dossier.md
```

The renderer converts the fixture into deterministic Markdown. It preserves the
review packet context, safety mode, card purposes, source-binding rules, risks,
human review notes, outputs, assessment gates, and any top-level folder dossier
metadata.

The renderer validates before writing markdown. Malformed JSON, non-object JSON,
ordinary validation failures, and promoted review states exit nonzero with a
labeled `render_boundary=failed` line; promoted states use the same packet,
dossier, gate, and card labels as the review-boundary report.

A checked-in demo render is available at
`examples/rendered/education_demo_dossier.md`. It is generated from
`examples/education_cards.review_packet_fixture.json` only.

A public-domain folder demo render is available at
`examples/rendered/public_domain_learning_dossier.md`. It is generated from
`examples/education_cards.public_domain_folder_dossier.json`.

## How to Review in 90 Seconds

1. Open the fixture and confirm it is synthetic and `local_review_only`.
2. Run the validator and confirm both valid and invalid examples behave as
   expected.
3. Open the public-domain fixture and confirm the source sheet identifies title,
   creator, publication year, public-domain basis, URL, and minimal excerpt.
4. Run the review-boundary report and confirm every packet, dossier, gate, and
   card state remains local-only.
5. Run the forbidden-authority inventory check and confirm it is fresh.
6. Open the rendered dossier and confirm it says local review material only, not
   classroom-cleared, and no LMS/network/account/publish/student-data actions are
   authorized.
7. Optionally run an invalid fixture through the renderer and confirm it reports
   `render_boundary=failed` without writing markdown.

That is the whole demo: a small fixture contract, a local validator, a
review-boundary inventory, a forbidden-authority inventory, and a deterministic
renderer for reviewer inspection.
