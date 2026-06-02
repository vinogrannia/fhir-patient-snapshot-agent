"""Build safe LLM prompts from normalized patient snapshot context."""

from __future__ import annotations

from app.normalizer import PatientSnapshotContext
from app.summary_renderer import SAFETY_NOTE


SYSTEM_INSTRUCTIONS = """You are a clinical summarisation assistant.
Your task is to summarise provided FHIR source data only.
Do not diagnose, recommend treatment, or infer facts not present in the source context.
Do not write clinical advice, care plans, monitoring recommendations, or treatment follow-up instructions.
If the source data contains possible concerns, describe them as source-data verification points only.
When information is missing, say that it is missing.
Always include a source resource list so the output can be verified."""


def build_snapshot_prompt(context: PatientSnapshotContext) -> str:
    """Build the user prompt that can be sent to an LLM summarisation provider."""

    return "\n".join(
        [
            "Create a concise FHIR patient snapshot using only the source context below.",
            "",
            SAFETY_NOTE,
            "",
            "Required sections:",
            "- Patient overview",
            "- Active problems",
            "- Medications",
            "- Allergies",
            "- Recent observations/labs",
            "- Source-data verification points, not recommendations",
            "- Missing information",
            "- Source FHIR resources used",
            "",
            "Rules:",
            "- Do not recommend monitoring, treatment, medication changes, referrals, or follow-up actions.",
            "- Do not say that a condition requires action unless the source data explicitly says so.",
            "- Use wording such as 'source data shows' or 'verify in source data' instead of clinical advice.",
            "",
            "Source context:",
            _source_context(context),
        ]
    )


def _source_context(context: PatientSnapshotContext) -> str:
    patient = context.patient
    sections = [
        "Patient:",
        f"- id: {patient.id}",
        f"- name: {patient.name}",
        f"- gender: {patient.gender}",
        f"- birth_date: {patient.birth_date}",
        f"- age_years: {patient.age_years}",
        f"- deceased: {patient.deceased}",
        "",
        "Active conditions:",
        *_condition_lines(context.active_conditions),
        "",
        "Resolved/non-active conditions:",
        *_condition_lines(context.resolved_conditions),
        "",
        "Medication requests:",
        *_medication_lines(context.medications),
        "",
        "Allergy intolerance records:",
        *_allergy_lines(context.allergies),
        "",
        "Recent observations:",
        *_observation_lines(context.recent_observations),
        "",
        "Recent encounters:",
        *_encounter_lines(context.recent_encounters),
        "",
        "Missing information identified by deterministic normalizer:",
        *_fallback_lines(context.missing_information),
        "",
        "Source FHIR resources:",
        *_source_lines(context),
    ]
    return "\n".join(sections)


def _condition_lines(items: object) -> list[str]:
    conditions = list(items)
    if not conditions:
        return ["- none"]

    return [
        f"- Condition/{item.id}: {item.name}; status={item.clinical_status}; onset={item.onset}; abatement={item.abatement}"
        for item in conditions
    ]


def _medication_lines(items: object) -> list[str]:
    medications = list(items)
    if not medications:
        return ["- none"]

    return [
        f"- MedicationRequest/{item.id}: {item.name}; status={item.status}; intent={item.intent}; authored_on={item.authored_on}; as_needed={item.as_needed}"
        for item in medications
    ]


def _allergy_lines(items: object) -> list[str]:
    allergies = list(items)
    if not allergies:
        return ["- none"]

    return [
        f"- AllergyIntolerance/{item.id}: {item.substance}; status={item.clinical_status}; criticality={item.criticality}"
        for item in allergies
    ]


def _observation_lines(items: object) -> list[str]:
    observations = list(items)
    if not observations:
        return ["- none"]

    return [
        f"- Observation/{item.id}: {item.effective}; {item.name}; category={item.category}; value={item.value}"
        for item in observations
    ]


def _encounter_lines(items: object) -> list[str]:
    encounters = list(items)
    if not encounters:
        return ["- none"]

    return [
        f"- Encounter/{item.id}: status={item.status}; class={item.class_code}; start={item.start}; end={item.end}"
        for item in encounters
    ]


def _source_lines(context: PatientSnapshotContext) -> list[str]:
    return [
        f"- {source.resource_type}/{source.resource_id}"
        for source in context.source_resources
    ]


def _fallback_lines(items: list[str]) -> list[str]:
    if not items:
        return ["- none"]

    return [f"- {item}" for item in items]
