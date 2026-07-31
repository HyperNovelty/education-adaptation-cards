# Roadmap

This repository explores the idea that the next classroom may be a folder: a durable workspace where mission, sources, questions, misconceptions, assessment evidence, and human review gates live in files rather than only in chat memory.

## Near-term maintainer work

- Strengthen schemas for learner-state beyond source-bound questions, assessment evidence, and review-gate outcomes.
- Add more negative fixtures that prevent cards from silently moving from draft/review states into approved learner-facing states.
- Keep the project local/reference-only: no student data, no LMS integration, no classroom deployment, and no account actions.

## Program fit

- **Codex for OSS:** Codex can help maintain fixture coverage, validator behavior, docs, and issue triage for a public education-verification schema.
- **Codex Open Source Fund:** API credits would support expansion of open fixtures and verification examples around AI-assisted learning infrastructure.

## Good first issues

- Add an invalid fixture for malformed learner-question statuses or misconception evidence missing source IDs.

## Recently completed

- Added schema fields for learner questions that remain unanswered or insufficiently sourced.
- Added misconception evidence objects with source IDs, severity, and teacher/reviewer response.
- Added a negative fixture for a card that has learner questions without misconception evidence.
- Expanded the markdown renderer with learner-question and misconception-evidence sections.
- Added a public-domain folder-based learning dossier example with mission, source/reference sheet, question map, practice task, evidence checklist, and review gate metadata.
