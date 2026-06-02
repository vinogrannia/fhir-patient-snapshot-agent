"""Normalize raw FHIR resources into summary-ready clinical context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.fhir_client import bundle_entries


@dataclass(frozen=True)
class SourceRef:
    resource_type: str
    resource_id: str


@dataclass(frozen=True)
class PatientOverview:
    id: str
    name: str
    gender: str
    birth_date: str
    age_years: int | None
    deceased: bool


@dataclass(frozen=True)
class ConditionSummary:
    id: str
    name: str
    clinical_status: str
    verification_status: str
    onset: str
    abatement: str


@dataclass(frozen=True)
class MedicationSummary:
    id: str
    name: str
    status: str
    intent: str
    authored_on: str
    as_needed: bool | None


@dataclass(frozen=True)
class AllergySummary:
    id: str
    substance: str
    clinical_status: str
    verification_status: str
    criticality: str


@dataclass(frozen=True)
class ObservationSummary:
    id: str
    name: str
    category: str
    effective: str
    value: str


@dataclass(frozen=True)
class ObservationGroups:
    vitals: list[ObservationSummary]
    labs: list[ObservationSummary]
    surveys: list[ObservationSummary]
    other: list[ObservationSummary]


@dataclass(frozen=True)
class EncounterSummary:
    id: str
    status: str
    class_code: str
    start: str
    end: str


@dataclass(frozen=True)
class PatientSnapshotContext:
    patient: PatientOverview
    active_conditions: list[ConditionSummary]
    resolved_conditions: list[ConditionSummary]
    medications: list[MedicationSummary]
    allergies: list[AllergySummary]
    recent_observations: list[ObservationSummary]
    observation_groups: ObservationGroups
    recent_encounters: list[EncounterSummary]
    missing_information: list[str]
    source_resources: list[SourceRef]


def normalize_snapshot(raw: dict[str, Any], recent_observation_limit: int = 12) -> PatientSnapshotContext:
    """Convert fetched FHIR resources into a compact clinical context."""

    patient = _normalize_patient(raw["patient"])
    conditions = [_normalize_condition(item) for item in bundle_entries(raw["conditions"])]
    medications = [_normalize_medication(item) for item in bundle_entries(raw["medications"])]
    allergies = [_normalize_allergy(item) for item in bundle_entries(raw["allergies"])]
    observations = [_normalize_observation(item) for item in bundle_entries(raw["observations"])]
    encounters = [_normalize_encounter(item) for item in bundle_entries(raw["encounters"])]

    observations = sorted(observations, key=lambda item: item.effective, reverse=True)
    recent_observations = observations[:recent_observation_limit]
    encounters = sorted(encounters, key=lambda item: item.start, reverse=True)

    active_conditions = [
        item for item in conditions if item.clinical_status.lower() == "active"
    ]
    resolved_conditions = [
        item for item in conditions if item.clinical_status.lower() != "active"
    ]

    missing_information = _missing_information(
        patient=patient,
        active_conditions=active_conditions,
        medications=medications,
        allergies=allergies,
        observations=observations,
    )

    return PatientSnapshotContext(
        patient=patient,
        active_conditions=active_conditions,
        resolved_conditions=resolved_conditions,
        medications=medications,
        allergies=allergies,
        recent_observations=recent_observations,
        observation_groups=_group_observations(recent_observations),
        recent_encounters=encounters[:5],
        missing_information=missing_information,
        source_resources=_source_resources(raw),
    )


def _normalize_patient(resource: dict[str, Any]) -> PatientOverview:
    birth_date = _string(resource.get("birthDate"))
    return PatientOverview(
        id=_string(resource.get("id")),
        name=_human_name(resource.get("name", [])),
        gender=_string(resource.get("gender"), "unknown"),
        birth_date=birth_date,
        age_years=_age_years(birth_date),
        deceased=bool(resource.get("deceasedBoolean") or resource.get("deceasedDateTime")),
    )


def _normalize_condition(resource: dict[str, Any]) -> ConditionSummary:
    return ConditionSummary(
        id=_string(resource.get("id")),
        name=_codeable_text(resource.get("code")),
        clinical_status=_coding_code(resource.get("clinicalStatus")),
        verification_status=_coding_code(resource.get("verificationStatus")),
        onset=_string(resource.get("onsetDateTime") or resource.get("onsetString")),
        abatement=_string(resource.get("abatementDateTime") or resource.get("abatementString")),
    )


def _normalize_medication(resource: dict[str, Any]) -> MedicationSummary:
    dosage = resource.get("dosageInstruction")
    first_dosage = dosage[0] if isinstance(dosage, list) and dosage else {}
    return MedicationSummary(
        id=_string(resource.get("id")),
        name=_codeable_text(resource.get("medicationCodeableConcept")),
        status=_string(resource.get("status")),
        intent=_string(resource.get("intent")),
        authored_on=_string(resource.get("authoredOn")),
        as_needed=first_dosage.get("asNeededBoolean") if isinstance(first_dosage, dict) else None,
    )


def _normalize_allergy(resource: dict[str, Any]) -> AllergySummary:
    return AllergySummary(
        id=_string(resource.get("id")),
        substance=_codeable_text(resource.get("code")),
        clinical_status=_coding_code(resource.get("clinicalStatus")),
        verification_status=_coding_code(resource.get("verificationStatus")),
        criticality=_string(resource.get("criticality")),
    )


def _normalize_observation(resource: dict[str, Any]) -> ObservationSummary:
    return ObservationSummary(
        id=_string(resource.get("id")),
        name=_codeable_text(resource.get("code")),
        category=_observation_category(resource),
        effective=_string(resource.get("effectiveDateTime") or resource.get("issued")),
        value=_observation_value(resource),
    )


def _normalize_encounter(resource: dict[str, Any]) -> EncounterSummary:
    period = resource.get("period", {})
    if not isinstance(period, dict):
        period = {}

    class_value = resource.get("class", {})
    if not isinstance(class_value, dict):
        class_value = {}

    return EncounterSummary(
        id=_string(resource.get("id")),
        status=_string(resource.get("status")),
        class_code=_string(class_value.get("code") or class_value.get("display")),
        start=_string(period.get("start")),
        end=_string(period.get("end")),
    )


def _group_observations(observations: list[ObservationSummary]) -> ObservationGroups:
    vitals: list[ObservationSummary] = []
    labs: list[ObservationSummary] = []
    surveys: list[ObservationSummary] = []
    other: list[ObservationSummary] = []

    for observation in observations:
        category = observation.category.lower()
        if category == "vital-signs":
            vitals.append(observation)
        elif category == "laboratory":
            labs.append(observation)
        elif category == "survey":
            surveys.append(observation)
        else:
            other.append(observation)

    return ObservationGroups(
        vitals=vitals,
        labs=labs,
        surveys=surveys,
        other=other,
    )


def _missing_information(
    patient: PatientOverview,
    active_conditions: list[ConditionSummary],
    medications: list[MedicationSummary],
    allergies: list[AllergySummary],
    observations: list[ObservationSummary],
) -> list[str]:
    missing: list[str] = []
    if not patient.birth_date:
        missing.append("Patient birth date is missing.")
    if not active_conditions:
        missing.append("No active conditions were found in the queried FHIR resources.")
    if not medications:
        missing.append("No medication requests were found in the queried FHIR resources.")
    if not allergies:
        missing.append("No allergy intolerance records were found.")
    if not observations:
        missing.append("No observations were found.")

    return missing


def _source_resources(raw: dict[str, Any]) -> list[SourceRef]:
    sources = [_source_ref(raw["patient"])]
    for key in ("conditions", "medications", "allergies", "observations", "encounters"):
        sources.extend(_source_ref(resource) for resource in bundle_entries(raw[key]))

    return sorted(sources, key=lambda item: (item.resource_type, _resource_id_sort_key(item.resource_id)))


def _source_ref(resource: dict[str, Any]) -> SourceRef:
    return SourceRef(
        resource_type=_string(resource.get("resourceType")),
        resource_id=_string(resource.get("id")),
    )


def _human_name(names: Any) -> str:
    if not isinstance(names, list) or not names:
        return "Unknown"

    name = names[0]
    if not isinstance(name, dict):
        return "Unknown"

    given = name.get("given", [])
    given_text = " ".join(str(part) for part in given) if isinstance(given, list) else ""
    family = _string(name.get("family"))
    full_name = f"{given_text} {family}".strip()
    return full_name or "Unknown"


def _codeable_text(value: Any) -> str:
    if not isinstance(value, dict):
        return "Unknown"

    if value.get("text"):
        return str(value["text"])

    coding = value.get("coding")
    if isinstance(coding, list) and coding and isinstance(coding[0], dict):
        return _string(coding[0].get("display") or coding[0].get("code"), "Unknown")

    return "Unknown"


def _coding_code(value: Any) -> str:
    if not isinstance(value, dict):
        return ""

    coding = value.get("coding")
    if isinstance(coding, list) and coding and isinstance(coding[0], dict):
        return _string(coding[0].get("code") or coding[0].get("display"))

    return ""


def _observation_category(resource: dict[str, Any]) -> str:
    categories = resource.get("category")
    if not isinstance(categories, list) or not categories:
        return ""

    return _coding_code(categories[0])


def _observation_value(resource: dict[str, Any]) -> str:
    if isinstance(resource.get("valueQuantity"), dict):
        quantity = resource["valueQuantity"]
        value = _string(quantity.get("value"))
        unit = _string(quantity.get("unit") or quantity.get("code"))
        return f"{value} {unit}".strip()

    if isinstance(resource.get("valueCodeableConcept"), dict):
        return _codeable_text(resource["valueCodeableConcept"])

    if "component" in resource and isinstance(resource["component"], list):
        values = []
        for component in resource["component"]:
            if not isinstance(component, dict):
                continue
            name = _codeable_text(component.get("code"))
            quantity = component.get("valueQuantity")
            if isinstance(quantity, dict):
                value = _string(quantity.get("value"))
                unit = _string(quantity.get("unit") or quantity.get("code"))
                values.append(f"{name}: {value} {unit}".strip())
        return "; ".join(values)

    for key in ("valueString", "valueBoolean", "valueInteger", "valueDateTime"):
        if key in resource:
            return _string(resource[key])

    return ""


def _age_years(birth_date: str) -> int | None:
    if len(birth_date) < 10:
        return None

    try:
        year, month, day = (int(part) for part in birth_date[:10].split("-"))
    except ValueError:
        return None

    today = date.today()
    age = today.year - year
    if (today.month, today.day) < (month, day):
        age -= 1

    return age


def _resource_id_sort_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def _string(value: Any, default: str = "") -> str:
    if value is None:
        return default

    return str(value)
