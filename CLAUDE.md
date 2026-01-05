# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`pipeworks_name_generation` is a phonetic name generator that produces pronounceable, neutral
names without imposing semantic meaning. The system is designed to be context-free,
deterministic, and lightweight.

**Critical Design Principle**: Determinism is paramount. The same seed must always produce
the same name. This is essential for games where entity IDs need to map to consistent names
across sessions.

## Development Commands

### Setup

```bash
# Create virtual environment (Python 3.12+)
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
pip install -e .
```

### Testing

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

### Code Quality

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

### Pre-commit Hooks

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

### Running Examples

```bash
python examples/minimal_proof_of_concept.py
```

### Build Tool Commands

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
```

### Documentation

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
_working/                      # Local scratch workspace (not committed)
  output/                      # Default output directory for build tools
```

## Build Tools

### Syllable Extractor (`build_tools/syllable_extractor.py`)

A build-time tool for extracting syllables from text files using dictionary-based hyphenation
via pyphen. This tool is used to generate syllable lists for pattern development.

**Key Features:**

- Dictionary-based hyphenation using pyphen (LibreOffice dictionaries)
- Support for 40+ languages
- Configurable syllable length constraints
- Deterministic extraction (same input = same output)
- Unicode support for accented characters
- Timestamped dual-file output (syllables + metadata)

**Interactive Usage:**

```bash
python -m build_tools.syllable_extractor
# Prompts for:
# 1. Language selection (by number, name, or code)
# 2. Min/max syllable length (default: 2-8)
# 3. Input file path (with tab completion)
# Output is automatically saved to _working/output/
```

**Batch Mode Usage:**

The syllable extractor supports batch processing for automated workflows. Batch mode is triggered
by providing command-line arguments (when no arguments are provided, interactive mode is used).

```bash
# Process a single file with manual language selection
python -m build_tools.syllable_extractor --file input.txt --lang en_US

# Process a single file with automatic language detection
python -m build_tools.syllable_extractor --file input.txt --auto

# Process multiple specific files
python -m build_tools.syllable_extractor --files book1.txt book2.txt book3.txt --auto

# Scan a directory for files (non-recursive)
python -m build_tools.syllable_extractor --source ~/documents/ --pattern "*.txt" --lang en_US

# Scan a directory recursively with auto-detection
python -m build_tools.syllable_extractor --source ~/corpus/ --recursive --auto

# Use custom syllable length constraints and output directory
python -m build_tools.syllable_extractor \
  --source ~/texts/ \
  --pattern "*.md" \
  --recursive \
  --auto \
  --min 3 \
  --max 6 \
  --output ~/results/

# Quiet mode (suppress progress indicators)
python -m build_tools.syllable_extractor --files *.txt --lang de_DE --quiet

# Verbose mode (show detailed processing information)
python -m build_tools.syllable_extractor --source ~/data/ --auto --verbose
```

**Batch Mode Options:**

Input options (mutually exclusive):

- `--file PATH` - Process a single file
- `--files PATH [PATH ...]` - Process multiple specific files
- `--source DIR` - Scan a directory for files (requires --pattern)

Language options (mutually exclusive, required):

- `--lang CODE` - Use specific language code (e.g., en_US, de_DE)
- `--auto` - Automatically detect language from text content

Directory scanning options:

- `--pattern PATTERN` - File pattern for directory scanning (default: `*.txt`)
- `--recursive` - Scan directories recursively

Extraction parameters:

- `--min N` - Minimum syllable length (default: 2)
- `--max N` - Maximum syllable length (default: 8)
- `--output DIR` - Output directory (default: `_working/output/`)

Output control:

- `--quiet` - Suppress progress indicators
- `--verbose` - Show detailed processing information

**Batch Mode Behavior:**

- **Sequential Processing:** Files are processed one at a time in sorted order (deterministic)
- **Error Handling:** Processing continues even if individual files fail
- **Summary Report:** Displays statistics, successful files, and failures at the end
- **Exit Codes:** Returns 0 if all files succeed, 1 if any failures occur
- **Flat Output:** All output files are saved to a single directory with language codes in filenames

**Programmatic Batch Usage:**

```python
from pathlib import Path
from build_tools.syllable_extractor import (
    discover_files,
    process_batch,
    process_single_file_batch,
    BatchResult,
    FileProcessingResult
)

# Discover files in a directory
files = discover_files(
    source=Path("~/documents"),
    pattern="*.txt",
    recursive=True
)

# Process batch
result: BatchResult = process_batch(
    files=files,
    language_code="en_US",  # or "auto" for detection
    min_len=2,
    max_len=8,
    output_dir=Path("_working/output"),
    quiet=False,
    verbose=False
)

# Check results
print(f"Total: {result.total_files}")
print(f"Successful: {result.successful}")
print(f"Failed: {result.failed}")
print(result.format_summary())

# Process single file programmatically
file_result: FileProcessingResult = process_single_file_batch(
    input_path=Path("input.txt"),
    language_code="auto",
    min_len=3,
    max_len=6,
    output_dir=Path("output"),
    verbose=False
)

if file_result.success:
    print(f"Extracted {file_result.syllables_count} syllables")
    print(f"Detected language: {file_result.language_code}")
else:
    print(f"Error: {file_result.error_message}")
```

**Programmatic Single-File Usage:**

```python
from pathlib import Path
from build_tools.syllable_extractor import (
    SyllableExtractor,
    ExtractionResult,
    generate_output_filename,
    save_metadata
)

# Initialize extractor
extractor = SyllableExtractor('en_US', min_syllable_length=2, max_syllable_length=8)

# Extract syllables from file
syllables = extractor.extract_syllables_from_file(Path('input.txt'))

# Generate timestamped output paths
syllables_path, metadata_path = generate_output_filename()

# Save outputs
extractor.save_syllables(syllables, syllables_path)

# Create and save metadata
result = ExtractionResult(
    syllables=syllables,
    language_code='en_US',
    min_syllable_length=2,
    max_syllable_length=8,
    input_path=Path('input.txt')
)
save_metadata(result, metadata_path)
```

**Output Format:**

Files are saved to `_working/output/` with timestamped names including language codes:

- `YYYYMMDD_HHMMSS.syllables.LANG.txt` - Unique syllables (one per line, sorted, lowercase)
- `YYYYMMDD_HHMMSS.meta.LANG.txt` - Extraction metadata and statistics

Examples:

- `20260105_143022.syllables.en_US.txt`
- `20260105_143022.meta.en_US.txt`
- `20260105_143045.syllables.de_DE.txt`
- `20260105_143045.meta.de_DE.txt`

The language code in filenames enables easy sorting and organization when processing
multiple files in different languages.

Metadata includes:

- Extraction date/time
- Language code
- Syllable length constraints
- Input file path
- Total unique syllables extracted
- Length distribution (with bar chart)
- Sample syllables (first 15)

**Supported Languages:**

The tool supports 40+ languages via pyphen. Common examples:

- `en_US`, `en_GB` - English (US/UK)
- `de_DE`, `de_AT`, `de_CH` - German (Germany/Austria/Switzerland)
- `fr` - French
- `es` - Spanish
- `pt_BR`, `pt_PT` - Portuguese (Brazil/Portugal)
- `ru_RU` - Russian
- Many more (see `SUPPORTED_LANGUAGES` in the code)

**Important Notes:**

- This is a **build-time tool only** - pyphen should NEVER be a runtime dependency
- The extractor is deterministic (same input always produces same output)
- Only extracts syllables from words that pyphen can hyphenate (filters out unsplittable words)
- Case-insensitive processing (all output is lowercase)
- Punctuation and special characters are automatically removed

**Testing:**

```bash
# Run all syllable extractor tests (87 tests total)
pytest tests/test_syllable_extractor.py tests/test_syllable_extractor_batch.py -v

# Run only core extraction tests (33 tests)
pytest tests/test_syllable_extractor.py -v

# Run only batch processing tests (34 tests)
pytest tests/test_syllable_extractor_batch.py -v

# Run only language detection tests (20 tests)
pytest tests/test_language_detection.py -v
```

**Test Coverage:**

Core extraction tests (`test_syllable_extractor.py`):

- Initialization and configuration
- Syllable extraction from text and files
- Length constraint enforcement
- Output file generation
- Metadata formatting
- Edge cases and error handling

Batch processing tests (`test_syllable_extractor_batch.py`):

- File discovery with pattern matching and recursion
- Single file batch processing with error handling
- Multi-file batch processing
- Result aggregation and formatting
- Argument parsing and validation
- Main batch function integration
- End-to-end workflows and determinism

Language detection tests (`test_language_detection.py`):

- ISO code to pyphen locale mapping
- Auto-detection with various languages
- Error handling and fallbacks
- Integration with SyllableExtractor

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

## Project Configuration

- **Python Version**: 3.12+
- **License**: GPL-3.0-or-later (all contributions must remain GPL)
- **Line Length**: 100 characters (black/ruff)
- **Type Checking**: mypy enabled but lenient in Phase 1 (`disallow_untyped_defs = false`)
- **Test Framework**: pytest with coverage reporting
- **Pre-commit Hooks**: Enabled for automated code quality checks
- **CI/CD**: GitHub Actions for testing, linting, security, docs, and builds

## CI/CD Pipeline

### GitHub Actions Workflows

**Main CI Pipeline** (`.github/workflows/ci.yml`):

- **Code Quality**: Ruff linting, Black formatting, mypy type checking
- **Test Suite**: Runs on Ubuntu, macOS, Windows with Python 3.12 and 3.13
- **Security Scan**: Bandit for code security, Safety for dependency vulnerabilities
- **Documentation**: Builds Sphinx docs and checks for excessive warnings
- **Package Build**: Builds distribution packages and validates with twine
- **Coverage**: Uploads coverage reports to Codecov

**Dependency Updates** (`.github/workflows/dependency-update.yml`):

- Runs weekly on Monday at 9:00 AM UTC
- Checks for outdated dependencies
- Creates GitHub issues with update recommendations

### CI Pre-commit Hooks

The project uses pre-commit hooks for automated code quality enforcement:

**File Formatting**:

- Trailing whitespace removal
- End-of-file fixing
- Line ending normalization (LF)

**Code Quality**:

- YAML/TOML/JSON validation
- Python AST checking
- Import sorting (isort)
- Code formatting (Black)
- Linting (Ruff with auto-fix)
- Type checking (mypy for main package)

**Security**:

- Bandit security scanning
- Dependency vulnerability checking (Safety)

**Documentation**:

- Markdown linting (markdownlint)
- Spell checking (codespell)

**Triggers**:

- Pre-commit hooks run automatically on `git commit`
- CI pipeline runs on pushes to `main`/`develop` and on pull requests
- Can be manually triggered via GitHub Actions UI

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
