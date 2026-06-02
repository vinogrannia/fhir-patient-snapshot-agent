# Screenshots

Place UI screenshots for the project README and contest submission in this directory.

Recommended screenshot:

- `streamlit_patient_snapshot.png` - Streamlit UI after generating Patient `1` with `LLM summary` and audience `ED doctor`.

Suggested capture:

1. Start the local IRIS FHIR Server.
2. Run `py -m streamlit run app/web_ui.py`.
3. Open `http://localhost:8501`.
4. Generate Patient `1` with `LLM summary` and `ED doctor`.
5. Capture the app area showing metrics, the patient snapshot, and collapsed source resources.
