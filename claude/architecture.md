# Architecture and Design

This document covers the architecture, design philosophy, and development phases of the pipeworks_name_generation project.

## Architecture

### Current State (Phase 1 - Proof of Concept)

The project is in **Phase 1**: a minimal working proof of concept with hardcoded syllables.

**Core Components:**

- `pipeworks_name_generation/generator.py` - Contains `NameGenerator` class with hardcoded syllables
- Currently supports only the "simple" pattern
- No external dependencies at runtime (intentional design choice)

**Key Methods:**

- `NameGenerator.generate(seed, syllables=None)` - Generate single name deterministically
- `NameGenerator.generate_batch(count, base_seed, unique=True)` - Batch generation

### Critical Implementation Details

**Deterministic RNG:**

```python
# ALWAYS use Random(seed), NOT random.seed()
rng = random.Random(seed)  # Creates isolated RNG instance
# This avoids global state contamination
```

**Syllable Selection:**

- Currently uses `rng.sample()` without replacement to prevent repetition (e.g., "kakaka")
- Hardcoded syllables in `_SIMPLE_SYLLABLES` list
- Names are capitalized with `.capitalize()` (first letter only)

### Planned Architecture (Future Phases)

**Phase 2+** will add:

1. YAML pattern loading from `data/` directory
2. Multiple pattern sets beyond "simple"
3. Additional build tools in `build_tools/` (syllable extractor already implemented)
4. Phonotactic constraints
5. CLI interface

**Important**: Natural language toolkits (NLTK, etc.) are **build-time only**. They should
never be runtime dependencies. The runtime generator must remain fast and lightweight.

## Directory Structure

```text
pipeworks_name_generation/    # Core library code
tests/                         # pytest test suite
examples/                      # Usage examples
data/                          # Pattern files (future: YAML configs)
build_tools/                   # Build-time corpus analysis tools
  syllable_extractor.py        # Syllable extraction using pyphen (build-time only)
scripts/                       # Utility scripts
docs/                          # Documentation
claude/                        # Claude Code documentation
_working/                      # Local scratch workspace (not committed)
  output/                      # Default output directory for build tools
```

## Design Philosophy

### What This System Is

- A phonetically-plausible name generator
- Deterministic and seedable
- Context-free and domain-agnostic
- Zero runtime dependencies (by design)

### What This System Is NOT

- A lore or narrative system
- Genre-specific (fantasy/sci-fi/etc.)
- Semantically aware
- Culturally or historically affiliated

The generator produces **structural** names. Meaning and interpretation are applied by consuming applications.

## Testing Requirements

All changes must maintain determinism. The following test **must always pass**:

```python
gen = NameGenerator(pattern="simple")
assert gen.generate(seed=42) == gen.generate(seed=42)
```

Batch generation must also be deterministic:

```python
batch1 = gen.generate_batch(count=5, base_seed=42)
batch2 = gen.generate_batch(count=5, base_seed=42)
assert batch1 == batch2
```

## Current Phase Limitations

Phase 1 is intentionally minimal. The following are **hardcoded** and expected:

- Only "simple" pattern exists
- Syllables are hardcoded in generator.py
- No YAML loading
- No phonotactic constraints
- No CLI

Do not treat these as bugs or missing features in Phase 1. They are intentional scope limitations.

## Adding New Features

When extending beyond Phase 1:

1. Maintain determinism at all costs
2. Keep runtime dependencies minimal
3. Reserve heavy processing (NLP, corpus analysis) for build-time tools
4. Pattern data should be in `data/` directory
5. Build tools should be in `build_tools/` directory
6. All patterns must be loadable, not hardcoded
