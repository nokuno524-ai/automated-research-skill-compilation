import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from synthesizer import synthesize_from_content, SynthesizerStage


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
    spec = SynthesizerStage().run(paper_content)
    assert spec.name == "A Great Paper"
    assert spec.summary == "We propose a great method."
    assert "Our method is awesome." in spec.description
    assert "E = mc^2" in spec.key_equations


def test_synthesize_missing_fields_graceful():
    # Pass an empty dict to verify the try...except block catches missing fields
    # or at least handles them gracefully without crashing.
    spec = SynthesizerStage().run({})
    assert spec.name == ""
    assert spec.summary == ""
    assert spec.description == ""


def test_synthesize_failure_retry_raises():
    from unittest.mock import MagicMock
    mock_paper_content = MagicMock()
    mock_paper_content.get.side_effect = Exception("Mocked Failure")

    with pytest.raises(Exception, match="Mocked Failure"):
        SynthesizerStage().run(mock_paper_content)

