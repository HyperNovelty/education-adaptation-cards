# Changelog

## 2026-09-01

- Added a validator-level forbidden future-authority field scan that fails before generic key checks for learner identity, student records, LMS fields, classroom deployment, gradebook writes, automated grading, and auto-publish.
- Added public-safe invalid fixtures for packet `student_id`, card `lms_export`, dossier `classroom_deployment`, and assessment-gate `gradebook_write`.
- Added `scripts/report_forbidden_authority_fields.py` and a checked-in deterministic inventory at `examples/rendered/forbidden_authority_fields.json`.

## 2026-08-31

- Hardened `scripts/render_learning_dossier.py` to fail closed with labeled `render_boundary=failed` output for malformed JSON, non-object JSON, validation failures, and promoted review-boundary states before any markdown write or check mutation.
- Added checked-in deterministic review-boundary JSON reports for the review-packet and minimal fixtures.
- Added unittest renderer/report regressions covering promoted packet, dossier mission, dossier gate, and card states plus freshness checks for all checked-in boundary reports and the public-domain markdown render.

## 2026-08-24

- Added `scripts/report_review_boundaries.py`, a stdlib CLI that inventories local-only packet, dossier, review-gate, and card human-review states with human or deterministic JSON output.
- Added a checked-in public-domain review-boundary JSON report plus check mode for freshness validation.
- Added public-safe invalid fixtures and regression tests for promoted packet status, dossier mission review state, and dossier review-gate status.

## 2026-08-03

- Hardened local validation for learner-question and misconception-evidence source bindings, including duplicate source IDs, status/source consistency, and undeclared card source references.
- Added public-safe invalid fixtures and focused regression tests for malformed learner-question source state and undeclared misconception evidence source IDs.
- Updated schema descriptions and reviewer docs to reflect enforced source-binding semantics.

## 2026-07-31

- Added optional top-level `learning_dossier` metadata for folder-based mission, source/reference sheet, question map, practice task, evidence checklist, and review gate sections.
- Added a public-domain folder dossier fixture and checked-in deterministic Markdown render using Lewis Carroll's 1865 `Alice's Adventures in Wonderland`.
- Added validator and renderer coverage for dossier evidence/review requirements while preserving the exactly-one teacher/student/assessment-gate card contract.
