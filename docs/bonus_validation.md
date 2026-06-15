# Bonus Feature Validation Notes

This page lists quick checks for contest bonus features that are implemented as repository artifacts.

## Vector Search

The Streamlit UI includes `Source Context Vector Search` after a snapshot is generated.

Online demo:

```text
https://fhir-patient-snapshot-agent.onrender.com/
```

Local demo:

```powershell
$env:ONLINE_DEMO_MODE="1"
py -m streamlit run app/web_ui.py
```

Suggested query:

```text
medications allergies labs
```

Implementation:

- `app/vector_search.py`
- `app/web_ui.py`
- `tests/test_vector_search.py`

The implementation vectorizes normalized patient snapshot sections with token-frequency vectors and ranks matches with cosine similarity.

## Embedded Python

The repository includes IRIS-compatible ObjectScript classes with Embedded Python methods:

- `src/FHIR/Snapshot/EmbeddedPythonDemo.cls`
- `src/FHIR/Snapshot/EmbeddedVectorSearch.cls`

Example IRIS terminal commands after copying or mounting this repository into an IRIS container:

```objectscript
do $system.OBJ.LoadDir("/path/to/fhir-patient-snapshot-agent/src","ck",,1)
write ##class(FHIR.Snapshot.EmbeddedPythonDemo).Demo(),!
write ##class(FHIR.Snapshot.EmbeddedVectorSearch).Demo(),!
```

Expected behavior:

- `EmbeddedPythonDemo.Demo()` returns a numeric observation value extracted with Python.
- `EmbeddedVectorSearch.Demo()` returns a cosine similarity score computed with Embedded Python.

These classes are included as InterSystems Embedded Python artifacts. The main application runtime remains Python/Streamlit plus the IRIS for Health FHIR Server workflow described in the README.
