# Assessment Boundary

Education adaptation cards in this repository are local review aids. They help a
reviewer inspect how a synthetic packet might become teacher notes, student
activities, or assessment-gate checklists.

They are not grading automation, diagnosis, student surveillance, or approval for
classroom use.

Named future-authority fields fail closed before generic key validation. The
current forbidden names cover learner identity, student records, LMS authority,
classroom deployment authority, gradebook writes, automated grading, and
auto-publish. Failures include `forbidden_future_authority_field=<field>` so the
reason is visible to maintainers and renderer callers.

## What Cards May Do

- summarize a synthetic fixture for reviewer inspection
- preserve source boundaries and uncertainty labels
- list risks, mitigations, and required human review roles
- render draft-only lesson, activity, rubric, or gate-report sections
- flag whether a local review packet still needs review

## What Cards Must Not Do

- assign, calculate, or issue final grades
- diagnose learners or infer protected/sensitive traits
- monitor students, track behavior, or create surveillance records
- collect student data, assessment records, rosters, LMS exports, or accounts
- add `student_id`, `learner_id`, `student_record`, `student_records`,
  `lms_export`, `lms_sync`, `lms_course_id`, `classroom_deployment`,
  `classroom_deployment_status`, `gradebook_write`, `auto_grade`, or
  `auto_publish`
- claim final approval without human review
- claim legal, privacy, accessibility, curriculum, or compliance readiness

## Review Posture

Rendered dossiers should remain `local_review_only`, `draft_only`, or
`needs_human_review`. A human reviewer may use them as a checklist or discussion
artifact, but not as a substitute for teacher judgment, institutional review, or
separate approval outside this prototype.
