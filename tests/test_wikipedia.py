"""Tests for Wikipedia description fetch with mocked urllib."""

import json
from unittest.mock import MagicMock, patch

import pytest

from services.item_service import fetch_wikipedia_description


class TestFetchWikipediaDescription:
    """Tests for fetch_wikipedia_description function."""

    def _mock_urlopen(self, responses):
        """Create a mock urlopen that returns different responses per call.

        responses: list of dicts, each will be JSON-encoded.
        """
        mock = MagicMock()
        side_effects = []
        for resp_data in responses:
            cm = MagicMock()
            cm.__enter__ = MagicMock(return_value=cm)
            cm.__exit__ = MagicMock(return_value=False)
            cm.read.return_value = json.dumps(resp_data).encode("utf-8")
            side_effects.append(cm)
        mock.side_effect = side_effects
        return mock

    @patch("services.item_service.urllib.request.urlopen")
    def test_fetch_returns_description_for_known_item(self, mock_urlopen):
        """fetch_wikipedia_description('Magnesium') returns a non-empty string."""
        opensearch_response = [
            "Magnesium",
            ["Magnesium supplement"],
            [""],
            ["https://en.wikipedia.org/wiki/Magnesium_supplement"],
        ]
        summary_response = {
            "extract": "Magnesium salts are available as a medication. They are used to treat magnesium deficiency. Side effects may include diarrhea.",
        }
        mock_urlopen.side_effect = [
            self._make_context_manager(opensearch_response),
            self._make_context_manager(summary_response),
        ]

        result = fetch_wikipedia_description("Magnesium")

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Magnesium" in result

    @patch("services.item_service.urllib.request.urlopen")
    def test_fetch_returns_none_for_unknown_item(self, mock_urlopen):
        """fetch_wikipedia_description('xyznonexistent123') returns None."""
        opensearch_response = [
            "xyznonexistent123",
            [],
            [],
            [],
        ]
        mock_urlopen.return_value = self._make_context_manager(opensearch_response)

        result = fetch_wikipedia_description("xyznonexistent123")

        assert result is None

    @patch("services.item_service.urllib.request.urlopen")
    def test_fetch_handles_timeout_gracefully(self, mock_urlopen):
        """fetch_wikipedia_description handles network timeout, returns None."""
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("timed out")

        result = fetch_wikipedia_description("Magnesium")

        assert result is None

    @patch("services.item_service.urllib.request.urlopen")
    def test_result_truncated_to_three_sentences(self, mock_urlopen):
        """Result is truncated to at most 3 sentences."""
        opensearch_response = [
            "Magnesium",
            ["Magnesium"],
            [""],
            ["https://en.wikipedia.org/wiki/Magnesium"],
        ]
        summary_response = {
            "extract": "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five.",
        }
        mock_urlopen.side_effect = [
            self._make_context_manager(opensearch_response),
            self._make_context_manager(summary_response),
        ]

        result = fetch_wikipedia_description("Magnesium")

        assert result is not None
        # Count sentences: should be at most 3
        sentences = [s.strip() for s in result.split(". ") if s.strip()]
        assert len(sentences) <= 3

    def _make_context_manager(self, data):
        """Create a context manager mock that returns JSON data."""
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=cm)
        cm.__exit__ = MagicMock(return_value=False)
        cm.read.return_value = json.dumps(data).encode("utf-8")
        return cm
