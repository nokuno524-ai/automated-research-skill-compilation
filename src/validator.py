"""Validator: Check generated skill artifacts against quality criteria."""
import json
import os
import logging
import ast
import subprocess
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

    # Stage 4 checks
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


def check_syntax(path: str) -> bool:
    try:
        with open(path, "r") as f:
            ast.parse(f.read())
        return True
    except SyntaxError:
        return False
    except Exception:
        return False

def check_security(path: str) -> bool:
    try:
        with open(path, "r") as f:
            code = f.read()
            if "os.system" in code or "subprocess" in code or "exec(" in code or "eval(" in code:
                return False
        return True
    except Exception:
        return False

def check_functional(path: str, tmpdir: str) -> bool:
    try:
        # Run with a strict timeout and no internet theoretically
        env = os.environ.copy()
        proc = subprocess.run(["python", path, "--help"], capture_output=True, timeout=10, cwd=tmpdir, env=env)
        return proc.returncode == 0
    except Exception:
        return False

def validate_skill_directory(skill_dir: str) -> ValidationResult:
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

    # Functional, syntax, and security testing
    scripts_to_check = []
    if result.has_method_script:
        scripts_to_check.append(os.path.join(skill_dir, "scripts", "method.py"))
    if result.has_validation_script:
        scripts_to_check.append(os.path.join(skill_dir, "scripts", "validate.py"))

    # Syntax and security check
    all_syntax_ok = True
    all_security_ok = True
    for script in scripts_to_check:
        if not check_syntax(script):
            result.errors.append(f"Syntax error in script: {os.path.basename(script)}")
            all_syntax_ok = False
        if not check_security(script):
            result.errors.append(f"Security check failed for script: {os.path.basename(script)}")
            all_security_ok = False

    result.syntax_correct = all_syntax_ok and len(scripts_to_check) > 0
    result.security_pass = all_security_ok and len(scripts_to_check) > 0

    val_script_path = os.path.join(skill_dir, "scripts", "validate.py")
    if result.has_validation_script and result.syntax_correct:
        if check_functional(val_script_path, os.path.join(skill_dir, "scripts")):
            result.functional_correct = True
        else:
            result.errors.append("Validation script functional check failed")
            result.functional_correct = False

    # Calculate completeness score with functional tests and schemas
    structure_score = sum([
        result.has_skill_md, result.has_method_script, 
        result.has_validation_script, result.has_spec_json, result.has_readme
    ]) / len(REQUIRED_FILES) if len(REQUIRED_FILES) > 0 else 0.0

    syntax_score = 1.0 if result.syntax_correct else 0.0
    doc_score = len(result.skill_md_sections) / len(REQUIRED_SKILL_SECTIONS) if len(REQUIRED_SKILL_SECTIONS) > 0 else 0.0
    exec_score = 1.0 if result.functional_correct else 0.0
    schema_score = 1.0 if not any("MethodSpec" in e for e in result.errors) else 0.0

    # Attach scores to result (for reporting)
    result.scores = {
        "structure": structure_score,
        "syntax": syntax_score,
        "documentation": doc_score,
        "execution": exec_score,
        "schema": schema_score
    }

    result.completeness_score = (structure_score + syntax_score + doc_score + exec_score + schema_score) / 5.0
    
    # Schema compliance
    result.schema_compliant = len(result.errors) == 0 and result.completeness_score >= 0.7
    
    # Overall pass
    result.overall_pass = (
        result.schema_compliant
        and result.has_skill_md
        and result.has_method_script
        and result.syntax_correct
        and result.security_pass
        and result.completeness_score >= 0.6
    )
    
    return result


def format_validation_report(result: ValidationResult, skill_dir: str) -> str:
    """Format validation result as readable report."""
    lines = [
        f"=== Validation Report: {skill_dir} ===",
        f"Overall: {'✅ PASS' if result.overall_pass else '❌ FAIL'}",
        f"Schema Compliant: {'✅' if result.schema_compliant else '❌'}",
        f"Completeness: {result.completeness_score:.1%}",
        f"Syntax Correct: {'✅' if result.syntax_correct else '❌'}",
        f"Functional Correct: {'✅' if result.functional_correct else '❌'}",
        f"Security Pass: {'✅' if result.security_pass else '❌'}",
        "",
        "Files:",
        f"  SKILL.md: {'✅' if result.has_skill_md else '❌'}",
        f"  scripts/method.py: {'✅' if result.has_method_script else '❌'}",
        f"  scripts/validate.py: {'✅' if result.has_validation_script else '❌'}",
        f"  references/method_spec.json: {'✅' if result.has_spec_json else '❌'}",
        f"  README.md: {'✅' if result.has_readme else '❌'}",
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
