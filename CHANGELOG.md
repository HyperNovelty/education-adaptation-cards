# Changelog

## 2026-08-03

- Hardened local validation for learner-question and misconception-evidence source bindings, including duplicate source IDs, status/source consistency, and undeclared card source references.
- Added public-safe invalid fixtures and focused regression tests for malformed learner-question source state and undeclared misconception evidence source IDs.
- Updated schema descriptions and reviewer docs to reflect enforced source-binding semantics.

## 2026-07-31

- Added optional top-level `learning_dossier` metadata for folder-based mission, source/reference sheet, question map, practice task, evidence checklist, and review gate sections.
- Added a public-domain folder dossier fixture and checked-in deterministic Markdown render using Lewis Carroll's 1865 `Alice's Adventures in Wonderland`.
- Added validator and renderer coverage for dossier evidence/review requirements while preserving the exactly-one teacher/student/assessment-gate card contract.
