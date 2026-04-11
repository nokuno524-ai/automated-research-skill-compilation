"""Tests for Paper-to-Skill Pipeline."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from extractor import parse_markdown_paper, content_to_dict, extract_arxiv_id
from synthesizer import synthesize_from_content
from skill_generator import generate_skill_directory
from validator import validate_skill_directory, format_validation_report


def test_extractor():
    """Test paper content extraction."""
    sample = open(os.path.join(os.path.dirname(__file__), '..', 'examples', 'attention_paper.md')).read()
    content = parse_markdown_paper(sample, url="arxiv.org/abs/1706.03762")
    
    assert content.title == "Attention Is All You Need", f"Title: {content.title}"
    assert len(content.sections) > 0, "No sections extracted"
    assert len(content.equations) > 0, "No equations extracted"
    assert content.arxiv_id == "1706.03762", f"arxiv_id: {content.arxiv_id}"
    print("✓ Extractor test passed")


def test_synthesizer():
    """Test method synthesis."""
    sample = open(os.path.join(os.path.dirname(__file__), '..', 'examples', 'lora_paper.md')).read()
    content = parse_markdown_paper(sample, url="arxiv.org/abs/2106.09685")
    spec = synthesize_from_content(content_to_dict(content))
    
    assert spec.name, "No method name"
    assert spec.category, "No category"
    assert spec.summary, "No summary"
    assert len(spec.key_equations) > 0, "No equations extracted"
    print(f"✓ Synthesizer test passed: {spec.name} ({spec.category})")


def test_full_pipeline():
    """Test the full pipeline on all example papers."""
    examples_dir = os.path.join(os.path.dirname(__file__), '..', 'examples')
    papers = [f for f in os.listdir(examples_dir) if f.endswith('.md')]
    
    for paper_file in papers:
        paper_path = os.path.join(examples_dir, paper_file)
        sample = open(paper_path).read()
        
        content = parse_markdown_paper(sample, url=f"arxiv.org/abs/0000.00000")
        spec = synthesize_from_content(content_to_dict(content))
        
        out_dir = tempfile.mkdtemp(prefix=f"p2s_test_{paper_file.replace('.md', '')}_")
        generate_skill_directory(json.loads(json.dumps(vars(spec))), out_dir)
        
        result = validate_skill_directory(out_dir)
        report = format_validation_report(result, out_dir)
        
        print(f"\n{report}")
        assert result.has_skill_md, f"{paper_file}: Missing SKILL.md"
        assert result.has_method_script, f"{paper_file}: Missing method.py"
        assert result.completeness_score >= 0.5, f"{paper_file}: Low completeness {result.completeness_score}"
    
    print(f"\n✓ Full pipeline test passed for {len(papers)} papers")


def test_arxiv_id_extraction():
    """Test arXiv ID parsing."""
    assert extract_arxiv_id("https://arxiv.org/abs/1706.03762") == "1706.03762"
    assert extract_arxiv_id("https://arxiv.org/pdf/2106.09685") == "2106.09685"
    assert extract_arxiv_id("1706.03762") == "1706.03762"
    print("✓ arXiv ID extraction test passed")


if __name__ == "__main__":
    test_arxiv_id_extraction()
    test_extractor()
    test_synthesizer()
    test_full_pipeline()
    print("\n✅ All tests passed!")
