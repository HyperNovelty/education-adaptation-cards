# Local Learning Dossier

Local review material only. Not classroom-cleared. No LMS, network, account, publish, or student-data actions are authorized by this artifact.

## Packet Context

- Source fixture: `examples/education_cards.public_domain_folder_dossier.json`
- Generated at: `2026-07-31T12:00:00Z`
- Safety mode: `local_review_only`
- Target system: `ipublishos_agent_os_bridge`
- Packet ID: `alice_public_domain_folder_dossier`
- Packet title: Public-Domain Folder Learning Dossier: Alice Source Check
- Packet path: `examples/education_cards.public_domain_folder_dossier.json`
- Packet status: `draft_only`

## Review Gate Summary

- Lane completeness: exactly one teacher card, one student card, and one assessment/gate card validated before rendering.
- Release boundary: all human review statuses must remain `draft_only` or `needs_human_review`.
- Rendering mode: deterministic markdown generated from local fixture content only.

## Folder-Based Learning Dossier

- Dossier ID: `alice_source_check_folder`
- Dossier title: Alice Source Check Folder
- Folder layout:
  - mission.md
  - source_reference_sheet.md
  - question_map.md
  - practice_task.md
  - evidence_checklist.md
  - review_gate.md

### Learning Mission

- Mission ID: `mission_source_to_claim`
- Audience: higher education writing or media literacy reviewers
- Review state: `needs_human_review`
- Objective: Practice turning one public-domain literary excerpt into source-bound questions, a small claim map, and reviewable evidence without adding unsourced interpretation.

### Source/Reference Sheet

- `PD001`: Alice's Adventures in Wonderland (1865), Lewis Carroll
  Public-domain status: `pre_1929_public_domain_us`
  Public-domain basis: First published in 1865, before 1929; used here as a public-domain United States source example.
  URL: https://www.gutenberg.org/ebooks/11
  Minimal excerpt: "Alice was beginning to get very tired of sitting by her sister on the bank."

### Question Map

- `question_observable_setting`: What observable setting detail can be cited directly from PD001 without interpretation?
  Source IDs: PD001
  Reviewer note: Synthetic source-check question; no learner answer is collected.
- `question_claim_boundary`: Which statements would go beyond the excerpt and need another cited source or a reviewer note?
  Source IDs: PD001
  Reviewer note: Keeps the activity focused on claim boundaries, not literary evaluation or grading.

### Practice Task

- Task ID: `task_claim_evidence_table`
- Prompt: Create a three-row claim/evidence table: one directly supported observation, one inference labeled as inference, and one claim that must remain unanswered from this excerpt alone.
- Source IDs: PD001
- Evidence output IDs: evidence_source_id_present, evidence_boundary_label_present
- Reviewer note: Reviewer checks the artifact structure only; this fixture does not score or store learner work.

### Evidence Checklist

- `evidence_source_id_present`: Each factual observation includes the source ID PD001.
  Source IDs: PD001
  Reviewer note: Required before the folder can move out of draft review.
- `evidence_boundary_label_present`: Inference and unanswered claims are labeled so they are not presented as source facts.
  Source IDs: PD001
  Reviewer note: Required to keep the dossier source-bound and local-review-only.

### Review Gate

- Gate ID: `gate_folder_evidence_review`
- Status: `needs_human_review`
- Required roles: teacher, curriculum_reviewer
- Evidence required IDs: evidence_source_id_present, evidence_boundary_label_present
- Reviewer note: Human reviewers must confirm source IDs, public-domain citation notes, and claim-boundary labels before any separate use decision.

## Teacher Card: Alice Source Folder Review

- Card ID: `teacher_card_alice_source_folder`
- Card type: `teacher_card`
- Audience: `teacher`
- Grade band: `higher_ed`

### Purpose

Help a teacher review a folder-based source-check activity tied to one public-domain excerpt.

### Source Binding

- Source policy: `packet_sources_only`
- Allowed source IDs: PD001
- Blocked claims policy: Use only PD001 for factual observations; any interpretation or literary context must be labeled as inference or left unresolved.

### Adaptation Actions

- Confirm the source/reference sheet identifies the public-domain basis and URL.
- Review the question map for source-bound wording.
- Check that the practice task asks for evidence labels instead of grades or learner profiles.

### Risks

- `teacher_card_overreading_excerpt` [medium]: The activity could imply broad interpretation from a single short excerpt.
  Mitigation: Require claim-boundary labels and keep unsupported interpretation as a reviewer question.

### Human Review

- Status: `needs_human_review`
- Required roles: teacher, curriculum_reviewer
- Review notes:
  - Public-domain status is represented as a conservative pre-1929 United States basis.
  - Teacher review is required before any separate education-facing use.

### Outputs

- `alice_teacher_review_notes` [review_note]: Teacher-facing notes for reviewing the folder mission, source sheet, questions, practice task, and evidence checklist.

## Student Card: Alice Source Check Draft

- Card ID: `student_card_alice_source_check`
- Card type: `student_card`
- Audience: `student`
- Grade band: `higher_ed`

### Purpose

Convert the folder dossier into draft prompts that practice distinguishing source facts, inferences, and unresolved claims.

### Source Binding

- Source policy: `packet_sources_only`
- Allowed source IDs: PD001
- Blocked claims policy: Student-facing prompts may ask learners to inspect PD001 but must not add biographical, historical, or interpretive claims without sources.

### Adaptation Actions

- Ask for a claim/evidence table using PD001.
- Require explicit labels for inference and unanswered claims.
- Keep responses local and outside any account, LMS, or student-record workflow.

### Risks

- `student_card_source_confusion` [medium]: A learner may treat an inference as a directly supported source fact.
  Mitigation: The evidence checklist requires separate labels for supported observations, inferences, and unanswered claims.

### Human Review

- Status: `needs_human_review`
- Required roles: teacher
- Review notes:
  - Draft prompts only; no learner response is collected by this fixture.
  - No grade, learner judgment, profile, or classroom-clearance claim is included.

### Outputs

- `alice_claim_evidence_prompt` [student_activity]: Draft-only prompt for a local claim/evidence table.

### Learner Questions

- `question_alice_supported_claim` [source_bound]: Which claim can you support directly with PD001?
  Source IDs: PD001
  Reviewer note: Synthetic question for local review; no answer or identity is stored.

### Misconception Evidence

- `misconception_inference_as_fact` [medium]: A learner may label an inference as if it were directly stated in the source.
  Evidence signal: The practice task separates direct observation, inference, and unanswered claim rows.
  Source IDs: PD001
  Teacher response: Ask for the exact source phrase next to direct observations and require inference labels elsewhere.
  Reviewer note: Synthetic planning evidence only; not a record about a real learner.

## Assessment/Gate Card: Alice Folder Evidence Review

- Card ID: `assessment_gate_card_alice_folder`
- Card type: `assessment_gate_card`
- Audience: `curriculum_reviewer`
- Grade band: `higher_ed`

### Purpose

Gate the folder dossier so mission, source sheet, question map, practice task, evidence checklist, and review gate remain visible and review-only.

### Source Binding

- Source policy: `no_new_claims`
- Allowed source IDs: PD001
- Blocked claims policy: Gate fails if the dossier omits required evidence IDs, hides review status, or presents unsupported claims as source facts.

### Adaptation Actions

- Check that the folder dossier includes every required metadata section.
- Check that practice evidence IDs match the evidence checklist.
- Check that the review gate requires human roles and evidence IDs.

### Risks

- `assessment_gate_evidence_skipped` [high]: A folder task could be rendered without explicit evidence requirements.
  Mitigation: Validator requires non-empty practice evidence IDs and review-gate evidence IDs that reference checklist entries.

### Human Review

- Status: `needs_human_review`
- Required roles: teacher, curriculum_reviewer
- Review notes:
  - Gate status remains a review state only.
  - No publication, LMS, account, student-data, grading, or classroom-use action is authorized.

### Outputs

- `alice_folder_gate_report` [gate_report]: Review-only gate report for the folder dossier evidence requirements.

### Assessment Gates

- `folder_metadata_present` [pass]: Mission, source sheet, question map, practice task, evidence checklist, and review gate are present
  Evidence required:
  - learning_dossier object
  - All six required dossier sections
- `folder_evidence_linked` [needs_review]: Practice task and review gate name checklist evidence IDs
  Evidence required:
  - Practice evidence output IDs
  - Review gate evidence required IDs
