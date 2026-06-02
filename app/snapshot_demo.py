"""Command-line smoke test for fetching patient snapshot resources."""

from __future__ import annotations

import argparse
import json

from app.agent import PatientSnapshotAgent
from app.fhir_client import FhirClient, bundle_entries


AUDIENCE_CHOICES = ["clinician", "ed_doctor", "care_manager", "patient", "family_caregiver"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch FHIR resources for one patient.")
    parser.add_argument("patient_id", help="FHIR Patient resource ID")
    parser.add_argument(
        "--format",
        choices=["counts", "markdown", "prompt", "llm"],
        default="markdown",
        help="Output format for the fetched patient snapshot.",
    )
    parser.add_argument(
        "--audience",
        choices=AUDIENCE_CHOICES,
        default="clinician",
        help="Target audience for prompt and LLM summary modes.",
    )
    args = parser.parse_args()

    if args.format in {"markdown", "prompt", "llm"}:
        client = FhirClient.from_env()
        agent = PatientSnapshotAgent(client)
        if args.format == "prompt":
            mode = "prompt"
        elif args.format == "llm":
            mode = "llm"
        else:
            mode = "deterministic"
        result = agent.run(args.patient_id, mode=mode, audience=args.audience)
        if result.system_instructions and args.format == "prompt":
            print("# System Instructions")
            print()
            print(result.system_instructions)
            print()
            print("# User Prompt")
            print()
        print(result.output)
        return

    client = FhirClient.from_env()
    resources = client.get_patient_snapshot_resources(args.patient_id)

    counts = {
        "patient": 1 if resources.get("patient") else 0,
        "conditions": len(bundle_entries(resources["conditions"])),
        "medications": len(bundle_entries(resources["medications"])),
        "allergies": len(bundle_entries(resources["allergies"])),
        "observations": len(bundle_entries(resources["observations"])),
        "encounters": len(bundle_entries(resources["encounters"])),
        "care_plans": len(bundle_entries(resources["care_plans"])),
    }

    print(json.dumps({"patient_id": args.patient_id, "resource_counts": counts}, indent=2))


if __name__ == "__main__":
    main()
