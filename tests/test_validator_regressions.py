#!/usr/bin/env python3
"""Focused regression tests for education adaptation card validation."""
from __future__ import annotations

import copy
import unittest
from pathlib import Path

from education_adaptation_cards import EXAMPLES, load_json, validate_doc

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DOMAIN_FIXTURE = ROOT / "examples" / "education_cards.public_domain_folder_dossier.json"


class ValidatorRegressionTests(unittest.TestCase):
    def load_public_domain_doc(self) -> dict:
        return copy.deepcopy(load_json(PUBLIC_DOMAIN_FIXTURE))

    def test_responsible_use_claim_in_dossier_objective_is_rejected(self) -> None:
        doc = self.load_public_domain_doc()
        doc["learning_dossier"]["learning_mission"]["objective"] = (
            "Assign a final grade from dossier evidence while leaving the cards otherwise clean."
        )

        with self.assertRaisesRegex(AssertionError, "must not claim final grading authority"):
            validate_doc(doc, "mutated_dossier_objective.json")

    def test_responsible_use_claim_in_dossier_practice_prompt_is_rejected(self) -> None:
        doc = self.load_public_domain_doc()
        doc["learning_dossier"]["practice_task"]["prompt"] = (
            "Produce a final grade from the source table without changing any card text."
        )

        with self.assertRaisesRegex(AssertionError, "must not claim final grading authority"):
            validate_doc(doc, "mutated_dossier_prompt.json")

    def test_responsible_use_claim_in_dossier_reviewer_note_is_rejected(self) -> None:
        doc = self.load_public_domain_doc()
        doc["learning_dossier"]["review_gate"]["reviewer_note"] = (
            "Approved for classroom use after this local dossier review."
        )

        with self.assertRaisesRegex(AssertionError, "must not claim classroom clearance"):
            validate_doc(doc, "mutated_dossier_reviewer_note.json")

    def test_pre_1929_public_domain_us_rejects_2025_publication_year(self) -> None:
        doc = self.load_public_domain_doc()
        doc["learning_dossier"]["source_reference_sheet"][0]["publication_year"] = 2025

        with self.assertRaisesRegex(AssertionError, "publication_year <= 1928"):
            validate_doc(doc, "mutated_public_domain_year.json")

    def test_existing_valid_fixtures_still_pass(self) -> None:
        for path in EXAMPLES:
            with self.subTest(path=path.name):
                validate_doc(load_json(path), path.name)

    def test_duplicate_allowed_source_ids_are_rejected(self) -> None:
        doc = self.load_public_domain_doc()
        card = doc["education_adaptation_cards"][1]
        card["source_binding"]["allowed_source_ids"] = ["PD001", "PD001"]

        with self.assertRaisesRegex(AssertionError, r"source_binding\.allowed_source_ids duplicate source_id: PD001"):
            validate_doc(doc, "mutated_duplicate_allowed_sources.json")

    def test_source_bound_question_requires_source_ids(self) -> None:
        doc = self.load_public_domain_doc()
        question = doc["education_adaptation_cards"][1]["learner_questions"][0]
        question["question_status"] = "source_bound"
        question["source_ids"] = []

        with self.assertRaisesRegex(AssertionError, "source_ids must be non-empty for source_bound learner question"):
            validate_doc(doc, "mutated_source_bound_without_sources.json")

    def test_unanswered_question_rejects_source_ids(self) -> None:
        doc = self.load_public_domain_doc()
        question = doc["education_adaptation_cards"][1]["learner_questions"][0]
        question["question_status"] = "unanswered"
        question["source_ids"] = ["PD001"]

        with self.assertRaisesRegex(AssertionError, "source_ids must be empty for unanswered learner question"):
            validate_doc(doc, "mutated_unanswered_with_sources.json")

    def test_duplicate_learner_question_source_ids_are_rejected(self) -> None:
        doc = self.load_public_domain_doc()
        question = doc["education_adaptation_cards"][1]["learner_questions"][0]
        question["source_ids"] = ["PD001", "PD001"]

        with self.assertRaisesRegex(AssertionError, r"learner_questions\[0\]\.source_ids duplicate source_id: PD001"):
            validate_doc(doc, "mutated_duplicate_question_sources.json")

    def test_learner_question_undeclared_source_id_is_rejected(self) -> None:
        doc = self.load_public_domain_doc()
        question = doc["education_adaptation_cards"][1]["learner_questions"][0]
        question["source_ids"] = ["PD999"]

        with self.assertRaisesRegex(AssertionError, r"learner_questions\[0\]\.source_ids undeclared source_id: PD999"):
            validate_doc(doc, "mutated_question_undeclared_source.json")

    def test_duplicate_learner_question_ids_are_rejected(self) -> None:
        doc = self.load_public_domain_doc()
        card = doc["education_adaptation_cards"][1]
        card["learner_questions"].append(copy.deepcopy(card["learner_questions"][0]))

        with self.assertRaisesRegex(AssertionError, "learner_questions duplicate question_id: question_alice_supported_claim"):
            validate_doc(doc, "mutated_duplicate_question_ids.json")

    def test_duplicate_misconception_source_ids_are_rejected(self) -> None:
        doc = self.load_public_domain_doc()
        evidence = doc["education_adaptation_cards"][1]["misconception_evidence"][0]
        evidence["source_ids"] = ["PD001", "PD001"]

        with self.assertRaisesRegex(AssertionError, r"misconception_evidence\[0\]\.source_ids duplicate source_id: PD001"):
            validate_doc(doc, "mutated_duplicate_misconception_sources.json")

    def test_misconception_undeclared_source_id_is_rejected(self) -> None:
        doc = self.load_public_domain_doc()
        evidence = doc["education_adaptation_cards"][1]["misconception_evidence"][0]
        evidence["source_ids"] = ["PD999"]

        with self.assertRaisesRegex(AssertionError, r"misconception_evidence\[0\]\.source_ids undeclared source_id: PD999"):
            validate_doc(doc, "mutated_misconception_undeclared_source.json")

    def test_duplicate_misconception_ids_are_rejected(self) -> None:
        doc = self.load_public_domain_doc()
        card = doc["education_adaptation_cards"][1]
        card["misconception_evidence"].append(copy.deepcopy(card["misconception_evidence"][0]))

        with self.assertRaisesRegex(
            AssertionError,
            "misconception_evidence duplicate misconception_id: misconception_inference_as_fact",
        ):
            validate_doc(doc, "mutated_duplicate_misconception_ids.json")


if __name__ == "__main__":
    unittest.main()
