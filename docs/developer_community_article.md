# Building a FHIR Patient Snapshot Agent with IRIS for Health, Streamlit, and an LLM

## Project Links

- GitHub: https://github.com/vinogrannia/fhir-patient-snapshot-agent
- Online demo: https://fhir-patient-snapshot-agent.onrender.com/
- YouTube demo: https://youtu.be/Hsu10Nnujng

## Overview

FHIR Patient Snapshot Agent is a small open-source application built for the InterSystems AI Agents and FHIR Programming Contest.

The project implements the suggested Smart Patient Summary Generator idea: it retrieves structured FHIR resources for a selected patient and generates a concise, role-specific patient summary.

The goal is not to diagnose or recommend treatment. The agent is a summarisation assistant only, and all generated content must be verified against the source FHIR data.

## How InterSystems IRIS for Health Is Used

The application uses InterSystems IRIS for Health as the FHIR interoperability layer.

In the local setup, IRIS for Health exposes a FHIR R4 API. The Python application queries that API and retrieves patient-related resources including:

- Patient
- Condition
- MedicationRequest
- AllergyIntolerance
- Observation
- Encounter
- CarePlan

The Python app does not read local clinical files directly. The FHIR resources returned by IRIS for Health are treated as the source of truth for the summary.

## Application Workflow

The workflow is:

1. The user enters a FHIR Patient ID.
2. The Python FHIR client queries the IRIS for Health FHIR R4 API.
3. The normalisation layer extracts patient demographics, active and resolved conditions, medications, allergies, recent observations, encounters, and care plans.
4. Observations are grouped into vitals, labs, survey/social history, and other observations.
5. The app can generate either:
   - a deterministic Markdown summary,
   - an LLM prompt preview,
   - or an LLM-generated summary.
6. The UI shows source FHIR resources in a collapsible review section so generated content can be checked against the original data.

## LLM Integration

The LLM integration uses Nebius Token Factory through an OpenAI-compatible chat completions API.

The configured model is:

```text
meta-llama/Llama-3.3-70B-Instruct
```

The prompt is safety-framed. It explicitly asks the model not to diagnose, recommend treatment, create new care plans, suggest medication changes, or infer facts that are not present in the source FHIR context.

The app also supports role-specific summaries for:

- Clinician
- ED doctor
- Care manager
- Patient
- Family caregiver

Each audience uses a different required section template and wording style.

## Streamlit UI

The Streamlit UI lets the user:

- enter a Patient ID,
- choose deterministic summary, LLM prompt preview, or LLM summary,
- choose the target audience,
- generate the patient snapshot,
- review the source FHIR resources used by the agent.

The hosted online demo runs in a public demo mode using bundled Patient 1 data captured from the local IRIS for Health FHIR Server setup. This avoids exposing a private local FHIR endpoint or an LLM API key in the public deployment.

The full live FHIR workflow still runs locally against InterSystems IRIS for Health.

## Docker Usage

Docker is used in two ways:

1. The local InterSystems IRIS for Health FHIR Server is run through the external InterSystems community FHIR template.
2. This repository includes a `Dockerfile` and `docker-compose.demo.yml` to run the Python/Streamlit online demo mode.

The demo container can be started with:

```bash
docker compose -f docker-compose.demo.yml up --build
```

Then the app is available at:

```text
http://localhost:8501
```

## Small Documentation Note Found During Setup

While setting up the local InterSystems community FHIR template, I noticed a small documentation point that may affect first-time users.

The template README shows FHIR API test URLs such as:

```text
http://localhost:32783/fhir/r4/metadata
http://localhost:32783/fhir/r4/Patient/1
```

In my local Docker setup, unauthenticated requests returned:

```text
HTTP/1.1 401 Unauthorized
```

The same endpoints worked when Basic Auth was provided:

```powershell
curl.exe -i -u _SYSTEM:SYS http://localhost:32783/fhir/r4/metadata
curl.exe -i -u _SYSTEM:SYS http://localhost:32783/fhir/r4/Patient/1
```

This looks like a small documentation improvement opportunity: adding an authenticated `curl` example and a note about checking the mapped Docker host port with `docker ps` would make the first FHIR API verification step clearer.

I reported this suggestion here:

https://github.com/intersystems-community/iris-fhir-template/issues/37

## Why This Project Is Useful

FHIR systems often contain the right information, but the information is spread across many resources. A patient snapshot can help a user quickly understand what is available in the source data before reviewing details.

This prototype shows how an AI agent can sit on top of a FHIR interoperability layer and produce a structured summary while keeping source-resource traceability visible.

The most important design choice is safety: the agent summarises source data only. It does not replace clinical judgement.

## Current Status

The project currently includes:

- working FHIR client logic,
- normalisation for multiple FHIR resource types,
- deterministic summary mode,
- LLM prompt preview mode,
- Nebius/OpenAI-compatible LLM summary mode,
- role-specific prompts,
- Streamlit web UI,
- hosted online demo,
- Docker demo deployment,
- unit tests,
- screenshots,
- YouTube demo.

## Conclusion

This was my first InterSystems contest contribution. The project helped me learn how to combine InterSystems IRIS for Health FHIR Server, Python, Streamlit, Docker, and an OpenAI-compatible LLM workflow into a small but functional AI agent.

The result is a practical FHIR Patient Snapshot Agent that demonstrates how structured FHIR data can be transformed into a readable, source-grounded clinical summary.
