"""Validator: Check generated skill artifacts against quality criteria."""
import json
import os
import logging
import ast
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a generated skill directory."""
    schema_compliant: bool = False
    completeness_score: float = 0.0
    has_skill_md: bool = False
    has_method_script: bool = False
    has_validation_script: bool = False
    has_spec_json: bool = False
    has_readme: bool = False
    skill_md_sections: list = field(default_factory=list)
    missing_sections: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    overall_pass: bool = False
    syntax_correct: bool = False
    functional_correct: bool = False
    security_pass: bool = False


REQUIRED_SKILL_SECTIONS = [
    "description",
    "category",
    "usage",
    "key equations",
    "hyperparameters",
    "inputs/outputs",
    "references",
]

REQUIRED_FILES = [
    "SKILL.md",
    "scripts/method.py",
    "scripts/validate.py",
    "references/method_spec.json",
    "README.md",
]



def check_syntax(filepath: str) -> bool:
    """Check if a Python file has valid syntax.

    Args:
        filepath: Path to the Python file.

    Returns:
        True if valid syntax, False otherwise.
    """
    try:
        with open(filepath, 'r') as f:
            source = f.read()
        ast.parse(source)
        return True
    except (SyntaxError, FileNotFoundError, Exception) as e:
        logger.error(f"Syntax check failed for {filepath}: {e}")
        return False


def check_security(filepath: str) -> bool:
    """Check a Python file for forbidden imports.

    Args:
        filepath: Path to the Python file.

    Returns:
        True if no forbidden imports are found, False otherwise.
    """
    forbidden_imports = {'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib', 'requests'}
    try:
        with open(filepath, 'r') as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] in forbidden_imports:
                        return False
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in forbidden_imports:
                    return False
        return True
    except Exception as e:
        logger.error(f"Security check failed for {filepath}: {e}")
        return False


def check_functional(filepath: str, cwd: str, timeout: int = 10) -> bool:
    """Run a Python script in a sandboxed subprocess to check functionality.

    Args:
        filepath: Path to the Python script.
        cwd: Working directory for the subprocess.

    Returns:
        True if the script executes successfully (return code 0), False otherwise.
    """
    import subprocess
    try:
        proc = subprocess.run(
            ["python", filepath],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if proc.returncode != 0:
            logger.error(f"Functional check failed for {filepath}: {proc.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Functional check timed out for {filepath}")
        return False
    except Exception as e:
        logger.error(f"Functional check failed with exception: {e}")
        return False

def validate_skill_directory(skill_dir: str, timeout: int = 10) -> ValidationResult:
    """Validate a generated skill directory."""
    result = ValidationResult()
    
    # Check required files exist
    for f in REQUIRED_FILES:
        path = os.path.join(skill_dir, f)
        if not os.path.exists(path):
            result.errors.append(f"Missing required file: {f}")
        else:
            if f == "SKILL.md":
                result.has_skill_md = True
            elif f == "scripts/method.py":
                result.has_method_script = True
            elif f == "scripts/validate.py":
                result.has_validation_script = True
            elif f == "references/method_spec.json":
                result.has_spec_json = True
            elif f == "README.md":
                result.has_readme = True
    
    # Validate SKILL.md sections
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    if os.path.exists(skill_md_path):
        with open(skill_md_path) as f:
            skill_content = f.read().lower()
        
        for section in REQUIRED_SKILL_SECTIONS:
            if section in skill_content:
                result.skill_md_sections.append(section)
            else:
                result.missing_sections.append(section)
    
    # Validate method_spec.json
    spec_path = os.path.join(skill_dir, "references", "method_spec.json")
    if os.path.exists(spec_path):
        try:
            with open(spec_path) as f:
                spec = json.load(f)
            
            required_fields = {
                "name": str,
                "category": str,
                "summary": str,
                "description": str,
                "paper_title": str,
            }
            for field, type_ in required_fields.items():
                if field not in spec or not spec.get(field):
                    result.errors.append(f"MethodSpec missing required field: {field}")
                elif not isinstance(spec.get(field), type_):
                    result.errors.append(f"MethodSpec field '{field}' has wrong type, expected {type_.__name__}")
        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON in method_spec.json: {e}")


    # Syntax and Security checks
    method_script_path = os.path.join(skill_dir, "scripts", "method.py")
    if result.has_method_script:
        result.syntax_correct = check_syntax(method_script_path)
        if not result.syntax_correct:
            result.errors.append("Syntax error in method script.")

        result.security_pass = check_security(method_script_path)
        if not result.security_pass:
            result.errors.append("Security check failed for method script (forbidden imports).")

    # Functional smoke test using the existing check_functional helper
    val_script_path = os.path.join(skill_dir, "scripts", "validate.py")
    if result.has_validation_script:
        # Use check_functional in a sandboxed way (timeout is inside check_functional)
        # Assuming the validate.py expects to run with cwd=skill_dir/scripts so it can import method.py
        scripts_dir = os.path.join(skill_dir, "scripts")
        result.functional_correct = check_functional(os.path.basename(val_script_path), scripts_dir, timeout=timeout)
        if not result.functional_correct:
            result.errors.append(f"Validation script execution failed or timed out.")


    # Heuristics: Extract file references from SKILL.md and ensure they exist
    if result.has_skill_md:
        try:
            with open(skill_md_path, 'r') as f:
                skill_content = f.read()
            # Look for typical markdown file links: [text](path) or just `path/to/file`
            # For simplicity in this heuristic, check if files mentioned in REQUIRED_FILES are actually referenced
            # if they are not in the standard list.
            # But the requirement says: "LLM-free heuristics (does the skill reference files it actually ships?)"

            # Simple regex to find file paths ending in .py, .json, .md in the SKILL.md
            file_refs = re.findall(r'([a-zA-Z0-9_/\-\.]+\.(?:py|json|md))', skill_content)
            for ref in set(file_refs):
                # Ignore external urls
                if ref.startswith("http"):
                    continue
                # Some references might be just filenames, some might be paths
                # Check if it exists in the skill_dir
                ref_path = os.path.join(skill_dir, ref)
                if not os.path.exists(ref_path):
                    # It might be in scripts/ or references/
                    if os.path.exists(os.path.join(skill_dir, "scripts", ref)):
                        continue
                    if os.path.exists(os.path.join(skill_dir, "references", ref)):
                        continue
                    if ref != "SKILL.md" and ref != "README.md":
                        result.warnings.append(f"SKILL.md references '{ref}' but it was not found in the output directory.")
        except Exception as e:
            logger.error(f"Error checking heuristics: {e}")

    # Calculate completeness score (0-100 scale)
    total_checks = len(REQUIRED_FILES) + len(REQUIRED_SKILL_SECTIONS) + 2  # +2 for schema compliant and functional

    passed = len(result.skill_md_sections) + sum([
        result.has_skill_md, result.has_method_script, 
        result.has_validation_script, result.has_spec_json, result.has_readme
    ])

    passed += 1 if result.functional_correct else 0
    passed += 1 if not any("MethodSpec" in e for e in result.errors) else 0


    result.completeness_score = passed / total_checks if total_checks > 0 else 0.0
    
    # Schema compliance
    result.schema_compliant = len(result.errors) == 0 and result.completeness_score >= 0.7
    
    # Overall pass
    result.overall_pass = (
        result.schema_compliant
        and result.has_skill_md
        and result.has_method_script
        and result.completeness_score >= 0.6
    )
    
    return result


def format_validation_report(result: ValidationResult, skill_dir: str) -> str:
    """Format validation result as readable report."""


    lines = [
        f"=== Validation Report: {skill_dir} ===",
        f"Overall: {'✅ PASS' if result.overall_pass else '❌ FAIL'}",
        f"Schema Compliant: {'✅' if result.schema_compliant else '❌'}",
        f"Completeness Score: {result.completeness_score * 100:.1f}/100",
        "",
        "Files:",
        f"  SKILL.md: {'✅' if result.has_skill_md else '❌'}",
        f"  scripts/method.py: {'✅' if result.has_method_script else '❌'}",
        f"  scripts/validate.py: {'✅' if result.has_validation_script else '❌'}",
        f"  references/method_spec.json: {'✅' if result.has_spec_json else '❌'}",
        f"  README.md: {'✅' if result.has_readme else '❌'}",
        "",
        "Tests:",
        f"  Syntax: {'✅' if result.syntax_correct else '❌'}",
        f"  Security: {'✅' if result.security_pass else '❌'}",
        f"  Functional: {'✅' if result.functional_correct else '❌'}",
        "",
        f"SKILL.md Sections Found: {', '.join(result.skill_md_sections) or 'None'}",
        f"SKILL.md Sections Missing: {', '.join(result.missing_sections) or 'None'}",
    ]


    
    if result.errors:
        lines.append("")
        lines.append("Errors:")
        for e in result.errors:
            lines.append(f"  ❌ {e}")
    
    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in result.warnings:
            lines.append(f"  ⚠️ {w}")
    
    return "\n".join(lines)




class ValidatorStage:
    """Stage 4: Validation."""

    def __init__(self, config=None):
        from src.config import PipelineConfig
        self.config = config or PipelineConfig()

    def run(self, stage_input: str) -> ValidationResult:
        """
        Run the validation stage on the generated skill directory.

        Args:
            stage_input: The path to the generated skill directory.

        Returns:
            The ValidationResult object.
        """
        return validate_skill_directory(stage_input, self.config.timeout_seconds)


if __name__ == "__main__":
    import tempfile
    from extractor import parse_markdown_paper, content_to_dict
    from synthesizer import synthesize_from_content
    from skill_generator import generate_skill_directory
    from dataclasses import asdict
    
    sample = """# Attention Is All You Need

## Abstract
We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.

## 3 Model Architecture
The Transformer follows an encoder-decoder structure.

$$\\text{Attention}(Q, K, V) = \\text{softmax}(\\frac{QK^T}{\\sqrt{d_k}})V$$
"""
    content = parse_markdown_paper(sample, url="arxiv.org/abs/1706.03762")
    spec = synthesize_from_content(content_to_dict(content))
    
    out = tempfile.mkdtemp(prefix="p2s_val_test_")
    generate_skill_directory(asdict(spec), out)
    
    result = validate_skill_directory(out)
    print(format_validation_report(result, out))
