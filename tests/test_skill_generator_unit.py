import os
import sys
import pytest
from unittest.mock import patch, mock_open

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from skill_generator import generate_skill_directory, SkillGeneratorStage



def test_generate_skill_directory_io_error():
    spec = {"name": "TestMethod", "category": "architecture"}

    with patch("builtins.open", mock_open()) as mocked_file:
        mocked_file.side_effect = IOError("Mocked IO Error")

        with pytest.raises(IOError):
            SkillGeneratorStage("/tmp/dummy_dir").run(spec)

        assert mocked_file.call_count > 0

def test_generate_skill_directory_success(tmpdir):
    spec = {"name": "TestMethod", "category": "architecture"}
    out_dir = str(tmpdir)
    SkillGeneratorStage(out_dir).run(spec)

    assert os.path.exists(os.path.join(out_dir, "SKILL.md"))
    assert os.path.exists(os.path.join(out_dir, "scripts", "method.py"))
