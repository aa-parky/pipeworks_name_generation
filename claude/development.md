# Development Guide

This document covers setup, testing, code quality, and development workflows for the pipeworks_name_generation project.

## Setup

```bash
# Create virtual environment (Python 3.12+)
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
pip install -e .
```

## Testing

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_minimal_generation.py

# Run specific test
pytest tests/test_minimal_generation.py::TestBasicGeneration::test_generator_creates_deterministic_names

# Run tests verbose
pytest -v

# Run tests with coverage report
pytest --cov=pipeworks_name_generation --cov-report=html
```

## Code Quality

```bash
# Lint with ruff
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Type checking with mypy
mypy pipeworks_name_generation/

# Format with black (line length: 100)
black pipeworks_name_generation/ tests/

# Run all code quality checks at once
pre-commit run --all-files
```

## Pre-commit Hooks

```bash
# Install pre-commit hooks (one-time setup)
pip install pre-commit
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files

# Run hooks manually on staged files
pre-commit run

# Update hooks to latest versions
pre-commit autoupdate

# Skip hooks for a commit (use sparingly)
git commit --no-verify
```

## Running Examples

```bash
python examples/minimal_proof_of_concept.py
```

## Build Tool Commands

```bash
# Extract syllables from text (interactive mode)
python -m build_tools.syllable_extractor

# Extract syllables in batch mode - single file
python -m build_tools.syllable_extractor --file input.txt --lang en_US

# Extract syllables in batch mode - multiple files
python -m build_tools.syllable_extractor --files file1.txt file2.txt file3.txt --auto

# Extract syllables in batch mode - directory scan
python -m build_tools.syllable_extractor --source ~/documents/ --pattern "*.txt" --lang en_US

# Extract syllables in batch mode - recursive directory scan with auto-detection
python -m build_tools.syllable_extractor --source ~/corpus/ --recursive --auto

# Extract syllables with custom parameters
python -m build_tools.syllable_extractor --file input.txt --lang de_DE --min 3 --max 6 --output ~/results/

# Run syllable extraction example (programmatic)
python examples/syllable_extraction_example.py

# Test syllable extractor (all tests)
pytest tests/test_syllable_extractor.py tests/test_syllable_extractor_batch.py -v

# Test only batch processing
pytest tests/test_syllable_extractor_batch.py -v

# Normalize syllables through 3-step pipeline (build-time tool)
python -m build_tools.syllable_normaliser --source data/corpus/ --output _working/normalized/

# Normalize syllables recursively with custom parameters
python -m build_tools.syllable_normaliser \
  --source data/ \
  --recursive \
  --min 3 \
  --max 10 \
  --output results/ \
  --verbose

# Test syllable normaliser (40 tests)
pytest tests/test_syllable_normaliser.py -v
```

For detailed documentation on each build tool, see:

- [Syllable Extractor](build_tools/syllable_extractor.md)
- [Syllable Normaliser](build_tools/syllable_normaliser.md)
- [Feature Annotator](build_tools/feature_annotator.md)
- [Analysis Tools](build_tools/analysis_tools.md)

## Documentation

```bash
# Build documentation (fully automated from code docstrings)
cd docs
make html

# View documentation (macOS)
open build/html/index.html

# Clean and rebuild
make clean && make html

# Documentation is automatically generated from code using sphinx-autoapi
# No manual .rst files needed - just write good docstrings!
# The docs are also built automatically on ReadTheDocs when pushed to GitHub
```

## Project Configuration

- **Python Version**: 3.12+
- **License**: GPL-3.0-or-later (all contributions must remain GPL)
- **Line Length**: 100 characters (black/ruff)
- **Type Checking**: mypy enabled but lenient in Phase 1 (`disallow_untyped_defs = false`)
- **Test Framework**: pytest with coverage reporting
- **Pre-commit Hooks**: Enabled for automated code quality checks
- **CI/CD**: GitHub Actions for testing, linting, security, docs, and builds

See also: [CI/CD Documentation](ci_cd.md)
