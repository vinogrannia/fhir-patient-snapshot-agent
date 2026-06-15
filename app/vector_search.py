"""Small vector search helper for patient snapshot sections."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from app.normalizer import PatientSnapshotContext


@dataclass(frozen=True)
class SearchDocument:
    title: str
    text: str


@dataclass(frozen=True)
class SearchHit:
    title: str
    text: str
    score: float


def snapshot_documents(context: PatientSnapshotContext) -> list[SearchDocument]:
    """Build searchable sections from a normalized patient snapshot."""

    return [
        SearchDocument(
            "Patient overview",
            f"{context.patient.name} {context.patient.gender} born {context.patient.birth_date}",
        ),
        SearchDocument(
            "Active problems",
            " ".join(f"{item.name} status {item.clinical_status} onset {item.onset}" for item in context.active_conditions)
            or "No active problems found.",
        ),
        SearchDocument(
            "Medications",
            " ".join(f"{item.name} status {item.status} authored {item.authored_on}" for item in context.medications)
            or "No medication requests found.",
        ),
        SearchDocument(
            "Allergies",
            " ".join(f"{item.substance} status {item.clinical_status}" for item in context.allergies)
            or "No allergy intolerance records found.",
        ),
        SearchDocument(
            "Recent observations",
            " ".join(f"{item.name} {item.category} {item.value} {item.effective}" for item in context.recent_observations),
        ),
        SearchDocument(
            "Recent encounters",
            " ".join(f"{item.class_code} {item.status} {item.start}" for item in context.recent_encounters),
        ),
        SearchDocument(
            "Care plans",
            " ".join(f"{item.title} {item.status} {item.period_start} {item.period_end}" for item in context.care_plans)
            or "No care plans found.",
        ),
        SearchDocument("Missing information", " ".join(context.missing_information) or "No missing information identified."),
    ]


def search_snapshot_context(context: PatientSnapshotContext, query: str, limit: int = 3) -> list[SearchHit]:
    """Return the most relevant snapshot sections using cosine similarity."""

    query_vector = _vectorize(query)
    if not query_vector:
        return []

    hits: list[SearchHit] = []
    for document in snapshot_documents(context):
        score = _cosine_similarity(query_vector, _vectorize(f"{document.title} {document.text}"))
        if score > 0:
            hits.append(SearchHit(document.title, document.text, score))

    return sorted(hits, key=lambda item: item.score, reverse=True)[:limit]


def _vectorize(text: str) -> Counter[str]:
    return Counter(_tokenize(text))


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9]+", text) if len(token) > 1]


def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    shared = set(left) & set(right)
    if not shared:
        return 0.0

    dot_product = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot_product / (left_norm * right_norm)
