"""Patient snapshot agent orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.fhir_client import FhirClient
from app.llm_provider import OpenAICompatibleChatProvider
from app.normalizer import PatientSnapshotContext, normalize_snapshot
from app.prompt_builder import SYSTEM_INSTRUCTIONS, build_snapshot_prompt
from app.summary_renderer import render_markdown_summary


AgentMode = Literal["deterministic", "prompt", "llm"]


@dataclass(frozen=True)
class AgentResult:
    patient_id: str
    mode: AgentMode
    context: PatientSnapshotContext
    output: str
    system_instructions: str | None = None


class PatientSnapshotAgent:
    """Fetch, normalize, and summarize FHIR patient resources."""

    def __init__(
        self,
        fhir_client: FhirClient,
        llm_provider: OpenAICompatibleChatProvider | None = None,
    ) -> None:
        self.fhir_client = fhir_client
        self.llm_provider = llm_provider

    def run(self, patient_id: str, mode: AgentMode = "deterministic") -> AgentResult:
        raw_resources = self.fhir_client.get_patient_snapshot_resources(patient_id)
        context = normalize_snapshot(raw_resources)

        if mode == "prompt":
            output = build_snapshot_prompt(context)
            system_instructions = SYSTEM_INSTRUCTIONS
        elif mode == "llm":
            provider = self.llm_provider or OpenAICompatibleChatProvider.from_env()
            output = provider.generate(
                system_instructions=SYSTEM_INSTRUCTIONS,
                user_prompt=build_snapshot_prompt(context),
            )
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
