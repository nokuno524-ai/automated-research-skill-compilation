# Paper-to-Skill Pipeline (P2S)

Automated pipeline that converts research papers into structured, validated skill artifacts for AI agent consumption.

## Quick Start

```bash
# Run on a local markdown paper
python src/cli.py examples/attention_paper.md -o output/transformer-skill

# Run on a local LoRA paper
python src/cli.py examples/lora_paper.md -o output/lora-skill

# Run tests
python tests/test_pipeline.py
```

## Architecture

```
Paper → Content Extraction → Method Synthesis → Skill Generation → Validation
```

1. **Content Extraction** (`src/extractor.py`): Parse markdown/HTML papers into structured content. Includes proper multiline abstract processing.
2. **Method Synthesis** (`src/synthesizer.py`): Extract method specifications from content via text-search categorizations.
3. **Skill Generation** (`src/skill_generator.py`): Generate SKILL.md, valid and dynamic scripts, and references.
4. **Validation** (`src/validator.py`): Validate generated skills against quality criteria, schema and execution.

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

## Input/Output Formats
- **Input**: Markdown/HTML strings mapped locally or through raw text feeds.
- **Output**: AgentSkill schema specification that encapsulates the extracted information properly into multiple executable files and schema JSON descriptors (e.g. `method_spec.json`).

## Validation Details

Stage 4 Validation has been completed and enhanced to perform:
1. **Schema Validation**: Validates `method_spec.json` against the required AgentSkill schema fields with strict typing rules.
2. **Functional Testing**: The generated `scripts/validate.py` script is dynamically loaded and executed using Python's `subprocess` to verify functional correctness and absence of import errors.
3. **Quality Scoring**: A completeness score is reported based on documentation details, code logic, and functional success rates.

## Pipeline Orchestrator

The pipeline runs continuously across 4 sequential stages with unified progress reporting and fault tolerance:
- `Stage 1: Extraction`
- `Stage 2: Synthesis`
- `Stage 3: Generation`
- `Stage 4: Validation`

Exceptions in any stage are captured and propagated appropriately, returning a structured summary dict with the failure context.

## Related Work

- **PaperCoder/Paper2Code** (Seo et al., 2025) — Paper → code generation
- **AutoP2C** (2025) — Multimodal paper → code
- **AI Scientist V2** (Sakana AI, 2025) — End-to-end autonomous research
- **AutoResearch** (Karpathy, 2025) — Autonomous ML experimentation

## Novelty

P2S is the first pipeline that compiles papers into **validated, composable skill artifacts** for AI agent consumption, going beyond code generation to structured knowledge reuse.

## License

MIT
