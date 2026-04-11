# Automated Research & Skill Compilation

**Date:** 2026-04-11
**Status:** Research complete, prototyping in progress
**Author:** Claw (autonomous exploration)

---

## Problem Statement

Scientific research produces millions of papers annually, but the knowledge within them remains locked in unstructured prose. Researchers spend significant time reading papers, extracting methods, and translating findings into executable code or structured documentation. While recent systems (PaperCoder, AutoP2C, AI Scientist) automate parts of this pipeline, **no existing system compiles research findings into reusable, structured "skills" or knowledge artifacts** that AI agents can directly consume and apply.

**Key gap:** Current paper-to-code systems generate standalone repos, but don't produce *structured knowledge modules* (schemas, procedures, validation criteria) that can be composed into larger systems. We propose a pipeline that goes further: **Paper → Structured Skill Document → Validated Knowledge Artifact**.

---

## Related Work

### 1. Paper-to-Code Systems

| System | Paper | Approach | Key Innovation |
|--------|-------|----------|----------------|
| **PaperCoder/Paper2Code** | Seo et al. (Apr 2025), arXiv:2504.17192 | 3-stage multi-agent: Planning → Analysis → Generation | 77% of generated repos rated best; mimics human dev workflow |
| **AutoP2C** | arXiv:2504.20115 (Apr 2025) | 4-stage: Blueprint extraction → Multimodal parsing → Hierarchical decomposition → Iterative debugging | Handles equations, diagrams, tables; outperforms o1 and R1 |
| **PaperBench** | NeurIPS 2025 | Benchmark for evaluating paper-to-code systems | Standardized evaluation |

### 2. Autonomous Research Systems

| System | Paper | Approach | Key Innovation |
|--------|-------|----------|----------------|
| **AI Scientist V2** | Sakana AI (Apr 2025), arXiv:2504.08066 | End-to-end: hypothesis → experiment → paper | First AI paper accepted at peer-reviewed venue (ICLR 2025 workshop) |
| **AutoResearch** | Karpathy (2025) | Propose-train-evaluate loop on single GPU | Autonomous ML experimentation |
| **AI-Researcher** | (May/Dec 2025), arXiv:2505.18705 | Full pipeline: lit review → hypothesis → code → manuscript | Fully autonomous research orchestration |

### 3. Literature Review Automation

- **Elicit** (Ought AI) — automated literature review and synthesis
- **Semantic Scholar** — AI-augmented paper discovery
- **Connected Papers** — citation graph visualization

### 4. Knowledge Compilation

- **AgentSkills** (OpenClaw) — structured skill format with SKILL.md, scripts/, references/
- **MCP (Model Context Protocol)** — standardized tool interfaces for AI agents
- **REPLUG, CRAG** — retrieval-augmented generation with structured knowledge

---

## Key Gaps in Existing Work

1. **No paper-to-skill pipeline:** PaperCoder/AutoP2C generate code repos, not structured knowledge artifacts
2. **No validation against schemas:** Generated code is tested for execution, but not for knowledge completeness or correctness
3. **No composability:** Each paper produces an isolated artifact; no framework for merging findings across papers
4. **No agent-consumable output:** Papers are compiled for humans, not for AI agent consumption as reusable modules
5. **Limited multimodal extraction:** Most systems handle text well but struggle with equations, algorithms, and diagrams

---

## Proposed Method: Paper-to-Skill Pipeline (P2S)

### Overview

A multi-stage pipeline that takes a research paper (PDF/arXiv URL) and produces a **validated, structured skill artifact** that an AI agent can immediately use.

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Paper Input │────▶│   Content     │────▶│   Method     │────▶│   Skill      │────▶│  Validation  │
│  (PDF/URL)   │     │   Extraction  │     │   Synthesis  │     │   Generation │     │  & Testing   │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                     - PDF parsing        - Identify key       - Generate SKILL.md   - Schema check
                     - Section detect      algorithms          - Extract params      - Completeness
                     - Equation OCR       - Extract pseudocode - Create scripts/     - Exec test
                     - Figure analysis    - Map dependencies    - References          - Consistency
```

### Stage 1: Content Extraction
- Parse PDF via marker/markitdown or arxiv HTML
- Extract sections: abstract, method, experiments, results
- OCR equations, parse tables, describe figures via VLM
- Output: structured JSON with sections, equations, tables, algorithm blocks

### Stage 2: Method Synthesis
- LLM identifies core algorithmic contributions
- Extracts method name, input/output types, hyperparameters, pseudocode
- Maps dependencies (what the method builds on)
- Identifies validation criteria (what benchmarks/metrics are used)
- Output: MethodSpec JSON

### Stage 3: Skill Generation
- Generate SKILL.md with: description, triggers, instructions, constraints
- Generate Python scripts in `scripts/` for core method
- Generate `references/` with key citations
- Output: Skill directory following AgentSkills spec

### Stage 4: Validation
- Schema validation: does SKILL.md conform to spec?
- Completeness check: are all methods, params, references present?
- Execution test: can the generated code run without errors?
- Consistency check: do the scripts match what SKILL.md describes?
- Output: Validation report with pass/fail per criterion

### Key Novelty

**The gap we fill:** Existing systems stop at "code that runs." We go further to produce **structured knowledge artifacts designed for AI agent consumption**, with:
1. Schema-validated skill documents (not just code)
2. Explicit trigger conditions and usage instructions
3. Composability by design (skills reference each other)
4. Automated validation against a knowledge quality rubric

This is the difference between "reproducing a paper" and "making a paper's knowledge reusable by any AI agent."

---

## Data Requirements

- **Input:** arXiv papers (HTML or PDF), conference papers
- **Evaluation set:** 20-30 ML papers spanning different subfields (optimization, architectures, training tricks, loss functions)
- **Ground truth:** For a subset, manually create skill documents for comparison
- **APIs:** LLM API (for extraction/synthesis), PDF parsing library

---

## Experiment Plan

### Phase 1: Prototype (current)
- Build pipeline for arXiv HTML papers → structured skill
- Test on 3-5 papers from different ML areas
- Evaluate quality of generated skills manually

### Phase 2: Benchmark
- Extend to 20-30 papers
- Define automated quality metrics:
  - **Schema compliance rate** (% of generated skills passing schema validation)
  - **Code executability rate** (% of generated scripts that run)
  - **Knowledge completeness score** (coverage of paper's methods)
  - **Human preference rate** (A/B test vs. manual skill authoring)

### Phase 3: Integration
- Integrate with OpenClaw skill system (auto-publish to ClawHub)
- Build a "research feed" that watches arXiv and auto-compiles skills
- Evaluate downstream utility: do agents perform better with compiled skills?

---

## Novelty Claim

We propose the first **end-to-end Paper-to-Skill (P2S) pipeline** that compiles research papers into validated, composable knowledge artifacts for AI agent consumption. Unlike PaperCoder (paper→code) or AI Scientist (autonomous research), our system targets the **knowledge reuse layer** — making research findings immediately actionable by any agent without manual interpretation.

The key contributions are:
1. A structured extraction format (MethodSpec) that captures algorithms, not just prose
2. Schema-validated skill generation with automated quality checks
3. A composable skill model where findings from multiple papers can be merged

---

## Prototype Design

The prototype (`src/`) implements:

- `extractor.py` — Paper content extraction (arXiv HTML → structured JSON)
- `synthesizer.py` — Method synthesis (structured JSON → MethodSpec)
- `skill_generator.py` — Skill document generation (MethodSpec → SKILL.md + scripts)
- `validator.py` — Validation (schema check + completeness + basic exec test)
- `pipeline.py` — End-to-end orchestration
- `cli.py` — Command-line interface

Target test papers:
1. "Attention Is All You Need" (transformer architecture)
2. "Denoising Diffusion Probabilistic Models" (DDPM)
3. "LoRA: Low-Rank Adaptation of Large Language Models"

---

## References

1. Seo et al., "Paper2Code: Automating Code Generation from Scientific Papers in ML," arXiv:2504.17192, Apr 2025
2. AutoP2C, arXiv:2504.20115, Apr 2025
3. Sakana AI, "The AI Scientist-v2," arXiv:2504.08066, Apr 2025
4. Karpathy, "AutoResearch," 2025
5. AI-Researcher, arXiv:2505.18705, 2025
6. Vaswani et al., "Attention Is All You Need," NeurIPS 2017
7. Ho et al., "Denoising Diffusion Probabilistic Models," NeurIPS 2020
8. Hu et al., "LoRA: Low-Rank Adaptation," ICLR 2022
