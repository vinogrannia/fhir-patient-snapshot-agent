"""Bundled demo context for public online demos."""

from __future__ import annotations

from pathlib import Path

from app.agent import AgentResult, AgentMode, SnapshotAudience
from app.normalizer import (
    CarePlanSummary,
    ConditionSummary,
    EncounterSummary,
    MedicationSummary,
    ObservationGroups,
    ObservationSummary,
    PatientOverview,
    PatientSnapshotContext,
    SourceRef,
)
from app.prompt_builder import SYSTEM_INSTRUCTIONS, build_snapshot_prompt
from app.summary_renderer import render_markdown_summary


SAMPLE_SUMMARY_PATH = Path(__file__).resolve().parents[1] / "docs" / "sample_patient_1_llm_summary.md"


def demo_patient_context() -> PatientSnapshotContext:
    """Return a static Patient 1 context for public demos without live secrets."""

    vitals = [
        ObservationSummary("552", "Body Height", "vital-signs", "2019-09-08T15:32:17+00:00", "193.3 cm"),
        ObservationSummary(
            "553",
            "Pain severity - 0-10 verbal numeric rating [Score] - Reported",
            "vital-signs",
            "2019-09-08T15:32:17+00:00",
            "1 {score}",
        ),
        ObservationSummary("554", "Body Weight", "vital-signs", "2019-09-08T15:32:17+00:00", "113.4 kg"),
        ObservationSummary("555", "Body Mass Index", "vital-signs", "2019-09-08T15:32:17+00:00", "30.35 kg/m2"),
        ObservationSummary(
            "556",
            "Blood Pressure",
            "vital-signs",
            "2019-09-08T15:32:17+00:00",
            "Diastolic Blood Pressure: 82 mm[Hg]; Systolic Blood Pressure: 120.0 mm[Hg]",
        ),
    ]
    labs = [
        ObservationSummary("557", "Total Cholesterol", "laboratory", "2019-09-08T15:32:17+00:00", "185.81 mg/dL"),
        ObservationSummary("558", "Triglycerides", "laboratory", "2019-09-08T15:32:17+00:00", "145.21 mg/dL"),
        ObservationSummary(
            "559",
            "Low Density Lipoprotein Cholesterol",
            "laboratory",
            "2019-09-08T15:32:17+00:00",
            "80.23 mg/dL",
        ),
        ObservationSummary(
            "560",
            "High Density Lipoprotein Cholesterol",
            "laboratory",
            "2019-09-08T15:32:17+00:00",
            "76.54 mg/dL",
        ),
    ]
    surveys = [
        ObservationSummary("561", "Tobacco smoking status NHIS", "survey", "2019-09-08T15:32:17+00:00", "Never smoker")
    ]
    older = [
        ObservationSummary("532", "Body Height", "vital-signs", "2018-09-02T15:32:17+00:00", "193.3 cm"),
        ObservationSummary(
            "533",
            "Pain severity - 0-10 verbal numeric rating [Score] - Reported",
            "vital-signs",
            "2018-09-02T15:32:17+00:00",
            "2 {score}",
        ),
    ]

    return PatientSnapshotContext(
        patient=PatientOverview("1", "Carroll471 O'Hara248", "male", "1954-06-13", 71, False),
        active_conditions=[
            ConditionSummary("13", "Body mass index 30+ - obesity (finding)", "active", "confirmed", "1991-09-01T15:32:17+00:00", "")
        ],
        resolved_conditions=[
            ConditionSummary("286", "Laceration of foot", "resolved", "confirmed", "2015-12-16T15:32:17+00:00", "2015-12-30T15:32:17+00:00"),
            ConditionSummary("322", "Viral sinusitis (disorder)", "resolved", "confirmed", "2016-10-12T15:32:17+00:00", "2016-10-19T15:32:17+00:00"),
            ConditionSummary("528", "Viral sinusitis (disorder)", "resolved", "confirmed", "2018-02-16T15:32:17+00:00", "2018-03-09T15:32:17+00:00"),
            ConditionSummary("543", "Laceration of forearm", "resolved", "confirmed", "2019-08-11T15:32:17+00:00", "2019-09-01T15:32:17+00:00"),
        ],
        medications=[
            MedicationSummary("288", "Acetaminophen 325 MG Oral Tablet", "stopped", "order", "2015-12-16T15:32:17+00:00", True),
            MedicationSummary("545", "Naproxen sodium 220 MG Oral Tablet", "stopped", "order", "2019-08-11T15:32:17+00:00", True),
        ],
        allergies=[],
        recent_observations=[*vitals, *labs, *surveys, *older],
        observation_groups=ObservationGroups(vitals=vitals + older, labs=labs, surveys=surveys, other=[]),
        recent_encounters=[
            EncounterSummary("551", "finished", "AMB", "2019-09-08T15:32:17+00:00", "2019-09-08T16:02:17+00:00"),
            EncounterSummary("542", "finished", "EMER", "2019-08-11T15:32:17+00:00", "2019-08-11T16:17:17+00:00"),
            EncounterSummary("531", "finished", "AMB", "2018-09-02T15:32:17+00:00", "2018-09-02T15:47:17+00:00"),
            EncounterSummary("527", "finished", "AMB", "2018-02-16T15:32:17+00:00", "2018-02-16T15:47:17+00:00"),
            EncounterSummary("325", "finished", "AMB", "2017-08-27T15:32:17+00:00", "2017-08-27T15:47:17+00:00"),
        ],
        care_plans=[
            CarePlanSummary("291", "Wound care", "completed", "order", "2015-12-16T15:32:17+00:00", "2015-12-30T15:32:17+00:00"),
            CarePlanSummary("548", "Wound care", "completed", "order", "2019-08-11T15:32:17+00:00", "2019-09-01T15:32:17+00:00"),
        ],
        missing_information=["No allergy intolerance records were found."],
        source_resources=[
            SourceRef("CarePlan", "291"),
            SourceRef("CarePlan", "548"),
            SourceRef("Condition", "13"),
            SourceRef("Condition", "286"),
            SourceRef("Condition", "322"),
            SourceRef("Condition", "528"),
            SourceRef("Condition", "543"),
            SourceRef("Encounter", "325"),
            SourceRef("Encounter", "527"),
            SourceRef("Encounter", "531"),
            SourceRef("Encounter", "542"),
            SourceRef("Encounter", "551"),
            SourceRef("MedicationRequest", "288"),
            SourceRef("MedicationRequest", "545"),
            SourceRef("Observation", "532"),
            SourceRef("Observation", "533"),
            SourceRef("Observation", "552"),
            SourceRef("Observation", "553"),
            SourceRef("Observation", "554"),
            SourceRef("Observation", "555"),
            SourceRef("Observation", "556"),
            SourceRef("Observation", "557"),
            SourceRef("Observation", "558"),
            SourceRef("Observation", "559"),
            SourceRef("Observation", "560"),
            SourceRef("Observation", "561"),
            SourceRef("Patient", "1"),
        ],
    )


def demo_agent_result(mode: AgentMode, audience: SnapshotAudience) -> AgentResult:
    """Return a static agent result for public online demos."""

    context = demo_patient_context()
    if mode == "prompt":
        return AgentResult("1", mode, audience, context, build_snapshot_prompt(context, audience=audience), SYSTEM_INSTRUCTIONS)
    if mode == "llm":
        return AgentResult("1", mode, audience, context, _sample_llm_summary(), None)
    return AgentResult("1", mode, audience, context, render_markdown_summary(context), None)


def _sample_llm_summary() -> str:
    return SAMPLE_SUMMARY_PATH.read_text(encoding="utf-8")
