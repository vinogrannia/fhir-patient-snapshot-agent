"""Small FHIR R4 client for the Patient Snapshot Agent."""

from __future__ import annotations

import os
import base64
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import load_dotenv


DEFAULT_FHIR_BASE_URL = "http://localhost:32783/fhir/r4"


class FhirClientError(RuntimeError):
    """Raised when the FHIR server cannot satisfy a request."""


@dataclass(frozen=True)
class FhirClient:
    """HTTP client for an InterSystems IRIS for Health FHIR R4 endpoint."""

    base_url: str = DEFAULT_FHIR_BASE_URL
    timeout_seconds: float = 15.0
    username: str | None = None
    password: str | None = None

    @classmethod
    def from_env(cls) -> "FhirClient":
        """Create a client using FHIR_BASE_URL and optional Basic Auth config."""

        load_dotenv()
        return cls(
            base_url=os.getenv("FHIR_BASE_URL", DEFAULT_FHIR_BASE_URL),
            username=os.getenv("FHIR_USERNAME"),
            password=os.getenv("FHIR_PASSWORD"),
        )

    def get_resource(self, resource_type: str, resource_id: str) -> dict[str, Any]:
        """Fetch a single FHIR resource by type and ID."""

        return self._get(f"{resource_type}/{resource_id}")

    def search(self, resource_type: str, **params: str) -> dict[str, Any]:
        """Search a FHIR resource collection and return the raw Bundle."""

        return self._get(resource_type, params=params)

    def get_patient_snapshot_resources(self, patient_id: str) -> dict[str, Any]:
        """Fetch the core resources used by the first patient snapshot workflow."""

        patient_ref = f"Patient/{patient_id}"
        return {
            "patient": self.get_resource("Patient", patient_id),
            "conditions": self.search("Condition", subject=patient_ref),
            "medications": self.search("MedicationRequest", subject=patient_ref),
            "allergies": self.search("AllergyIntolerance", patient=patient_ref),
            "observations": self.search("Observation", subject=patient_ref),
            "encounters": self.search("Encounter", subject=patient_ref),
        }

    def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urlencode(params)}"

        try:
            request = Request(url, headers=self._headers(), method="GET")
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise FhirClientError(
                f"FHIR request failed for {url}: HTTP {exc.code} {exc.reason}. {detail}"
            ) from exc
        except URLError as exc:
            raise FhirClientError(f"FHIR request failed for {url}: {exc}") from exc

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise FhirClientError(f"FHIR response was not JSON for {url}") from exc

        if not isinstance(payload, dict):
            raise FhirClientError(f"FHIR response was not a JSON object for {url}")

        return payload

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/fhir+json"}
        if self.username and self.password:
            token = f"{self.username}:{self.password}".encode("utf-8")
            headers["Authorization"] = f"Basic {base64.b64encode(token).decode('ascii')}"

        return headers


def bundle_entries(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract resources from a FHIR Bundle."""

    entries = bundle.get("entry", [])
    if not isinstance(entries, list):
        return []

    resources: list[dict[str, Any]] = []
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("resource"), dict):
            resources.append(entry["resource"])

    return resources
