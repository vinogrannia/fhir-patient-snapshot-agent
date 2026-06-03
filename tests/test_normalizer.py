"""Tests for FHIR resource normalization."""

from __future__ import annotations

import unittest

from app.llm_provider import extract_chat_completion_text
from app.normalizer import normalize_snapshot
from app.prompt_builder import build_snapshot_prompt
from app.web_ui import _clean_summary_markdown


class NormalizeSnapshotTest(unittest.TestCase):
    def test_normalizes_patient_snapshot(self) -> None:
        raw = {
            "patient": {
                "resourceType": "Patient",
                "id": "1",
                "name": [{"given": ["Carroll471"], "family": "O'Hara248"}],
                "gender": "male",
                "birthDate": "1954-06-13",
            },
            "conditions": {
                "resourceType": "Bundle",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Condition",
                            "id": "13",
                            "clinicalStatus": {"coding": [{"code": "active"}]},
                            "verificationStatus": {"coding": [{"code": "confirmed"}]},
                            "code": {"text": "Body mass index 30+ - obesity (finding)"},
                            "onsetDateTime": "1991-09-01T15:32:17+00:00",
                        }
                    }
                ],
            },
            "medications": {
                "resourceType": "Bundle",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "MedicationRequest",
                            "id": "288",
                            "status": "stopped",
                            "intent": "order",
                            "medicationCodeableConcept": {
                                "text": "Acetaminophen 325 MG Oral Tablet"
                            },
                            "authoredOn": "2015-12-16T15:32:17+00:00",
                            "dosageInstruction": [{"asNeededBoolean": True}],
                        }
                    }
                ],
            },
            "allergies": {"resourceType": "Bundle", "entry": []},
            "observations": {
                "resourceType": "Bundle",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Observation",
                            "id": "555",
                            "category": [{"coding": [{"code": "vital-signs"}]}],
                            "code": {"text": "Body Mass Index"},
                            "effectiveDateTime": "2019-09-08T15:32:17+00:00",
                            "valueQuantity": {"value": 30.35, "unit": "kg/m2"},
                        }
                    }
                ],
            },
            "encounters": {"resourceType": "Bundle", "entry": []},
            "care_plans": {
                "resourceType": "Bundle",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "CarePlan",
                            "id": "900",
                            "status": "active",
                            "intent": "plan",
                            "title": "Weight management plan",
                            "period": {"start": "2019-09-08"},
                        }
                    }
                ],
            },
        }

        context = normalize_snapshot(raw)

        self.assertEqual(context.patient.name, "Carroll471 O'Hara248")
        self.assertEqual(context.active_conditions[0].name, "Body mass index 30+ - obesity (finding)")
        self.assertEqual(context.medications[0].name, "Acetaminophen 325 MG Oral Tablet")
        self.assertEqual(context.recent_observations[0].value, "30.35 kg/m2")
        self.assertEqual(context.observation_groups.vitals[0].name, "Body Mass Index")
        self.assertEqual(context.observation_groups.labs, [])
        self.assertEqual(context.care_plans[0].title, "Weight management plan")
        self.assertIn("No allergy intolerance records were found.", context.missing_information)

    def test_builds_prompt_with_safety_constraints(self) -> None:
        raw = {
            "patient": {
                "resourceType": "Patient",
                "id": "1",
                "name": [{"given": ["Carroll471"], "family": "O'Hara248"}],
            },
            "conditions": {"resourceType": "Bundle", "entry": []},
            "medications": {"resourceType": "Bundle", "entry": []},
            "allergies": {"resourceType": "Bundle", "entry": []},
            "observations": {"resourceType": "Bundle", "entry": []},
            "encounters": {"resourceType": "Bundle", "entry": []},
            "care_plans": {"resourceType": "Bundle", "entry": []},
        }

        prompt = build_snapshot_prompt(normalize_snapshot(raw), audience="patient")

        self.assertIn("does not diagnose", prompt)
        self.assertIn("Do not recommend monitoring", prompt)
        self.assertIn("Target audience: patient", prompt)
        self.assertIn("Write in plain language for the patient", prompt)
        self.assertIn("Your snapshot", prompt)
        self.assertIn("Source-data notes", prompt)
        self.assertIn("Do not use imperative verbs", prompt)
        self.assertIn("Use Markdown headings for each required section", prompt)
        self.assertIn("Use Markdown bullet lists with '- '", prompt)
        self.assertIn("Do not write a subsection label followed by a blank line and then unbulleted list items", prompt)
        self.assertIn("Do not create empty bullet points", prompt)
        self.assertIn("Put a blank line before every section heading", prompt)
        self.assertIn("Do not copy raw source-context lines verbatim", prompt)
        self.assertIn("Do not include FHIR resource IDs in narrative sections", prompt)
        self.assertIn("Keep FHIR resource IDs only in the Source FHIR resources used section", prompt)
        self.assertIn("readable clinical language", prompt)
        self.assertIn("Do not repeat resolved history", prompt)
        self.assertIn("Do not invent additional missing information", prompt)
        self.assertIn("Every source resource used to generate the summary must appear", prompt)
        self.assertIn("only include items listed under 'Missing information identified by deterministic normalizer'", prompt)
        self.assertIn("Recent vital-sign observations", prompt)
        self.assertIn("Care plans", prompt)
        self.assertIn("Source FHIR resources", prompt)
        self.assertIn("Patient/1", prompt)

    def test_builds_distinct_ed_doctor_prompt_sections(self) -> None:
        raw = {
            "patient": {
                "resourceType": "Patient",
                "id": "1",
                "name": [{"given": ["Carroll471"], "family": "O'Hara248"}],
            },
            "conditions": {"resourceType": "Bundle", "entry": []},
            "medications": {"resourceType": "Bundle", "entry": []},
            "allergies": {"resourceType": "Bundle", "entry": []},
            "observations": {"resourceType": "Bundle", "entry": []},
            "encounters": {"resourceType": "Bundle", "entry": []},
            "care_plans": {"resourceType": "Bundle", "entry": []},
        }

        prompt = build_snapshot_prompt(normalize_snapshot(raw), audience="ed_doctor")

        self.assertIn("Target audience: ed_doctor", prompt)
        self.assertIn("Immediate orientation", prompt)
        self.assertIn("Medication/allergy verification", prompt)
        self.assertIn("Source-data checks", prompt)
        self.assertIn("Keep it terse and scan-friendly", prompt)

    def test_extracts_chat_completion_text(self) -> None:
        payload = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Clinical summary text",
                    }
                }
            ]
        }

        self.assertEqual(extract_chat_completion_text(payload), "Clinical summary text")

    def test_removes_source_section_from_ui_summary(self) -> None:
        summary = "\n".join(
            [
                "Patient Snapshot",
                "",
                "Immediate Orientation",
                "Source data shows one active condition.",
                "",
                "Source FHIR Resources Used",
                "",
                "Patient/1",
                "Condition/13",
            ]
        )

        visible_summary = _clean_summary_markdown(summary)

        self.assertIn("Immediate Orientation", visible_summary)
        self.assertNotIn("Source FHIR Resources Used", visible_summary)
        self.assertNotIn("Condition/13", visible_summary)

    def test_removes_bold_source_section_from_ui_summary(self) -> None:
        summary = "\n".join(
            [
                "Patient Snapshot",
                "",
                "**Immediate Orientation**",
                "Source data shows one active condition.",
                "",
                "**Source FHIR Resources Used**",
                "",
                "Patient/1",
                "Condition/13",
            ]
        )

        visible_summary = _clean_summary_markdown(summary)

        self.assertIn("Immediate Orientation", visible_summary)
        self.assertNotIn("Source FHIR Resources Used", visible_summary)
        self.assertNotIn("Patient/1", visible_summary)

    def test_adds_spacing_before_embedded_observation_subheadings(self) -> None:
        summary = (
            "Recent observations/labs\n"
            "Observation/556: Blood Pressure; value=120/82 mmHg Recent laboratory observations:\n"
            "Observation/557: Total Cholesterol; value=185.81 mg/dL"
        )

        visible_summary = _clean_summary_markdown(summary)

        self.assertIn("120/82 mmHg\n\nRecent laboratory observations:", visible_summary)

    def test_adds_spacing_before_ed_summary_inline_sections(self) -> None:
        summary = (
            "Medication/allergy verification\n"
            "Naproxen sodium 220 MG Oral Tablet The patient has no recorded allergy intolerance records.\n"
            "Recent encounters and observations\n"
            "Encounter on 2017-08-27 (AMB class) Recent observations include:\n"
            "Vital signs: Body Height (193.3 cm)"
        )

        visible_summary = _clean_summary_markdown(summary)

        self.assertIn(
            "Naproxen sodium 220 MG Oral Tablet\n\nThe patient has no recorded allergy intolerance records.",
            visible_summary,
        )
        self.assertIn(
            "Encounter on 2017-08-27 (AMB class)\n\nRecent observations include:",
            visible_summary,
        )

    def test_adds_spacing_before_source_data_allergy_statement(self) -> None:
        summary = (
            "Medication/allergy verification\n"
            "Naproxen sodium 220 MG Oral Tablet (stopped) Source data contains no allergy intolerance records."
        )

        visible_summary = _clean_summary_markdown(summary)

        self.assertIn(
            "Naproxen sodium 220 MG Oral Tablet (stopped)\n\nSource data contains no allergy intolerance records.",
            visible_summary,
        )

    def test_adds_spacing_before_short_recent_observations_heading(self) -> None:
        summary = (
            "Recent encounters and observations\n"
            "Encounter on 2017-08-27 (finished, ambulatory) Recent observations:\n"
            "Vital signs: Body Height (193.3 cm)"
        )

        visible_summary = _clean_summary_markdown(summary)

        self.assertIn(
            "Encounter on 2017-08-27 (finished, ambulatory)\n\nRecent observations:",
            visible_summary,
        )

    def test_removes_inline_resource_id_prefixes_from_ui_summary(self) -> None:
        summary = "\n".join(
            [
                "Active problems",
                "Condition/13: Body mass index 30+ - obesity",
                "Recent observations",
                "Observation/555: Body Mass Index, 30.35 kg/m2",
            ]
        )

        visible_summary = _clean_summary_markdown(summary)

        self.assertIn("Body mass index 30+ - obesity", visible_summary)
        self.assertIn("Body Mass Index, 30.35 kg/m2", visible_summary)
        self.assertNotIn("Condition/13", visible_summary)
        self.assertNotIn("Observation/555", visible_summary)

    def test_adds_missing_bullets_after_colon_labels(self) -> None:
        summary = "\n".join(
            [
                "Resolved conditions:",
                "",
                "Laceration of foot, resolved by 2015-12-30",
                "Viral sinusitis, resolved by 2016-10-19",
            ]
        )

        visible_summary = _clean_summary_markdown(summary)

        self.assertIn("- Laceration of foot, resolved by 2015-12-30", visible_summary)
        self.assertIn("- Viral sinusitis, resolved by 2016-10-19", visible_summary)

    def test_adds_bullets_without_bulleting_next_section_heading(self) -> None:
        summary = "\n".join(
            [
                "Medication/allergy verification",
                "Medication requests include:",
                "Acetaminophen 325 MG Oral Tablet",
                "Naproxen sodium 220 MG Oral Tablet",
                "Allergies",
                "Source data contains no allergy intolerance records.",
                "Care plans listed in the source data",
                "Completed care plans:",
                "Wound care from December 16, 2015, to December 30, 2015",
                "Wound care from August 11, 2019, to September 1, 2019",
                "Source-data notes",
                "Only stopped medication requests are present.",
            ]
        )

        visible_summary = _clean_summary_markdown(summary)

        self.assertIn("Medication requests include:\n- Acetaminophen 325 MG Oral Tablet", visible_summary)
        self.assertIn("- Naproxen sodium 220 MG Oral Tablet", visible_summary)
        self.assertIn("\nAllergies\n", visible_summary)
        self.assertNotIn("- Allergies", visible_summary)
        self.assertIn("Completed care plans:\n- Wound care from December 16, 2015", visible_summary)
        self.assertIn("- Wound care from August 11, 2019", visible_summary)
        self.assertIn("\nSource-data notes\n", visible_summary)
        self.assertNotIn("- Source-data notes", visible_summary)

    def test_removes_empty_bullet_lines_from_ui_summary(self) -> None:
        summary = "\n".join(
            [
                "Medication/allergy verification",
                "-",
                "",
                "Medications:",
                "- Acetaminophen 325 MG Oral Tablet (stopped)",
                "•",
                "",
                "Allergies:",
                "- No allergy intolerance records were found",
            ]
        )

        visible_summary = _clean_summary_markdown(summary)

        self.assertIn("Medications:", visible_summary)
        self.assertIn("- Acetaminophen 325 MG Oral Tablet (stopped)", visible_summary)
        self.assertIn("Allergies:", visible_summary)
        self.assertIn("- No allergy intolerance records were found", visible_summary)
        self.assertNotIn("\n-\n", visible_summary)
        self.assertNotIn("\n•\n", visible_summary)


if __name__ == "__main__":
    unittest.main()
