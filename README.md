# education-adaptation-cards

JSON schema and fixtures for AI-era education adaptation cards: learner-state, assessment evidence, misconception tracking, and human review gates.

# iPublishOS / Agent OS Education Adaptation Cards

Local-only mock contract for attaching teacher, student, and assessment/gate education adaptation cards to iPublishOS / Agent OS review packets.

## Included

- `schemas/education_adaptation_cards.schema.json` — documentation-facing JSON Schema contract.
- `examples/education_cards.minimal.json` — smallest complete card lane fixture.
- `examples/education_cards.review_packet_fixture.json` — fuller fixture referencing the existing Voice-to-Source review packet output.
- `examples/invalid/human_review_status_approved_card.json` — negative fixture proving local-review-only human review states are enforced.
- `docs/education_adaptation_cards_contract.md` — implementation notes and review-packet integration guidance.
- `tests/validate_education_adaptation_cards.py` — Python standard-library validator; no third-party installs.
- `scripts/render_learning_dossier.py` — deterministic stdlib renderer for local markdown learning dossiers/review packets.

## Safety boundary

This prototype is local review material only. It does not publish, contact anyone, create accounts, install packages, call networks, integrate with an LMS, or collect student data.

## Verify

```bash
cd products/ipublishos_education_adaptation_cards
python3 -m json.tool schemas/education_adaptation_cards.schema.json >/tmp/education_adaptation_cards.schema.validated.json
python3 -m json.tool examples/education_cards.minimal.json >/tmp/education_cards.minimal.validated.json
python3 -m json.tool examples/education_cards.review_packet_fixture.json >/tmp/education_cards.review_packet_fixture.validated.json
python3 tests/validate_education_adaptation_cards.py
```


## Development

Run the validators with:

```bash
python3 tests/validate_education_adaptation_cards.py
python3 scripts/render_learning_dossier.py examples/education_cards.review_packet_fixture.json
python3 tests/test_render_learning_dossier_smoke.py
```
