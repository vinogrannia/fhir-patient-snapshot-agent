# Demo Script

This script can be used for a short contest video demo or a written project walkthrough.

## 1. Start the FHIR Server

Open a terminal in the InterSystems FHIR template directory:

```powershell
cd "C:\Users\const\Documents\Anna's docs\iris-challenge-ai-agent"
docker compose up --build
```

Explain:

- The Docker container runs InterSystems IRIS for Health.
- IRIS exposes a FHIR R4 API.
- The container maps the internal FHIR port `52773` to a host port. In this local setup, the host port is `32783`.

## 2. Verify the FHIR API

In another terminal:

```powershell
curl.exe -i -u _SYSTEM:SYS http://localhost:32783/fhir/r4/metadata
curl.exe -i -u _SYSTEM:SYS http://localhost:32783/fhir/r4/Patient/1
```

Explain:

- `/metadata` confirms that the FHIR server is available.
- `/Patient/1` confirms that the demo patient can be retrieved from IRIS.

## 3. Run the Resource Count Smoke Test

Open the agent project:

```powershell
cd "C:\Users\const\Documents\Anna's docs\fhir-patient-snapshot-agent"
python -m app.snapshot_demo 1 --format counts
```

Expected counts:

```text
Patient: 1
Condition: 5
MedicationRequest: 2
AllergyIntolerance: 0
Observation: 88
Encounter: 14
CarePlan: 2
```

Explain:

- The Python agent queries related FHIR resources for Patient `1`.
- The resources are fetched from InterSystems IRIS for Health using FHIR R4 REST endpoints.

## 4. Show the Deterministic Summary

```powershell
python -m app.snapshot_demo 1
```

Explain:

- This mode does not call an LLM.
- It proves that the app can fetch, normalise, and render the patient snapshot using deterministic Python code.
- It is useful as a fallback and for testing.

## 5. Show the LLM Prompt

```powershell
python -m app.snapshot_demo 1 --format prompt --audience ed_doctor
```

Explain:

- The app builds a safety-framed prompt from normalised FHIR data.
- The prompt can be adapted for a target audience such as clinician, ED doctor, care manager, patient, or family caregiver.
- The prompt instructs the model not to diagnose, recommend treatment, or infer facts not present in the source data.
- The prompt includes source FHIR resource IDs for verification.

## 6. Generate the LLM Summary

Confirm that `.env` contains a local Nebius Token Factory key:

```text
LLM_BASE_URL=https://api.tokenfactory.nebius.com/v1
LLM_MODEL=meta-llama/Llama-3.3-70B-Instruct
LLM_API_KEY=...
```

Run:

```powershell
python -m app.snapshot_demo 1 --format llm --audience patient
```

Explain:

- The app calls Nebius Token Factory through an OpenAI-compatible chat completions API.
- The generated summary is grounded in FHIR resources retrieved from IRIS.
- The output includes patient overview, active problems, medications, allergies, recent observations, care plans, source-data verification points, missing information, and source resources used.

## 7. Show the Web UI

Run:

```powershell
py -m streamlit run app/web_ui.py
```

Open the local Streamlit URL, usually:

```text
http://localhost:8501
```

Explain:

- The web UI provides a simple patient ID input.
- The user can choose deterministic summary, LLM summary, or LLM prompt preview.
- The user can select a summary audience.
- The result panel shows the generated patient snapshot.
- The source resource expander lists the FHIR resources used for verification.

## 8. Close With Safety Framing

Mention:

- This is a summarisation assistant only.
- It does not provide diagnosis, treatment recommendations, or clinical decision-making.
- All generated summaries must be verified against the source FHIR data.
