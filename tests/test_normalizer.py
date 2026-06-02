"""Tests for FHIR resource normalization."""

from __future__ import annotations

import unittest

from app.llm_provider import extract_chat_completion_text
from app.normalizer import normalize_snapshot
from app.prompt_builder import build_snapshot_prompt
from app.web_ui import _without_source_resources_section


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
        self.assertIn("Put a blank line before every section heading", prompt)
        self.assertIn("Do not repeat resolved history", prompt)
        self.assertIn("Do not invent additional missing information", prompt)
        self.assertIn("Every explicitly mentioned FHIR resource ID must appear", prompt)
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

        visible_summary = _without_source_resources_section(summary)

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

        visible_summary = _without_source_resources_section(summary)

        self.assertIn("Immediate Orientation", visible_summary)
        self.assertNotIn("Source FHIR Resources Used", visible_summary)
        self.assertNotIn("Patient/1", visible_summary)


if __name__ == "__main__":
    unittest.main()
