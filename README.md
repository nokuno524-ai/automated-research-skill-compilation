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

1. **Content Extraction** (`src/extractor.py`): Parse markdown/HTML papers into structured content
2. **Method Synthesis** (`src/synthesizer.py`): Extract method specifications from content
3. **Skill Generation** (`src/skill_generator.py`): Generate SKILL.md, scripts, and references
4. **Validation** (`src/validator.py`): Validate generated skills against quality criteria

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
