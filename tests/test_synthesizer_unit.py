import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from synthesizer import synthesize_from_content


def test_synthesize_from_content_success():
    paper_content = {
        "title": "A Great Paper",
        "abstract": "We propose a great method.",
        "sections": [
            {"title": "Proposed Method", "content": "Our method is awesome."}
        ],
        "equations": [
            {"latex": "E = mc^2"}
        ]
    }
    spec = synthesize_from_content(paper_content)
    assert spec.name == "A Great Paper"
    assert spec.summary == "We propose a great method."
    assert "Our method is awesome." in spec.description
    assert "E = mc^2" in spec.key_equations


def test_synthesize_missing_fields_graceful():
    # Pass an empty dict to verify the try...except block catches missing fields
    # or at least handles them gracefully without crashing.
    spec = synthesize_from_content({})
    assert spec.name == ""
    assert spec.summary == ""
    assert spec.description == ""

@patch("synthesizer.logger")
def test_synthesize_llm_api_failure_mock(mock_logger):
    # Test that the synthesize function handles mocked LLM failures gracefully
    # Simulate a failure inside the function by passing a mock object that
    # raises an Exception when .get() is called, representing an unexpected error
    # or LLM network failure.
    from unittest.mock import MagicMock
    mock_paper_content = MagicMock()
    mock_paper_content.get.side_effect = Exception("Mocked LLM API Network Error")

    spec = synthesize_from_content(mock_paper_content, method_name="Mock Method", use_llm=True)

    assert spec.name == "Mock Method"
    assert spec.summary == ""
    assert spec.description == ""
    assert spec.category == "architecture"
    mock_logger.error.assert_called_once()
