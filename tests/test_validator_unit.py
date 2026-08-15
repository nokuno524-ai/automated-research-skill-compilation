import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from validator import check_syntax, check_security


def test_check_syntax_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix=".py", delete=False) as f:
        f.write("def foo():\n    pass\n")
        path = f.name

    try:
        assert check_syntax(path) is True
    finally:
        os.remove(path)


def test_check_syntax_invalid():
    with tempfile.NamedTemporaryFile(mode='w', suffix=".py", delete=False) as f:
        f.write("def foo():\npass\n") # Indentation error
        path = f.name

    try:
        assert check_syntax(path) is False
    finally:
        os.remove(path)


def test_check_syntax_empty():
    with tempfile.NamedTemporaryFile(mode='w', suffix=".py", delete=False) as f:
        f.write("")
        path = f.name

    try:
        assert check_syntax(path) is True # Empty file is valid syntax
    finally:
        os.remove(path)


def test_check_functional_runtime_error():
    from validator import check_functional
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "bad_script.py")
        with open(script_path, "w") as f:
            f.write("raise RuntimeError('Boom')")

        assert check_functional(script_path, tmpdir) is False


def test_check_functional_success():
    from validator import check_functional
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "good_script.py")
        with open(script_path, "w") as f:
            f.write("print('Success')\n")

        assert check_functional(script_path, tmpdir) is True


def test_check_security_safe():
    with tempfile.NamedTemporaryFile(mode='w', suffix=".py", delete=False) as f:
        f.write("import math\nimport torch\n\nprint('Safe')")
        path = f.name

    try:
        assert check_security(path) is True
    finally:
        os.remove(path)


def test_check_security_unsafe():
    with tempfile.NamedTemporaryFile(mode='w', suffix=".py", delete=False) as f:
        f.write("import os\nos.system('echo dangerous')\n")
        path = f.name

    try:
        assert check_security(path) is False
    finally:
        os.remove(path)

def test_check_functional_timeout():
    from src.validator import check_functional
    import tempfile
    from unittest.mock import patch
    import subprocess

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "slow_script.py")
        with open(script_path, "w") as f:
            f.write("print('hello')")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="python", timeout=10)
            assert check_functional(script_path, tmpdir) is False

def test_check_security_subprocess():
    from validator import check_security
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix=".py", delete=False) as f:
        f.write("import subprocess\nsubprocess.run(['ls', '-la'])\n")
        path = f.name

    try:
        assert check_security(path) is False
    finally:
        os.remove(path)

def test_check_security_eval():
    from validator import check_security
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix=".py", delete=False) as f:
        f.write("x = eval('1 + 1')\n")
        path = f.name

    try:
        assert check_security(path) is False
    finally:
        os.remove(path)

def test_check_syntax_missing_frontmatter():
    from src.validator import validate_skill_directory
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a basic skill dir with missing YAML frontmatter
        os.makedirs(os.path.join(temp_dir, "scripts"))
        os.makedirs(os.path.join(temp_dir, "references"))

        with open(os.path.join(temp_dir, "SKILL.md"), "w") as f:
            f.write("# Skill\nJust a skill.\n")

        with open(os.path.join(temp_dir, "scripts", "method.py"), "w") as f:
            f.write("def test(): pass\n")

        with open(os.path.join(temp_dir, "scripts", "validate.py"), "w") as f:
            f.write("def val(): pass\n")

        with open(os.path.join(temp_dir, "references", "method_spec.json"), "w") as f:
            f.write('{"name": "test"}') # Invalid schema

        with open(os.path.join(temp_dir, "README.md"), "w") as f:
            f.write("# README\n")

        res = validate_skill_directory(temp_dir)
        assert res.schema_compliant is False
        assert len(res.missing_sections) > 0

def test_check_syntax_invalid_python():
    from src.validator import check_syntax
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix=".py", delete=False) as f:
        f.write("def foo()\n  pass\n") # Missing colon
        path = f.name

    try:
        assert check_syntax(path) is False
    finally:
        os.remove(path)
