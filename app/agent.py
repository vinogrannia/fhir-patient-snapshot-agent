"""Patient snapshot agent orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.fhir_client import FhirClient
from app.normalizer import PatientSnapshotContext, normalize_snapshot
from app.prompt_builder import SYSTEM_INSTRUCTIONS, build_snapshot_prompt
from app.summary_renderer import render_markdown_summary


AgentMode = Literal["deterministic", "prompt"]


@dataclass(frozen=True)
class AgentResult:
    patient_id: str
    mode: AgentMode
    context: PatientSnapshotContext
    output: str
    system_instructions: str | None = None


class PatientSnapshotAgent:
    """Fetch, normalize, and summarize FHIR patient resources."""

    def __init__(self, fhir_client: FhirClient) -> None:
        self.fhir_client = fhir_client

    def run(self, patient_id: str, mode: AgentMode = "deterministic") -> AgentResult:
        raw_resources = self.fhir_client.get_patient_snapshot_resources(patient_id)
        context = normalize_snapshot(raw_resources)

        if mode == "prompt":
            output = build_snapshot_prompt(context)
            system_instructions = SYSTEM_INSTRUCTIONS
        else:
            output = render_markdown_summary(context)
            system_instructions = None

        return AgentResult(
            patient_id=patient_id,
            mode=mode,
            context=context,
            output=output,
            system_instructions=system_instructions,
        )
