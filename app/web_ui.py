"""Streamlit web UI for the FHIR Patient Snapshot Agent."""

from __future__ import annotations

from typing import Literal

import streamlit as st

from app.agent import PatientSnapshotAgent
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

    with st.sidebar:
        st.header("Snapshot Settings")
        patient_id = st.text_input("Patient ID", value="1")
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

    if not generate:
        _render_landing_state()
        return

    if not patient_id.strip():
        st.error("Enter a FHIR Patient resource ID.")
        return

    mode = _agent_mode(mode_label)
    audience = AUDIENCE_LABELS[audience_label]

    try:
        with st.spinner("Fetching FHIR resources and generating snapshot..."):
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
        st.markdown(result.output)


def _render_landing_state() -> None:
    fhir_client = FhirClient.from_env()

    st.subheader("Generate a patient snapshot")
    st.write(
        "Enter a FHIR Patient ID in the sidebar, choose a summary mode, and generate a "
        "snapshot from the local InterSystems IRIS for Health FHIR Server."
    )

    cols = st.columns(3)
    cols[0].metric("Verified Patient", "1")
    cols[1].metric("FHIR Base URL", fhir_client.base_url)
    cols[2].metric("LLM Provider", "Nebius")


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


if __name__ == "__main__":
    main()
