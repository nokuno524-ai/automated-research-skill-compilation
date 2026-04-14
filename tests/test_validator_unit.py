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
