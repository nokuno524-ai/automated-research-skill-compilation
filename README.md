# Paper-to-Skill Pipeline (P2S)

Automated pipeline that converts research papers into structured, validated skill artifacts for AI agent consumption.

## Setup Instructions

Ensure you have Python 3.8+ installed. Install the necessary dependencies, especially `torch` and `numpy` which are required for validation tests.

```bash
# Install required dependencies
pip install torch numpy pytest

# Set PYTHONPATH
export PYTHONPATH=src
```

## Quick Start / Usage Examples

```bash
# Run on a local markdown paper
python src/pipeline.py examples/attention_paper.md -o output/transformer-skill

# Run on a local LoRA paper
python src/pipeline.py examples/lora_paper.md -o output/lora-skill

# Run with LLM enhanced extraction (Future/Mocked)
python src/pipeline.py examples/lora_paper.md -o output/lora-skill --use_llm

# Run all automated tests
PYTHONPATH=src pytest tests/
```

## Troubleshooting

- **`ModuleNotFoundError: No module named 'torch'`**: Make sure you have `torch` installed via `pip install torch`. The validation stage executes generated scripts which require it.
- **File not found errors**: Ensure the path to the paper (`examples/attention_paper.md`) is correct and relative to your current working directory.
- **Validation fails functionally**: Check `output/<skill-name>/scripts/method.py` to ensure the generated code has valid syntax and logic.

## Architecture

```
Paper → Content Extraction → Method Synthesis → Skill Generation → Validation
```

1. **Content Extraction** (`src/extractor.py`): Parse markdown/HTML papers into structured content.
2. **Method Synthesis** (`src/synthesizer.py`): Extract method specifications from content.
3. **Skill Generation** (`src/skill_generator.py`): Generate SKILL.md, scripts, and references.
4. **Validation** (`src/validator.py`): Validate generated skills against quality criteria. This includes automated checking for:
   - **Syntax correctness** using `ast.parse`.
   - **Functional correctness** by executing validation tests.
   - **Security** by ensuring no unsafe imports (e.g. `os`, `sys`, `subprocess`) are in the generated code.

## Output Structure

```
output/transformer-skill/
├── SKILL.md                  # Structured skill document
├── README.md                 # Overview
├── scripts/
│   ├── method.py            # Python implementation skeleton
│   └── validate.py          # Validation tests
└── references/
    └── method_spec.json     # Extracted method specification
```

## Related Work

- **PaperCoder/Paper2Code** (Seo et al., 2025) — Paper → code generation
- **AutoP2C** (2025) — Multimodal paper → code
- **AI Scientist V2** (Sakana AI, 2025) — End-to-end autonomous research
- **AutoResearch** (Karpathy, 2025) — Autonomous ML experimentation

## Novelty

P2S is the first pipeline that compiles papers into **validated, composable skill artifacts** for AI agent consumption, going beyond code generation to structured knowledge reuse.

## License

MIT
