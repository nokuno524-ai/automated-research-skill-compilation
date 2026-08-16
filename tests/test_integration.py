import pytest
import tempfile
import os
import json
from src.pipeline import run_pipeline

def test_pipeline_failure_recovery(monkeypatch):
    from src import synthesizer
    def mock_synthesize(*args, **kwargs):
        raise ValueError("Simulated synthesis failure")
    monkeypatch.setattr(synthesizer.SynthesizerStage, "run", mock_synthesize)

    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_pipeline("examples/attention_paper.md", temp_dir)
        assert "error" in result
        assert result["stage"] == "synthesis"
        assert "Simulated synthesis failure" in result["error"]

def test_functional_validation(mock_method_spec):
    from src.skill_generator import generate_skill_directory
    from src.validator import validate_skill_directory

    with tempfile.TemporaryDirectory() as temp_dir:
        generate_skill_directory(mock_method_spec, temp_dir)
        result = validate_skill_directory(temp_dir)
        assert result.overall_pass
        assert len(result.errors) == 0

def test_stage_isolation_extraction(mock_paper_content):
    from src.extractor import content_to_dict
    assert content_to_dict(mock_paper_content)["title"] == "Mock Title"

def test_stage_isolation_synthesis(mock_paper_content):
    from src.synthesizer import synthesize_from_content
    from src.extractor import content_to_dict
    from src import synthesizer
    spec = synthesizer.SynthesizerStage().run(content_to_dict(mock_paper_content))
    assert spec.name == "Mock Title"
    assert spec.summary == "Mock abstract."


def test_end_to_end_pipeline_paper1():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_pipeline("tests/fixtures/paper1.md", temp_dir)
        assert "error" not in result
        assert result["stages"]["extraction"]["title"] == "Minimal Model Architecture"
        assert result["stages"]["synthesis"]["category"] == "architecture"
        assert result["stages"]["validation"]["overall_pass"] is True
        assert result["stages"]["validation"]["syntax_correct"] is True
        assert result["stages"]["validation"]["functional_correct"] is True

def test_end_to_end_pipeline_paper2():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_pipeline("tests/fixtures/paper2.md", temp_dir)
        assert "error" not in result
        assert result["stages"]["extraction"]["title"] == "Training Strategy Optimization"
        assert result["stages"]["synthesis"]["category"] == "optimization"
        assert result["stages"]["validation"]["overall_pass"] is True
