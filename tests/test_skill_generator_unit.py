import os
import sys
import pytest
from unittest.mock import patch, mock_open

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from skill_generator import generate_skill_directory


def test_generate_skill_directory_io_error():
    spec = {"name": "TestMethod", "category": "architecture"}

    # Mock builtins.open to raise an IOError
    with patch("builtins.open", mock_open()) as mocked_file:
        mocked_file.side_effect = IOError("Mocked IO Error")

        # This shouldn't crash because we added a try...except IOError block
        generate_skill_directory(spec, "/tmp/dummy_dir")

        # We ensure it was actually called and hit the exception block
        assert mocked_file.call_count > 0
