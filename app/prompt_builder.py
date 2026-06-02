"""Build safe LLM prompts from normalized patient snapshot context."""

from __future__ import annotations

from app.normalizer import PatientSnapshotContext
from app.summary_renderer import SAFETY_NOTE


AUDIENCE_INSTRUCTIONS = {
    "clinician": "Write for a clinician who needs a concise cross-resource patient snapshot.",
    "ed_doctor": (
        "Write for an emergency department doctor. Prioritise immediate orientation, medication "
        "and allergy verification, recent encounters, and recent observations. Keep it terse and scan-friendly."
    ),
    "care_manager": (
        "Write for a care manager. Prioritise active problems, care plans, recent utilisation, "
        "documented gaps, and source-data verification points. Do not create tasks or outreach steps."
    ),
    "patient": (
        "Write in plain language for the patient. Avoid unexplained clinical shorthand. Keep medical "
        "terms only when they come from the source data, and briefly clarify them without adding advice."
    ),
    "family_caregiver": (
        "Write in plain language for a family caregiver. Focus on what the source data says, what is "
        "unknown, and what is marked for source-data verification. Do not assign responsibilities."
    ),
}


AUDIENCE_SECTIONS = {
    "clinician": [
        "Patient overview",
        "Active problems",
        "Medications",
        "Allergies",
        "Recent observations/labs",
        "Care plans",
        "Source-data verification points",
        "Missing information",
        "Source FHIR resources used",
    ],
    "ed_doctor": [
        "Immediate orientation",
        "Active problems relevant to this snapshot",
        "Medication/allergy verification",
        "Recent encounters and observations",
        "Care plans present in source data",
        "Source-data verification points",
        "Missing information",
        "Source FHIR resources used",
    ],
    "care_manager": [
        "Patient context",
        "Active problems",
        "Care plans and recent utilisation",
        "Medications and allergies",
        "Recent observations/labs",
        "Documented gaps from source data",
        "Source-data verification points",
        "Source FHIR resources used",
    ],
    "patient": [
        "Your snapshot",
        "Health problems listed in the source data",
        "Medicines listed in the source data",
        "Allergies listed in the source data",
        "Recent measurements and lab results",
        "Care plans listed in the source data",
        "Information to verify in the source data",
        "Missing information",
        "Source FHIR resources used",
    ],
    "family_caregiver": [
        "Patient snapshot",
        "Health problems listed in the source data",
        "Medicines and allergies listed in the source data",
        "Recent encounters, measurements, and labs",
        "Care plans listed in the source data",
        "Information to verify in the source data",
        "Missing information",
        "Source FHIR resources used",
    ],
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

    audience_key = audience if audience in AUDIENCE_INSTRUCTIONS else "clinician"
    audience_instruction = AUDIENCE_INSTRUCTIONS[audience_key]

    return "\n".join(
        [
            "Create a concise FHIR patient snapshot using only the source context below.",
            "",
            f"Target audience: {audience_key}",
            audience_instruction,
            "",
            SAFETY_NOTE,
            "",
            "Required sections:",
            *_required_section_lines(audience_key),
            "",
            "Rules:",
            "- Do not recommend monitoring, treatment, medication changes, referrals, or follow-up actions.",
            "- Do not create new care plans; only summarise CarePlan resources present in the source context.",
            "- Do not say that a condition requires action unless the source data explicitly says so.",
            "- Use wording such as 'source data shows' or 'verify in source data' instead of clinical advice.",
            "- Adapt wording and detail level for the target audience without changing the facts.",
            "- In the Missing information section, only include items listed under 'Missing information identified by deterministic normalizer'.",
            "- Do not invent additional missing information, risks, gaps, concerns, or follow-up needs.",
            "- Keep the Source FHIR resources used section concise: include the resources you used in the generated summary, not every available resource.",
            "",
            "Source context:",
            _source_context(context),
        ]
    )


def _required_section_lines(audience: str) -> list[str]:
    return [f"- {section}" for section in AUDIENCE_SECTIONS[audience]]


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
