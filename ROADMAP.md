# Roadmap

This repository explores the idea that the next classroom may be a folder: a durable workspace where mission, sources, questions, misconceptions, assessment evidence, and human review gates live in files rather than only in chat memory.

## Near-term maintainer work

- Keep renderer and report regression fixtures fresh for every valid review-state surface.
- Keep the project local/reference-only: no student data, no LMS integration, no classroom deployment, and no account actions.

## Program fit

- **Codex for OSS:** Codex can help maintain fixture coverage, validator behavior, docs, and issue triage for a public education-verification schema.
- **Codex Open Source Fund:** API credits would support expansion of open fixtures and verification examples around AI-assisted learning infrastructure.

## Good first issues

- Add more invalid examples for future local-only surfaces as new field names are proposed, before any renderer support is added.

## Recently completed

- Added a named forbidden future-authority field gate for learner identity, student records, LMS fields, classroom deployment, gradebook writes, automated grading, and auto-publish.
- Added public-safe invalid fixtures for `review_packet.student_id`, card `lms_export`, dossier `classroom_deployment`, and assessment-gate `gradebook_write`.
- Added a deterministic forbidden-authority inventory CLI and checked-in freshness report.
- Added schema fields for learner questions that remain unanswered or insufficiently sourced.
- Added misconception evidence objects with source IDs, severity, and teacher/reviewer response.
- Added a negative fixture for a card that has learner questions without misconception evidence.
- Expanded the markdown renderer with learner-question and misconception-evidence sections.
- Added a public-domain folder-based learning dossier example with mission, source/reference sheet, question map, practice task, evidence checklist, and review gate metadata.
- Hardened card-level learner-question and misconception-evidence source bindings, including duplicate source IDs, malformed status/source combinations, and undeclared source references.
- Added invalid fixtures for source-bound learner questions without source IDs and misconception evidence with undeclared source IDs.
- Added a deterministic review-boundary report CLI with checked-in JSON freshness checks for packet, dossier, review-gate, and card human-review states.
- Added packet, dossier mission, and dossier review-gate negative fixtures for promoted review states.
- Added renderer fail-closed review-boundary handling so promoted or invalid fixtures exit with labeled `render_boundary=failed` output before markdown writes.
- Added checked-in review-boundary JSON reports for the review-packet and minimal fixtures, with unittest freshness checks.
