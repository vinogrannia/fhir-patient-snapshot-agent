"""Tests for patient snapshot vector search."""

from __future__ import annotations

import unittest

from app.demo_data import demo_patient_context
from app.vector_search import search_snapshot_context, snapshot_documents


class VectorSearchTest(unittest.TestCase):
    def test_builds_snapshot_documents(self) -> None:
        documents = snapshot_documents(demo_patient_context())

        self.assertGreaterEqual(len(documents), 6)
        self.assertIn("Medications", {document.title for document in documents})
        self.assertIn("Recent observations", {document.title for document in documents})

    def test_search_returns_relevant_section(self) -> None:
        hits = search_snapshot_context(demo_patient_context(), "naproxen medication stopped")

        self.assertTrue(hits)
        self.assertEqual("Medications", hits[0].title)

    def test_empty_query_returns_no_hits(self) -> None:
        self.assertEqual([], search_snapshot_context(demo_patient_context(), ""))


if __name__ == "__main__":
    unittest.main()
