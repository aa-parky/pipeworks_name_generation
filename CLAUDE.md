# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`pipeworks_name_generation` is a phonetic name generator that produces pronounceable, neutral
names without imposing semantic meaning. The system is designed to be context-free,
deterministic, and lightweight.

**Critical Design Principle**: Determinism is paramount. The same seed must always produce
the same name. This is essential for games where entity IDs need to map to consistent names
across sessions.

## Quick Command Reference

### Setup and Testing

```bash
# Setup
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt && pip install -e .

# Run tests
pytest

# Code quality
ruff check . && black pipeworks_name_generation/ tests/ && mypy pipeworks_name_generation/
pre-commit run --all-files
```

### Build Tools

```bash
# Extract syllables
python -m build_tools.syllable_extractor --file input.txt --auto

# Normalize syllables
python -m build_tools.syllable_normaliser --source data/corpus/ --output _working/normalized/

# Annotate with features
python -m build_tools.syllable_feature_annotator
```

For detailed command options, see [Development Guide](claude/development.md).

## Documentation Structure

Detailed documentation is organized in the `claude/` directory:

### Core Documentation

- **[Architecture and Design](claude/architecture.md)** - System architecture, design philosophy,
  phases, testing requirements
- **[Development Guide](claude/development.md)** - Setup, testing, code quality, build tool
  commands
- **[CI/CD Pipeline](claude/ci_cd.md)** - GitHub Actions workflows, pre-commit hooks

### Build Tool Documentation

- **[Syllable Extractor](claude/build_tools/syllable_extractor.md)** - Dictionary-based syllable
  extraction (pyphen)
- **[Syllable Normaliser](claude/build_tools/syllable_normaliser.md)** - 3-step normalization
  pipeline
- **[Feature Annotator](claude/build_tools/feature_annotator.md)** - Phonetic feature detection
- **[Analysis Tools](claude/build_tools/analysis_tools.md)** - Post-annotation analysis and
  visualization

## Critical Implementation Rules

### Deterministic RNG

```python
# ALWAYS use Random(seed), NOT random.seed()
rng = random.Random(seed)  # Creates isolated RNG instance
# This avoids global state contamination
```

### Testing Requirements

All changes must maintain determinism:

```python
gen = NameGenerator(pattern="simple")
assert gen.generate(seed=42) == gen.generate(seed=42)
```

## Current State (Phase 1)

The project is in **Phase 1** - a minimal working proof of concept:

- Only "simple" pattern exists
- Syllables hardcoded in `generator.py`
- No YAML loading, phonotactic constraints, or CLI yet
- Zero runtime dependencies (by design)

These are **intentional scope limitations**, not bugs.

## Design Philosophy

**What this system IS:**

- Phonetically-plausible name generator
- Deterministic and seedable
- Context-free and domain-agnostic

**What this system IS NOT:**

- A lore or narrative system
- Genre-specific (fantasy/sci-fi/etc.)
- Semantically aware
- Culturally affiliated

The generator produces **structural** names. Meaning and interpretation are applied by consuming applications.

## Project Configuration

- **Python**: 3.12+
- **License**: GPL-3.0-or-later
- **Line Length**: 100 characters (black/ruff)
- **Type Checking**: mypy enabled (lenient in Phase 1)
- **Testing**: pytest with coverage
- **CI/CD**: GitHub Actions + pre-commit hooks

For detailed configuration, see [Development Guide](claude/development.md) and [CI/CD Pipeline](claude/ci_cd.md).

## Directory Structure

```text
pipeworks_name_generation/    # Core library code
tests/                         # pytest test suite
examples/                      # Usage examples
data/                          # Pattern files (future: YAML configs)
build_tools/                   # Build-time corpus analysis tools
claude/                        # Claude Code documentation (this structure)
docs/                          # Sphinx documentation
_working/                      # Local scratch workspace (not committed)
```

## Adding New Features

When extending beyond Phase 1:

1. **Maintain determinism at all costs**
2. Keep runtime dependencies minimal
3. Reserve heavy processing (NLP, corpus analysis) for build-time tools
4. Pattern data goes in `data/` directory
5. Build tools go in `build_tools/` directory

See [Architecture and Design](claude/architecture.md) for detailed guidance.
