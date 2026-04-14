"""Validator: Check generated skill artifacts against quality criteria."""
import json
import os
import logging
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

    # Functional testing
    val_script_path = os.path.join(skill_dir, "scripts", "validate.py")
    if os.path.exists(val_script_path):
        import subprocess
        try:
            proc = subprocess.run(["python", val_script_path], capture_output=True, text=True, timeout=10)
            if proc.returncode != 0:
                result.errors.append(f"Validation script execution failed: {proc.stderr}")
        except Exception as e:
            result.errors.append(f"Failed to execute validation script: {e}")
    
    # Calculate completeness score with functional tests and schemas
    total_checks = len(REQUIRED_FILES) + len(REQUIRED_SKILL_SECTIONS) + 2  # +2 for schema compliant and no execution errors
    passed = len(result.skill_md_sections) + sum([
        result.has_skill_md, result.has_method_script, 
        result.has_validation_script, result.has_spec_json, result.has_readme
    ])

    no_execution_errors = 1 if not any("Validation script execution failed" in e for e in result.errors) else 0
    passed += no_execution_errors

    schema_ok = 1 if not any("MethodSpec" in e for e in result.errors) else 0
    passed += schema_ok

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
        f"Completeness: {result.completeness_score:.1%}",
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
