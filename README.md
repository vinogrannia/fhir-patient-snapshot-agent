# FHIR Patient Snapshot Agent

FHIR Patient Snapshot Agent is an AI-powered clinical summarisation tool built for the InterSystems AI Agents and FHIR Programming Contest.

The application retrieves structured FHIR resources for a selected patient from an InterSystems IRIS for Health FHIR Server and generates a concise clinical summary.

## Contest Idea

The project implements a Smart Patient Summary Generator: an AI agent called inside a FHIR interoperability solution.

Idea link: https://community.intersystems.com/post/intersystems-programming-contest-ai-agents-fhir

## Planned FHIR Resources

- Patient
- Condition
- MedicationRequest
- AllergyIntolerance
- Observation
- Encounter

## Core Workflow

1. A user selects or provides a `patient_id`.
2. The app queries FHIR R4 resources from InterSystems IRIS for Health FHIR Server.
3. A Python layer extracts and normalises relevant clinical context.
4. An LLM-powered summarisation agent generates a structured patient snapshot.
5. The app returns a summary with source FHIR resources used.

## Summary Output

- Patient overview
- Active problems
- Medications
- Allergies
- Recent observations and labs
- Red flags or follow-up points
- Missing information
- Source FHIR resources used

## Safety Note

This project is for demonstration purposes only. It does not provide diagnosis, treatment recommendations, or clinical decision-making. All generated summaries must be verified against the source FHIR data.

## Tech Stack

- InterSystems IRIS for Health / FHIR Server
- Python
- FHIR R4
- LLM-based summarisation
- Docker

## Repository Structure

```text
.
+-- app/
|   +-- README.md
|   +-- fhir_client.py
|   +-- normalizer.py
|   +-- prompt_builder.py
|   +-- summary_renderer.py
|   +-- snapshot_demo.py
+-- tests/
|   +-- test_normalizer.py
+-- data/
|   +-- README.md
+-- docs/
|   +-- day1_fhir_setup.md
+-- .env.example
+-- .gitignore
+-- README.md
+-- requirements.txt
```

## Local FHIR Server Setup

Day 1 setup uses the InterSystems community FHIR template as the reference starting point:

https://github.com/intersystems-community/iris-fhir-template

The project currently expects this FHIR base URL:

```text
http://localhost:32783/fhir/r4
```

The local InterSystems template exposes the FHIR port through Docker. Check `docker ps` and use the host port mapped to container port `52773`. In our first local run this was `32783`.

The local template also requires Basic Auth:

```text
FHIR_USERNAME=_SYSTEM
FHIR_PASSWORD=SYS
```

## Python Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The intended local verification commands are:

```bash
docker compose up --build
curl -i -u _SYSTEM:SYS http://localhost:32783/fhir/r4/metadata
curl -s -u _SYSTEM:SYS http://localhost:32783/fhir/r4/Patient | python3 -m json.tool
curl -s -u _SYSTEM:SYS http://localhost:32783/fhir/r4/Condition | python3 -m json.tool
curl -s -u _SYSTEM:SYS http://localhost:32783/fhir/r4/Observation | python3 -m json.tool
```

Run the local Python snapshot demo:

```bash
FHIR_BASE_URL=http://localhost:32783/fhir/r4 \
FHIR_USERNAME=_SYSTEM \
FHIR_PASSWORD=SYS \
python -m app.snapshot_demo 1
```

Generate an LLM-ready prompt instead of the deterministic demo summary:

```powershell
python -m app.snapshot_demo 1 --format prompt
```

On Windows PowerShell:

```powershell
$env:FHIR_BASE_URL='http://localhost:32783/fhir/r4'
$env:FHIR_USERNAME='_SYSTEM'
$env:FHIR_PASSWORD='SYS'
python -m app.snapshot_demo 1
```

Run tests:

```bash
python -m unittest
```

## Status

Day 1 baseline in progress:

- Project structure created
- FHIR server setup notes drafted
- Python FHIR client scaffolded
- CLI smoke test added
- Deterministic patient snapshot renderer added
- Normalizer unit test added
- Provider-neutral LLM prompt builder added

## Next Steps

1. Add or adapt Docker configuration for an InterSystems IRIS for Health FHIR Server.
2. Verify the local FHIR base URL at `http://localhost:32783/fhir/r4`.
3. Run `python -m app.snapshot_demo <patient_id>` against the local FHIR server.
4. Add tests and sample output for Patient `1`.
5. Add an LLM summarisation layer with explicit safety framing.
