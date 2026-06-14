"""Streamlit web UI for the FHIR Patient Snapshot Agent."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Literal

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent import PatientSnapshotAgent
from app.demo_data import demo_agent_result
from app.fhir_client import FhirClient, FhirClientError
from app.llm_provider import LlmProviderError
from app.normalizer import PatientSnapshotContext


UiMode = Literal["deterministic", "prompt", "llm"]


AUDIENCE_LABELS = {
    "Clinician": "clinician",
    "ED doctor": "ed_doctor",
    "Care manager": "care_manager",
    "Patient": "patient",
    "Family caregiver": "family_caregiver",
}


def main() -> None:
    st.set_page_config(
        page_title="FHIR Patient Snapshot Agent",
        layout="wide",
    )

    st.title("FHIR Patient Snapshot Agent")
    st.caption("Clinical summarisation from InterSystems IRIS for Health FHIR resources")
    _inject_compact_markdown_css()
    demo_mode = _online_demo_mode_enabled()

    with st.sidebar:
        st.header("Snapshot Settings")
        patient_id = st.text_input("Patient ID", value="1", disabled=demo_mode)
        mode_label = st.radio(
            "Summary mode",
            options=[
                "Deterministic summary",
                "LLM summary",
                "LLM prompt preview",
            ],
            index=0,
        )
        audience_label = st.selectbox(
            "LLM summary audience",
            options=list(AUDIENCE_LABELS),
            index=0,
        )
        generate = st.button("Generate Snapshot", type="primary", use_container_width=True)

        st.divider()
        st.subheader("Safety")
        st.write(
            "This demo summarises source FHIR data only. It does not diagnose, "
            "recommend treatment, or replace clinical judgement."
        )
        if demo_mode:
            st.info(
                "Online demo mode uses bundled Patient 1 data captured from the local "
                "IRIS for Health FHIR Server demo setup."
            )

    if not generate:
        _render_landing_state(demo_mode)
        return

    if not patient_id.strip():
        st.error("Enter a FHIR Patient resource ID.")
        return

    mode = _agent_mode(mode_label)
    audience = AUDIENCE_LABELS[audience_label]

    try:
        with st.spinner("Fetching FHIR resources and generating snapshot..."):
            if demo_mode:
                result = demo_agent_result(mode, audience)
            else:
                agent = PatientSnapshotAgent(FhirClient.from_env())
                result = agent.run(patient_id.strip(), mode=mode, audience=audience)
    except FhirClientError as exc:
        st.error("FHIR request failed.")
        st.code(str(exc), language="text")
        return
    except LlmProviderError as exc:
        st.error("LLM request failed.")
        st.code(str(exc), language="text")
        return

    _render_context_metrics(result.context)
    if demo_mode:
        st.caption("Online demo mode: bundled Patient 1 context from the local IRIS for Health FHIR Server demo setup.")
    if mode in {"prompt", "llm"}:
        st.caption(f"LLM summary audience: {audience_label}")
    st.info(
        "Summary for demonstration only. Verify all generated content against the listed "
        "FHIR resources before any clinical use."
    )

    if mode == "prompt" and result.system_instructions:
        st.subheader("System Instructions")
        st.code(result.system_instructions, language="text")
        st.subheader("User Prompt")
        st.code(result.output, language="markdown")
    else:
        st.subheader("Patient Snapshot")
        st.markdown(_clean_summary_markdown(result.output))

    if mode != "prompt":
        with st.expander(f"Source FHIR resources used ({len(result.context.source_resources)})"):
            for source in result.context.source_resources:
                st.write(f"- {source.resource_type}/{source.resource_id}")


def _online_demo_mode_enabled() -> bool:
    return os.getenv("ONLINE_DEMO_MODE", "").strip().lower() in {"1", "true", "yes"}


def _render_landing_state(demo_mode: bool = False) -> None:
    fhir_client = FhirClient.from_env()

    st.subheader("Generate a patient snapshot")
    if demo_mode:
        st.write(
            "Choose a summary mode and generate a public demo snapshot from bundled "
            "Patient 1 data captured from the local InterSystems IRIS for Health FHIR Server setup."
        )
    else:
        st.write(
            "Enter a FHIR Patient ID in the sidebar, choose a summary mode, and generate a "
            "snapshot from the local InterSystems IRIS for Health FHIR Server."
        )

    cols = st.columns(3)
    cols[0].metric("Verified Patient", "1")
    cols[1].metric("FHIR Source", "Bundled demo" if demo_mode else fhir_client.base_url)
    cols[2].metric("LLM Provider", "Sample output" if demo_mode else "Nebius")


def _inject_compact_markdown_css() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stMarkdownContainer"] p {
            margin-bottom: 0.35rem;
        }
        [data-testid="stMarkdownContainer"] ul {
            margin-top: 0.1rem;
            margin-bottom: 0.45rem;
            padding-left: 1.25rem;
        }
        [data-testid="stMarkdownContainer"] li {
            margin-bottom: 0.15rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_context_metrics(context: PatientSnapshotContext) -> None:
    cols = st.columns(7)
    cols[0].metric("Patient", context.patient.id)
    cols[1].metric("Active Problems", len(context.active_conditions))
    cols[2].metric("Medications", len(context.medications))
    cols[3].metric("Allergies", len(context.allergies))
    cols[4].metric("Recent Observations", len(context.recent_observations))
    cols[5].metric("Recent Encounters", len(context.recent_encounters))
    cols[6].metric("Care Plans", len(context.care_plans))


def _agent_mode(mode_label: str) -> UiMode:
    if mode_label == "LLM summary":
        return "llm"
    if mode_label == "LLM prompt preview":
        return "prompt"
    return "deterministic"


def _without_source_resources_section(markdown: str) -> str:
    return re.sub(
        r"(?ims)^\s{0,3}(?:#+\s*)?\*{0,2}Source FHIR Resources Used\*{0,2}(?:\s|:|$).*\Z",
        "",
        markdown,
    ).rstrip()


def _clean_summary_markdown(markdown: str) -> str:
    cleaned = _without_source_resources_section(markdown)
    cleaned = _without_inline_resource_ids(cleaned)
    cleaned = _without_empty_bullet_lines(cleaned)
    subsection_labels = [
        "Recent vital-sign observations:",
        "Recent laboratory observations:",
        "Recent survey/social history observations:",
        "Recent observations include:",
        "Recent observations:",
        "Other recent observations:",
        "Recent encounters:",
        "Medications:",
        "Allergies:",
        "The patient has no recorded allergy intolerance records.",
        "Source data contains no allergy intolerance records.",
    ]
    for label in subsection_labels:
        cleaned = re.sub(rf"(?<!\n\n)\s+({re.escape(label)})", rf"\n\n\1", cleaned)

    cleaned = _add_missing_bullets_after_colon_labels(cleaned)
    cleaned = _without_empty_bullet_lines(cleaned)
    return cleaned.rstrip()


def _without_inline_resource_ids(markdown: str) -> str:
    return re.sub(
        r"\b(?:Patient|Condition|MedicationRequest|AllergyIntolerance|Observation|Encounter|CarePlan)/\d+:\s*",
        "",
        markdown,
    )


def _without_empty_bullet_lines(markdown: str) -> str:
    return re.sub("(?m)^\\s*[-*\\u2022]\\s*$\\n?", "", markdown)


def _add_missing_bullets_after_colon_labels(markdown: str) -> str:
    lines = markdown.splitlines()
    fixed: list[str] = []
    in_colon_list = False
    colon_list_started = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            fixed.append(line)
            continue

        if in_colon_list and _looks_like_section_heading(stripped):
            fixed.append(line)
            in_colon_list = stripped.endswith(":")
            colon_list_started = False
            continue

        if in_colon_list and _looks_like_unbulleted_list_item(stripped):
            fixed.append(f"- {stripped}")
            colon_list_started = True
            continue

        if in_colon_list and stripped.startswith(("-", "*")):
            fixed.append(line)
            colon_list_started = True
            continue

        fixed.append(line)
        in_colon_list = stripped.endswith(":")
        colon_list_started = False

    return "\n".join(fixed)


def _looks_like_unbulleted_list_item(text: str) -> bool:
    if text.startswith(("-", "*", "#")):
        return False
    if text.endswith(":"):
        return False
    return True


def _looks_like_section_heading(text: str) -> bool:
    headings = {
        "Patient overview",
        "Patient snapshot",
        "Your snapshot",
        "Immediate orientation",
        "Active problems",
        "Active problems relevant to this snapshot",
        "Health problems listed in the source data",
        "Medications",
        "Medication/allergy verification",
        "Medicines listed in the source data",
        "Medicines and allergies listed in the source data",
        "Allergies",
        "Allergies listed in the source data",
        "Recent observations/labs",
        "Recent encounters and observations",
        "Recent encounters, measurements, and labs",
        "Recent measurements and lab results",
        "Care plans",
        "Care plans present in source data",
        "Care plans listed in the source data",
        "Source-data checks",
        "Source-data notes",
        "Missing information",
    }
    return text.strip("* ") in headings


if __name__ == "__main__":
    main()
