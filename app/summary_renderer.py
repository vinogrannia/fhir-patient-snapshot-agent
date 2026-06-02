"""Render normalized clinical context as a deterministic Markdown summary."""

from __future__ import annotations

from app.normalizer import (
    AllergySummary,
    ConditionSummary,
    EncounterSummary,
    CarePlanSummary,
    MedicationSummary,
    ObservationSummary,
    PatientSnapshotContext,
)


SAFETY_NOTE = (
    "Safety note: This summary is for demonstration and clinical summarisation only. "
    "It does not diagnose, recommend treatment, or replace clinical judgement. "
    "Verify all generated content against the source FHIR data."
)


def render_markdown_summary(context: PatientSnapshotContext) -> str:
    """Render a concise patient snapshot without using an LLM."""

    patient = context.patient
    lines = [
        "# FHIR Patient Snapshot",
        "",
        SAFETY_NOTE,
        "",
        "## Patient Overview",
        "",
        f"- ID: {patient.id}",
        f"- Name: {patient.name}",
        f"- Gender: {patient.gender}",
        f"- Birth date: {_or_missing(patient.birth_date)}",
        f"- Approximate age: {_age_text(patient.age_years)}",
        f"- Deceased: {'yes' if patient.deceased else 'no'}",
        "",
        "## Active Problems",
        "",
        *_condition_lines(context.active_conditions),
        "",
        "## Medications",
        "",
        *_medication_lines(context.medications),
        "",
        "## Allergies",
        "",
        *_allergy_lines(context.allergies),
        "",
        "## Recent Vitals",
        "",
        *_observation_lines(context.observation_groups.vitals),
        "",
        "## Recent Labs",
        "",
        *_observation_lines(context.observation_groups.labs),
        "",
        "## Survey / Social History Observations",
        "",
        *_observation_lines(context.observation_groups.surveys),
        "",
        "## Other Recent Observations",
        "",
        *_observation_lines(context.observation_groups.other),
        "",
        "## Recent Encounters",
        "",
        *_encounter_lines(context.recent_encounters),
        "",
        "## Care Plans",
        "",
        *_care_plan_lines(context.care_plans),
        "",
        "## Source-Data Verification Points",
        "",
        *_verification_point_lines(context),
        "",
        "## Missing Information",
        "",
        *_fallback_lines(context.missing_information, "No obvious missing information detected."),
        "",
        "## Source FHIR Resources Used",
        "",
        *_source_lines(context),
    ]
    return "\n".join(lines)


def _condition_lines(conditions: list[ConditionSummary]) -> list[str]:
    if not conditions:
        return ["- No active conditions found."]

    return [
        f"- {item.name} ({item.clinical_status or 'status unknown'}, onset: {_or_missing(item.onset)})"
        for item in conditions
    ]


def _medication_lines(medications: list[MedicationSummary]) -> list[str]:
    if not medications:
        return ["- No medication requests found."]

    lines = []
    for item in medications:
        as_needed = "as needed" if item.as_needed else "scheduled/unspecified"
        lines.append(
            f"- {item.name} ({item.status or 'status unknown'}, {as_needed}, authored: {_or_missing(item.authored_on)})"
        )
    return lines


def _allergy_lines(allergies: list[AllergySummary]) -> list[str]:
    if not allergies:
        return ["- No allergy intolerance records found."]

    return [
        f"- {item.substance} ({item.clinical_status or 'status unknown'}, criticality: {_or_missing(item.criticality)})"
        for item in allergies
    ]


def _observation_lines(observations: list[ObservationSummary]) -> list[str]:
    if not observations:
        return ["- No observations found."]

    return [
        f"- {item.effective}: {item.name} = {_or_missing(item.value)} [{item.category or 'uncategorized'}]"
        for item in observations
    ]


def _encounter_lines(encounters: list[EncounterSummary]) -> list[str]:
    if not encounters:
        return ["- No encounters found."]

    return [
        f"- Encounter/{item.id}: {item.status or 'status unknown'}, class {item.class_code or 'unknown'}, start {_or_missing(item.start)}"
        for item in encounters
    ]


def _care_plan_lines(care_plans: list[CarePlanSummary]) -> list[str]:
    if not care_plans:
        return ["- No care plans found."]

    return [
        f"- CarePlan/{item.id}: {item.title} ({item.status or 'status unknown'}, intent: {_or_missing(item.intent)})"
        for item in care_plans
    ]


def _verification_point_lines(context: PatientSnapshotContext) -> list[str]:
    lines = []
    active_names = {item.name.lower() for item in context.active_conditions}
    recent_observation_names = {item.name.lower(): item for item in context.recent_observations}

    if any("obesity" in name or "body mass index 30" in name for name in active_names):
        lines.append("- Active obesity-related condition is present in the source data.")

    bmi = recent_observation_names.get("body mass index")
    if bmi and bmi.value:
        lines.append(f"- Most recent listed BMI observation: {bmi.value}.")

    if not context.allergies:
        lines.append("- Allergy list is empty; confirm whether this means no known allergies or missing documentation.")

    return lines or ["- No deterministic verification points identified from the normalized source data."]


def _source_lines(context: PatientSnapshotContext) -> list[str]:
    grouped: dict[str, list[str]] = {}
    for source in context.source_resources:
        grouped.setdefault(source.resource_type, []).append(source.resource_id)

    return [
        f"- {resource_type}: {', '.join(ids)}"
        for resource_type, ids in sorted(grouped.items())
    ]


def _fallback_lines(items: list[str], fallback: str) -> list[str]:
    if not items:
        return [f"- {fallback}"]

    return [f"- {item}" for item in items]


def _age_text(age_years: int | None) -> str:
    if age_years is None:
        return "missing"

    return f"{age_years} years"


def _or_missing(value: str) -> str:
    return value or "missing"
