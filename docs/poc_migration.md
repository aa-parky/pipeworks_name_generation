# Proof of Concept - Phase 1

This directory contains the Phase 1 proof of concept for `pipeworks_name_generation`.

## What's Included

- **`pipeworks_name_generation/`** - Core library with minimal generator
- **`tests/`** - Test suite (pytest)
- **`examples/`** - Usage demonstration
- **`requirements-dev.txt`** - Development dependencies
- **`pyproject.toml`** - Project configuration

## Quick Start

```bash
# From the poc directory:

# 1. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dev dependencies
pip install -r requirements-dev.txt

# 3. Install package in editable mode
pip install -e .

# 4. Run tests
pytest tests/ -v

# 5. Run example
python examples/minimal_proof_of_concept.py
```

## Expected Output

### Tests
```
tests/test_minimal_generation.py::TestBasicGeneration::test_generator_creates_deterministic_names PASSED
tests/test_minimal_generation.py::TestBasicGeneration::test_different_seeds_produce_different_names PASSED
tests/test_minimal_generation.py::TestBasicGeneration::test_generator_accepts_pattern_name PASSED
tests/test_minimal_generation.py::TestBasicGeneration::test_generator_rejects_unknown_pattern PASSED
tests/test_minimal_generation.py::TestBasicGeneration::test_generated_names_are_capitalized PASSED
tests/test_minimal_generation.py::TestBasicGeneration::test_optional_syllable_count PASSED
tests/test_minimal_generation.py::TestBatchGeneration::test_generate_batch_returns_list PASSED
tests/test_minimal_generation.py::TestBatchGeneration::test_generate_batch_unique_names PASSED
tests/test_minimal_generation.py::TestBatchGeneration::test_generate_batch_deterministic PASSED
```

### Example
```
Testing pipeworks_name_generation proof of concept...

Name with seed=42: Thorgrimis
Same seed again:   Thorgrimis
Different seed:    Kalathin

✓ Determinism verified: same seed = same name
✓ Randomness verified: different seeds = different names

Testing batch generation...
Generated 10 names:
   1. Marindel
   2. Soravyn
   3. Kalathin
   ...

✓ Batch generation works!
✓ All unique: True

==================================================
SUCCESS! Proof of concept works.
==================================================
```

## What's Hardcoded (Phase 1)

- Syllables are hardcoded in `generator.py`
- Only "simple" pattern is supported
- No YAML loading yet
- No phonotactic constraints

## Next Steps (Phase 2+)

1. Add YAML pattern loading
2. Create multiple pattern sets
3. Add build tools for syllable extraction
4. Implement phonotactic constraints
5. Add CLI interface

## Migrating to Main Repo

Copy these files to your `pipeworks_name_generation` repository:

```bash
# Copy structure
cp -r pipeworks_name_generation/* /path/to/repo/pipeworks_name_generation/
cp -r tests/* /path/to/repo/tests/
cp -r examples/* /path/to/repo/examples/
cp pyproject.toml /path/to/repo/
cp requirements*.txt /path/to/repo/
```

Then run tests to verify everything works!
