# Local Learning Dossier

Local review material only. Not classroom-cleared. No LMS, network, account, publish, or student-data actions are authorized by this artifact.

## Packet Context

- Source fixture: `examples/education_cards.review_packet_fixture.json`
- Generated at: `2026-06-06T10:30:00Z`
- Safety mode: `local_review_only`
- Target system: `ipublishos_agent_os_bridge`
- Packet ID: `voice_to_source_synthetic_packet_edu_mock`
- Packet title: Synthetic Field Guide + Education Adaptation Lane
- Packet path: `docs/ipublishos_learning_dossier_qa_implications_2026-06-09.md`
- Packet status: `draft_only`

## Review Gate Summary

- Lane completeness: exactly one teacher card, one student card, and one assessment/gate card validated before rendering.
- Release boundary: all human review statuses must remain `draft_only` or `needs_human_review`.
- Rendering mode: deterministic markdown generated from local fixture content only.

## Teacher Card: Source-Locked Lesson Planner

- Card ID: `teacher_card_source_locked_lesson`
- Card type: `teacher_card`
- Audience: `teacher`
- Grade band: `adult_professional`

### Purpose

Create a teacher-reviewable lesson plan from an iPublishOS/Agent OS packet while preserving source ledger boundaries, uncertainty, and draft-only status.

### Source Binding

- Source policy: `approved_references_only`
- Allowed source IDs: S001, S002, C001
- Blocked claims policy: Only use claims already present in packet source excerpts or approved citation candidates. Unapproved candidates may appear only as review questions.

### Adaptation Actions

- Map packet thesis, examples, and caveats into 3-5 learning objectives.
- Generate a 30-minute lesson sequence with source IDs next to every factual point.
- Add teacher notes for unresolved claims, terminology risks, and discussion boundaries.
- Mark all generated material DRAFT_ONLY / NOT CLASSROOM-CLEARED.

### Risks

- `teacher_card_unapproved_citation` [high]: A citation candidate that is still review-only could be used as if it were approved.
  Mitigation: Renderer must preserve citation candidate status and gate unapproved candidates out of factual lesson claims.
- `teacher_card_context_collapse` [medium]: A packet designed for product review may not include enough classroom context.
  Mitigation: Require teacher notes and do not infer standards alignment unless explicitly supplied.

### Human Review

- Status: `needs_human_review`
- Required roles: teacher, editor, curriculum_reviewer
- Review notes:
  - No standards alignment is claimed in this mock.
  - Teacher must confirm age/level fit before classroom use.

### Outputs

- `source_locked_lesson_plan` [lesson_plan]: A source-cited lesson sequence suitable for internal review packet rendering.
- `teacher_review_notes` [review_note]: Teacher-facing unresolved questions and classroom caveats.

## Student Card: Guided Source Check

- Card ID: `student_card_guided_source_check`
- Card type: `student_card`
- Audience: `student`
- Grade band: `adult_professional`

### Purpose

Transform the packet into a student activity that teaches source checking instead of presenting draft packet output as finished authority.

### Source Binding

- Source policy: `packet_sources_only`
- Allowed source IDs: S001, S002, C001
- Blocked claims policy: Student-facing copy may ask learners to inspect source-backed claims; it must not introduce additional factual assertions.

### Adaptation Actions

- Convert 3 key packet claims into source-check questions.
- Ask students to label each claim as supported, partially supported, unsupported, or needs more context.
- Include reflection prompts about uncertainty and draft status.
- Avoid personalization, grading, or student data collection in this local mock.

### Risks

- `student_card_overtrust` [medium]: Learners may trust generated review material without checking sources.
  Mitigation: Activity centers source verification and includes explicit draft-only labels.
- `student_card_privacy_scope` [low]: Future implementations could accidentally collect student responses.
  Mitigation: This contract has no collection fields and requires local review only.

### Human Review

- Status: `needs_human_review`
- Required roles: teacher, curriculum_reviewer
- Review notes:
  - Student activity requires teacher approval before use.
  - No LMS/export/student account behavior is included.

### Outputs

- `guided_source_check_activity` [student_activity]: A draft-only worksheet/activity prompt bound to packet sources.
- `student_discussion_prompts` [discussion_prompt]: Questions for discussing source confidence and review status.

## Assessment/Gate Card: Education Lane Packet Release

- Card ID: `assessment_gate_card_review_packet_release`
- Card type: `assessment_gate_card`
- Audience: `curriculum_reviewer`
- Grade band: `adult_professional`

### Purpose

Provide implementation gates that decide whether education cards may be rendered into an iPublishOS/Agent OS review packet.

### Source Binding

- Source policy: `no_new_claims`
- Allowed source IDs: S001, S002, C001
- Blocked claims policy: Gate fails if rendered teacher/student cards contain factual claims without explicit packet source IDs or if draft-only labels are missing.

### Adaptation Actions

- Run source support review across teacher and student cards.
- Run role/status review for required human reviewers.
- Run safety label review for draft-only and not-classroom-cleared wording.
- Emit gate report into the review packet, not into public output.

### Risks

- `assessment_gate_false_pass` [high]: A gate result could be interpreted as automated curriculum approval.
  Mitigation: Allowed statuses are review states only; human_review remains required for release.
- `assessment_gate_missing_visibility` [medium]: Review packet renderer might hide gate results from reviewers.
  Mitigation: Renderer should place gate summary near packet top-level decision area.

### Human Review

- Status: `needs_human_review`
- Required roles: editor, curriculum_reviewer, legal_or_policy
- Review notes:
  - Use this card as a blocking internal gate, not as automated approval.
  - Legal/policy review is required before any external or classroom distribution.

### Outputs

- `education_lane_gate_report` [gate_report]: Structured gate report for the review packet.
- `education_lane_rubric` [rubric]: Reviewer rubric for source support, grade fit, safety labeling, and role approval.

### Assessment Gates

- `all_required_card_types_present` [pass]: Teacher, student, and assessment/gate cards are all present exactly once
  Evidence required:
  - One teacher_card
  - One student_card
  - One assessment_gate_card
- `source_ids_preserved` [needs_review]: Source IDs are preserved in education outputs
  Evidence required:
  - Claim-to-source map
  - No unsupported new factual claims
- `human_review_roles_assigned` [needs_review]: Required human review roles are explicit
  Evidence required:
  - Teacher reviewer
  - Editor reviewer
  - Curriculum reviewer
- `no_public_or_account_action` [pass]: No publish, account, network, LMS, or student-data action is requested
  Evidence required:
  - Local-only artifact paths
  - No credential or account fields
