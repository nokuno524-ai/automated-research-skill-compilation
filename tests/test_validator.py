import pytest
import os
import json
import tempfile
from src.validator import validate_skill_directory, ValidationResult

def test_validate_skill_directory_schema():
    with tempfile.TemporaryDirectory() as temp_dir:
        os.makedirs(os.path.join(temp_dir, "references"))
        with open(os.path.join(temp_dir, "references", "method_spec.json"), "w") as f:
            json.dump({"name": "Test", "category": "architecture", "summary": "Sum", "description": "Desc", "paper_title": "Paper"}, f)

        result = validate_skill_directory(temp_dir)
        # Should complain about missing files
        assert result.schema_compliant == False
        assert "Missing required file: SKILL.md" in result.errors
