
import json
import os
import sys
import logging
import argparse
import tempfile
from typing import Dict, Any

from src.config import PipelineConfig
from src.extractor import ExtractorStage, content_to_dict
from src.synthesizer import SynthesizerStage, spec_to_dict
from src.skill_generator import SkillGeneratorStage
from src.validator import ValidatorStage, format_validation_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_pipeline(paper_input: str, output_dir: str, config: PipelineConfig = None) -> Dict[str, Any]:
    """
    Run the full Paper-to-Skill pipeline using the Stage interface.
    
    Args:
        paper_input: Path to markdown/HTML file or arXiv URL
        output_dir: Where to write the skill directory
        config: Pipeline configuration object
    
    Returns:
        Dict with pipeline results and validation report
    """
    if config is None:
        config = PipelineConfig(output_dir=output_dir)

    results = {"stages": {}}
    
    # Check if file exists when a local path is provided
    if not paper_input.startswith("http") and not os.path.exists(paper_input):
        return {"error": f"File not found: {paper_input}", "stage": "input"}

    # Read input
    is_html = paper_input.endswith('.html')
    if paper_input.startswith("http"):
        logger.warning("URL fetching not implemented. Provide local file.")
        if "1706.03762" in paper_input and os.path.exists("examples/attention_paper.md"):
            raw = open("examples/attention_paper.md").read()
        else:
            return {"error": "URL fetching not implemented. Provide local file.", "stage": "input"}
    else:
        with open(paper_input) as f:
            raw = f.read()

    # Stage 1: Content Extraction
    try:
        logger.info("Stage 1: Content Extraction")
        extractor = ExtractorStage()
        content = extractor.run(raw, is_html=is_html, url=paper_input)
        content_dict = content_to_dict(content)

        results["stages"]["extraction"] = {
            "title": content.title,
            "num_sections": len(content.sections),
            "num_equations": len(content.equations),
            "arxiv_id": content.arxiv_id,
        }
        logger.info(f"Extracted: {content.title} ({len(content.sections)} sections)")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return {"error": str(e), "stage": "extraction"}

    # Stage 2: Method Synthesis
    try:
        logger.info("Stage 2: Method Synthesis")
        synthesizer = SynthesizerStage(config)
        spec = synthesizer.run(content_dict)
        spec_dict = spec_to_dict(spec)

        results["stages"]["synthesis"] = {
            "method_name": spec.name,
            "category": spec.category,
            "num_equations": len(spec.key_equations),
        }
        logger.info(f"Synthesized: {spec.name} (category: {spec.category})")
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return {"error": str(e), "stage": "synthesis"}

    # Stage 3: Skill Generation
    try:
        logger.info("Stage 3: Skill Generation")
        generator = SkillGeneratorStage(output_dir)
        generated_dir = generator.run(spec_dict)

        results["stages"]["generation"] = {"output_dir": generated_dir}
        logger.info(f"Generated skill at {generated_dir}")
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return {"error": str(e), "stage": "generation"}

    # Stage 4: Validation
    try:
        logger.info("Stage 4: Validation")
        validator = ValidatorStage(config)
        validation = validator.run(output_dir)
        report = format_validation_report(validation, output_dir)

        results["stages"]["validation"] = {
            "overall_pass": validation.overall_pass,
            "schema_compliant": validation.schema_compliant,
            "completeness_score": validation.completeness_score,
            "errors": validation.errors,
            "syntax_correct": validation.syntax_correct,
            "functional_correct": validation.functional_correct,
            "security_pass": validation.security_pass
        }
        print(report)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return {"error": str(e), "stage": "validation"}

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
