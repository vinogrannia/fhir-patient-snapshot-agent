# Day 1 FHIR Setup

This note tracks the first setup steps for the FHIR Patient Snapshot Agent.

## Goal

Run a local InterSystems IRIS for Health FHIR Server and verify that the app can query FHIR R4 resources for a patient snapshot workflow.

## Reference

The project uses the InterSystems community FHIR template as the starting reference:

https://github.com/intersystems-community/iris-fhir-template

Contest page:

https://community.intersystems.com/post/intersystems-programming-contest-ai-agents-fhir

## Intended Local FHIR Base URL

```text
http://localhost:32783/fhir/r4
```

The InterSystems container listens on `52773` internally. Use `docker ps` to find the host port mapped to `52773/tcp`. In the first local run, Docker mapped it to `32783`.

The local template requires Basic Auth:

```text
username: _SYSTEM
password: SYS
```

## Start the FHIR Server

From the directory containing the Docker Compose file:

```bash
docker compose up --build
```

Keep the terminal open while testing the server.

## Verify FHIR Capability Statement

```bash
curl -i -u _SYSTEM:SYS http://localhost:32783/fhir/r4/metadata
```

Expected result:

- HTTP 200 response
- A FHIR `CapabilityStatement`
- Confirmation that the server is exposing FHIR R4 endpoints

## Verify Resource Endpoints

```bash
curl -s -u _SYSTEM:SYS http://localhost:32783/fhir/r4/Patient | python3 -m json.tool
curl -s -u _SYSTEM:SYS http://localhost:32783/fhir/r4/Condition | python3 -m json.tool
curl -s -u _SYSTEM:SYS http://localhost:32783/fhir/r4/Observation | python3 -m json.tool
```

Useful endpoints for this project:

- `Patient`
- `Condition`
- `MedicationRequest`
- `AllergyIntolerance`
- `Observation`
- `Encounter`

## Day 1 Acceptance Checks

- Docker starts the local FHIR server.
- `GET /fhir/r4/metadata` returns a FHIR capability statement.
- At least one `Patient` search request returns a valid FHIR Bundle.
- The project has a clear README and initial repository structure.

Current verified local endpoint:

```text
http://localhost:32783/fhir/r4
```

Verified patient IDs from the local template include:

```text
1, 2, 3, 496, 585, 948
```

Patient `1` smoke test counts:

```text
Patient: 1
Condition: 5
MedicationRequest: 2
AllergyIntolerance: 0
Observation: 88
Encounter: 14
```

## Notes for Python Client

The first Python client should:

- Accept a configurable `FHIR_BASE_URL`.
- Fetch one patient by ID.
- Search related resources by `patient` or `subject` reference.
- Return raw source resource IDs alongside normalised clinical context.
- Fail clearly when the FHIR server is unavailable.

Smoke test command after the server is running:

```bash
python -m app.snapshot_demo 1
```

## Safety Framing

The app is a summarisation assistant only. It must not diagnose, recommend treatment, or replace clinical judgement. Generated text should always cite or list the source FHIR resources used.
