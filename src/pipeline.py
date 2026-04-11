"""Paper-to-Skill Pipeline: End-to-end orchestration."""
import json
import os
import sys
import logging
import argparse
import tempfile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_pipeline(paper_input: str, output_dir: str, use_llm: bool = False) -> dict:
    """
    Run the full Paper-to-Skill pipeline.
    
    Args:
        paper_input: Path to markdown/HTML file or arXiv URL
        output_dir: Where to write the skill directory
        use_llm: Whether to use LLM for enhanced extraction (not implemented in prototype)
    
    Returns:
        Dict with pipeline results and validation report
    """
    from extractor import parse_arxiv_html, parse_markdown_paper, content_to_dict, save_content
    from synthesizer import synthesize_from_content, save_spec
    from skill_generator import generate_skill_directory
    from validator import validate_skill_directory, format_validation_report
    
    results = {"stages": {}}
    
    # Stage 1: Content Extraction
    logger.info("Stage 1: Content Extraction")
    
    if paper_input.startswith("http"):
        # Try to fetch from web (placeholder - in production would use web_fetch or arxiv API)
        logger.warning("URL fetching not implemented in prototype. Provide local file.")
        # For prototype, create sample content
        if "1706.03762" in paper_input:
            raw = open("examples/attention_paper.md").read() if os.path.exists("examples/attention_paper.md") else ""
            if not raw:
                raw = """# Attention Is All You Need

## Abstract
We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.

## 1 Introduction
Recurrent models typically factor computation along the symbol positions of the input and output sequences. We propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism.

## 3 Model Architecture
The Transformer uses stacked self-attention and point-wise, fully connected layers for both encoder and decoder.

$$\\text{Attention}(Q, K, V) = \\text{softmax}(\\frac{QK^T}{\\sqrt{d_k}})V$$

$$\\text{MultiHead}(Q, K, V) = \\text{Concat}(\\text{head}_1, ..., \\text{head}_h)W^O$$

where $\\text{head}_i = \\text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$

## 5 Training
We trained the Transformer on the WMT 2014 English-to-German and English-to-French translation tasks.
"""
            content = parse_markdown_paper(raw, url=paper_input)
        else:
            return {"error": "URL fetching not implemented. Provide local file."}
    elif paper_input.endswith('.html'):
        with open(paper_input) as f:
            raw = f.read()
        content = parse_arxiv_html(raw, url=paper_input)
    else:
        with open(paper_input) as f:
            raw = f.read()
        content = parse_markdown_paper(raw, url=paper_input)
    
    content_dict = content_to_dict(content)
    results["stages"]["extraction"] = {
        "title": content.title,
        "num_sections": len(content.sections),
        "num_equations": len(content.equations),
        "arxiv_id": content.arxiv_id,
    }
    logger.info(f"Extracted: {content.title} ({len(content.sections)} sections, {len(content.equations)} equations)")
    
    # Stage 2: Method Synthesis
    logger.info("Stage 2: Method Synthesis")
    spec = synthesize_from_content(content_dict)
    spec_dict = json.loads(json.dumps(vars(spec)))  # serialize dataclass
    results["stages"]["synthesis"] = {
        "method_name": spec.name,
        "category": spec.category,
        "num_equations": len(spec.key_equations),
    }
    logger.info(f"Synthesized: {spec.name} (category: {spec.category})")
    
    # Stage 3: Skill Generation
    logger.info("Stage 3: Skill Generation")
    os.makedirs(output_dir, exist_ok=True)
    generate_skill_directory(spec_dict, output_dir)
    results["stages"]["generation"] = {"output_dir": output_dir}
    logger.info(f"Generated skill at {output_dir}")
    
    # Stage 4: Validation
    logger.info("Stage 4: Validation")
    validation = validate_skill_directory(output_dir)
    report = format_validation_report(validation, output_dir)
    results["stages"]["validation"] = {
        "overall_pass": validation.overall_pass,
        "schema_compliant": validation.schema_compliant,
        "completeness_score": validation.completeness_score,
        "errors": validation.errors,
    }
    print(report)
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paper-to-Skill Pipeline")
    parser.add_argument("input", help="Paper file (markdown/HTML) or arXiv URL")
    parser.add_argument("-o", "--output", default=None, help="Output directory")
    args = parser.parse_args()
    
    output = args.output or tempfile.mkdtemp(prefix="p2s_output_")
    results = run_pipeline(args.input, output)
    
    print(f"\n{'='*50}")
    print(f"Pipeline complete. Output: {output}")
    print(json.dumps(results, indent=2))
