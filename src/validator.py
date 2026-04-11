"""Validator: Check generated skill artifacts against quality criteria."""
import json
import os
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
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
            
            required_fields = ["name", "category", "summary", "description", "paper_title"]
            for field in required_fields:
                if not spec.get(field):
                    result.errors.append(f"MethodSpec missing required field: {field}")
        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON in method_spec.json: {e}")
    
    # Calculate completeness score
    total_checks = len(REQUIRED_FILES) + len(REQUIRED_SKILL_SECTIONS)
    passed = len(result.skill_md_sections) + sum([
        result.has_skill_md, result.has_method_script, 
        result.has_validation_script, result.has_spec_json, result.has_readme
    ])
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
