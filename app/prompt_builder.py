"""Build safe LLM prompts from normalized patient snapshot context."""

from __future__ import annotations

from app.normalizer import PatientSnapshotContext
from app.summary_renderer import SAFETY_NOTE


AUDIENCE_INSTRUCTIONS = {
    "clinician": "Write for a clinician who needs a concise cross-resource patient snapshot.",
    "ed_doctor": (
        "Write for an emergency department doctor who needs rapid orientation to source-data "
        "problems, medications, allergies, recent encounters, and recent observations."
    ),
    "care_manager": (
        "Write for a care manager who needs source-data context around active problems, care "
        "plans, recent utilisation, missing information, and verification points."
    ),
    "patient": (
        "Write in plain language for the patient. Keep medical terms when they come from the "
        "source data, but briefly clarify them without adding advice."
    ),
    "family_caregiver": (
        "Write in plain language for a family caregiver. Focus on what the source data says, "
        "what is missing, and what is marked for source-data verification."
    ),
}


SYSTEM_INSTRUCTIONS = """You are a clinical summarisation assistant.
Your task is to summarise provided FHIR source data only.
Do not diagnose, recommend treatment, or infer facts not present in the source context.
Do not write clinical advice, new care plans, monitoring recommendations, or treatment follow-up instructions.
If the source data contains possible concerns, describe them as source-data verification points only.
When information is missing, say that it is missing.
Always include a source resource list so the output can be verified."""


def build_snapshot_prompt(context: PatientSnapshotContext, audience: str = "clinician") -> str:
    """Build the user prompt that can be sent to an LLM summarisation provider."""

    audience_instruction = AUDIENCE_INSTRUCTIONS.get(audience, AUDIENCE_INSTRUCTIONS["clinician"])

    return "\n".join(
        [
            "Create a concise FHIR patient snapshot using only the source context below.",
            "",
            f"Target audience: {audience}",
            audience_instruction,
            "",
            SAFETY_NOTE,
            "",
            "Required sections:",
            "- Patient overview",
            "- Active problems",
            "- Medications",
            "- Allergies",
            "- Recent observations/labs",
            "- Care plans",
            "- Source-data verification points, not recommendations",
            "- Missing information",
            "- Source FHIR resources used",
            "",
            "Rules:",
            "- Do not recommend monitoring, treatment, medication changes, referrals, or follow-up actions.",
            "- Do not create new care plans; only summarise CarePlan resources present in the source context.",
            "- Do not say that a condition requires action unless the source data explicitly says so.",
            "- Use wording such as 'source data shows' or 'verify in source data' instead of clinical advice.",
            "- Adapt wording and detail level for the target audience without changing the facts.",
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
        "Recent vital-sign observations:",
        *_observation_lines(context.observation_groups.vitals),
        "",
        "Recent laboratory observations:",
        *_observation_lines(context.observation_groups.labs),
        "",
        "Recent survey/social history observations:",
        *_observation_lines(context.observation_groups.surveys),
        "",
        "Other recent observations:",
        *_observation_lines(context.observation_groups.other),
        "",
        "Recent encounters:",
        *_encounter_lines(context.recent_encounters),
        "",
        "Care plans:",
        *_care_plan_lines(context.care_plans),
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


def _care_plan_lines(items: object) -> list[str]:
    care_plans = list(items)
    if not care_plans:
        return ["- none"]

    return [
        f"- CarePlan/{item.id}: {item.title}; status={item.status}; intent={item.intent}; period={item.period_start} to {item.period_end}"
        for item in care_plans
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
