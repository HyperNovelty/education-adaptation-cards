#!/usr/bin/env python3
"""Focused regression tests for education adaptation card validation."""
from __future__ import annotations

import copy
import unittest
from pathlib import Path

from education_adaptation_cards import load_json, validate_doc

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


if __name__ == "__main__":
    unittest.main()
