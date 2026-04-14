"""Method Synthesis: Extract structured method specifications from paper content."""
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Hyperparameter:
    """Represents a hyperparameter of a synthesized method."""
    name: str
    description: str
    default_value: str = ""
    value_range: str = ""


@dataclass
class MethodIO:
    """Represents an input or output specification for a method."""
    name: str
    type: str
    description: str = ""


@dataclass
class MethodSpec:
    """Represents a structured specification of a method extracted from a paper."""
    name: str
    category: str  # architecture, training, optimization, loss_function, data_processing, evaluation
    summary: str  # 1-2 sentence description
    description: str  # detailed description
    
    # Algorithm details
    algorithm_steps: list = field(default_factory=list)  # list of step descriptions
    key_equations: list = field(default_factory=list)  # LaTeX strings
    pseudocode: str = ""
    
    # Interface
    inputs: list = field(default_factory=list)  # List[MethodIO]
    outputs: list = field(default_factory=list)  # List[MethodIO]
    hyperparameters: list = field(default_factory=list)  # List[Hyperparameter]
    
    # Dependencies
    depends_on: list = field(default_factory=list)  # other methods/concepts
    
    # Validation
    benchmark_datasets: list = field(default_factory=list)
    evaluation_metrics: list = field(default_factory=list)
    expected_results: str = ""
    
    # Metadata
    paper_title: str = ""
    paper_url: str = ""
    year: int = 0


def synthesize_from_content(paper_content: dict, method_name: str = "", use_llm: bool = False) -> MethodSpec:
    """
    Synthesize a MethodSpec from extracted paper content.
    
    Args:
        paper_content: Parsed content dictionary.
        method_name: Target method name.
        use_llm: Flag indicating if an LLM API should be used for synthesis.
                 If True, attempts an LLM call. Here we use heuristic extraction fallback.

    Returns:
        MethodSpec instance.
    """
    try:
        sections = paper_content.get("sections", [])
        equations = paper_content.get("equations", [])
        abstract = paper_content.get("abstract", "")
        title = paper_content.get("title", "")

        # Find method section (heuristic: look for "method", "approach", "model", "architecture" in section titles)
        method_sections = []
        for sec in sections:
            sec_title = sec.get("title", "").lower()
            if any(kw in sec_title for kw in ["method", "approach", "model", "architecture", "algorithm", "proposed"]):
                method_sections.append(sec)

        method_text = "\n".join(s.get("content", "") for s in method_sections) if method_sections else abstract

        # Extract key equations
        key_eqs = [eq.get("latex", "") for eq in equations if eq.get("latex")]

        # Heuristic category detection
        category = "architecture"
        text_lower = (title + " " + abstract).lower()
        if "loss" in text_lower or "objective" in text_lower:
            category = "loss_function"
        elif "optim" in text_lower or "gradient" in text_lower:
            category = "optimization"
        elif "train" in text_lower and ("strategy" in text_lower or "schedule" in text_lower):
            category = "training"
        elif "data" in text_lower and ("preprocess" in text_lower or "augment" in text_lower):
            category = "data_processing"

        if not method_name:
            method_name = title.split(":")[0].strip() if ":" in title else title

        spec = MethodSpec(
            name=method_name,
            category=category,
            summary=abstract[:300] if abstract else "",
            description=method_text[:2000],
            key_equations=key_eqs[:5],
            paper_title=title,
            paper_url=paper_content.get("url", ""),
        )

        return spec
    except Exception as e:
        logger.error(f"Error synthesizing: {e}")
        return MethodSpec(
            name=method_name or "Unknown",
            category="architecture",
            summary="",
            description=""
        )


def spec_to_dict(spec: MethodSpec) -> dict:
    """
    Convert a MethodSpec to a dictionary.
    """
    return asdict(spec)


def save_spec(spec: MethodSpec, path: str) -> None:
    """
    Save MethodSpec to a JSON file.

    Args:
        spec: The MethodSpec to save.
        path: Destination file path.
    """
    with open(path, 'w') as f:
        json.dump(spec_to_dict(spec), f, indent=2)
    logger.info(f"Saved method spec to {path}")


if __name__ == "__main__":
    from extractor import parse_markdown_paper, content_to_dict
    
    sample = """# Attention Is All You Need

## Abstract
We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.

## 3 Model Architecture
The Transformer follows an encoder-decoder structure using stacked self-attention and point-wise, fully connected layers.

$$\\text{Attention}(Q, K, V) = \\text{softmax}(\\frac{QK^T}{\\sqrt{d_k}})V$$

The encoder maps an input sequence to a sequence of continuous representations.
"""
    content = parse_markdown_paper(sample, url="arxiv.org/abs/1706.03762")
    spec = synthesize_from_content(content_to_dict(content))
    print(json.dumps(spec_to_dict(spec), indent=2)[:2000])
