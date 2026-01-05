# pipeworks_name_generation

> A lightweight, phonetic name generator that produces names which *sound right*,
> without imposing what they *mean*.

[![CI](https://github.com/aa-parky/pipeworks_name_generation/actions/workflows/ci.yml/badge.svg)](https://github.com/aa-parky/pipeworks_name_generation/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/aa-parky/pipeworks_name_generation/branch/main/graph/badge.svg)](https://codecov.io/gh/aa-parky/pipeworks_name_generation)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/aa-parky/pipeworks_name_generation)

`pipeworks_name_generation` is a standalone, GPL-3 licensed name generation system based on phonetic and syllabic recombination.

It generates **pronounceable, neutral names** intended to act purely as labels.  
Any narrative, cultural, or semantic meaning is deliberately left to downstream systems.

This project is designed to stand on its own and can be used independently of Pipeworks in
games, simulations, world-building tools, or other generative systems.

---

## Design Goals

- Generate names that are **linguistically plausible**, not random strings
- Avoid direct copying of real names or source material
- Support **deterministic generation** via seeding
- Remain **context-free** and reusable across domains
- Keep runtime dependencies lightweight, predictable, and stable
- Allow different consumers to apply their own meaning and interpretation

---

## Installation

### Requirements

- Python 3.12 or higher
- No runtime dependencies (by design)

### From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/aa-parky/pipeworks_name_generation.git
cd pipeworks_name_generation
pip install -e .
```

For development with testing and documentation tools:

```bash
pip install -e ".[dev]"
```

### From PyPI

> **Note:** Package not yet published to PyPI. Currently in Phase 1 (proof of concept).

Once published, installation will be:

```bash
pip install pipeworks-name-generation
```

### Verify Installation

Run the proof of concept example:

```bash
python examples/minimal_proof_of_concept.py
```

---

## Quick Start

```python
from pipeworks_name_generation import NameGenerator

# Create a generator
gen = NameGenerator(pattern="simple")

# Generate a name deterministically
name = gen.generate(seed=42)
print(name)  # "Kawyn"

# Same seed = same name (always!)
assert gen.generate(seed=42) == name

# Generate multiple unique names
names = gen.generate_batch(count=10, base_seed=1000, unique=True)
print(names)
# ['Borkragmar', 'Kragso', 'Thrakrain', 'Alisra', ...]
```

**Key Feature:** Determinism is guaranteed. The same seed will always produce the same name,
making this ideal for games where entity IDs need consistent names across sessions.

---

## Build Tools

The project includes build-time tools for analyzing and extracting phonetic patterns from text.

### Syllable Extractor

The syllable extractor uses dictionary-based hyphenation to extract syllables from text files.
This is a **build-time tool only** - not used during runtime name generation.

The tool supports two modes:

- **Interactive Mode** - Guided prompts for single-file processing
- **Batch Mode** - Automated processing of multiple files via command-line arguments

#### Interactive Mode

Run the interactive syllable extractor with no arguments:

```bash
python -m build_tools.syllable_extractor
```

The CLI will guide you through:

1. Selecting a language (40+ supported via pyphen) or auto-detection
2. Configuring syllable length constraints (default: 2-8 characters)
3. Choosing an input text file (with tab completion)
4. Extracting and saving syllables with metadata

#### Batch Mode

Process multiple files automatically using command-line arguments:

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
```

**Batch Mode Features:**

- Sequential processing with deterministic file ordering
- Continue-on-error with comprehensive error reporting
- Progress indicators and detailed summaries
- Support for automatic language detection
- Flexible input: single file, multiple files, or directory scanning

**Available Options:**

- `--file PATH` - Process a single file
- `--files PATH [PATH ...]` - Process multiple specific files
- `--source DIR` - Scan a directory for files
- `--lang CODE` - Use specific language code (e.g., en_US, de_DE)
- `--auto` - Automatically detect language from text
- `--pattern PATTERN` - File pattern for directory scanning (default: `*.txt`)
- `--recursive` - Scan directories recursively
- `--min N` - Minimum syllable length (default: 2)
- `--max N` - Maximum syllable length (default: 8)
- `--output DIR` - Output directory (default: `_working/output/`)
- `--quiet` - Suppress progress indicators
- `--verbose` - Show detailed processing information

#### Output Format

Output files are saved to `_working/output/` with timestamped names including language codes:

- `YYYYMMDD_HHMMSS.syllables.LANG.txt` - Unique syllables (one per line, sorted)
- `YYYYMMDD_HHMMSS.meta.LANG.txt` - Extraction metadata and statistics

Examples:

- `20260105_143022.syllables.en_US.txt`
- `20260105_143022.meta.en_US.txt`
- `20260105_143045.syllables.de_DE.txt`

The language code in filenames enables easy sorting and organization when processing
multiple files in different languages.

#### Programmatic Usage

Use the syllable extractor in your own scripts:

**Single-File Extraction:**

```python
from pathlib import Path
from build_tools.syllable_extractor import SyllableExtractor

# Initialize extractor for English (US)
extractor = SyllableExtractor('en_US', min_syllable_length=2, max_syllable_length=8)

# Extract syllables from text
syllables = extractor.extract_syllables_from_text("Hello wonderful world")
print(sorted(syllables))
# ['der', 'ful', 'hel', 'lo', 'won', 'world']

# Extract from a file
syllables = extractor.extract_syllables_from_file(Path('input.txt'))

# Save results
extractor.save_syllables(syllables, Path('output.txt'))
```

**Automatic Language Detection:**

```python
from build_tools.syllable_extractor import SyllableExtractor

# Automatic language detection from text
text = "Bonjour le monde, comment allez-vous?"
syllables, stats, detected_lang = SyllableExtractor.extract_with_auto_language(text)
print(f"Detected language: {detected_lang}")  # "fr"
print(f"Extracted {len(syllables)} syllables")

# Automatic detection from file
syllables, stats, detected_lang = SyllableExtractor.extract_file_with_auto_language(
    Path('german_text.txt')
)
print(f"Detected language: {detected_lang}")  # "de_DE"
```

**Batch Processing:**

```python
from pathlib import Path
from build_tools.syllable_extractor import discover_files, process_batch

# Discover files in a directory
files = discover_files(
    source=Path("~/documents"),
    pattern="*.txt",
    recursive=True
)

# Process batch with automatic language detection
result = process_batch(
    files=files,
    language_code="auto",  # or specific code like "en_US"
    min_len=2,
    max_len=8,
    output_dir=Path("_working/output"),
    quiet=False,
    verbose=False
)

# Check results
print(f"Processed {result.total_files} files")
print(f"Successful: {result.successful}")
print(f"Failed: {result.failed}")
print(result.format_summary())  # Detailed summary report
```

#### Supported Languages

The extractor supports 40+ languages through pyphen's LibreOffice dictionaries:

```python
from build_tools.syllable_extractor import SUPPORTED_LANGUAGES

print(f"{len(SUPPORTED_LANGUAGES)} languages available")
# English (US/UK), German, French, Spanish, Russian, and many more...
```

**Language Auto-Detection:**

The tool includes automatic language detection (requires `langdetect`):

```python
from build_tools.syllable_extractor import (
    detect_language_code,
    is_detection_available,
    list_supported_languages
)

# Check if detection is available
if is_detection_available():
    # Detect language from text
    lang_code = detect_language_code("Hello world, this is a test")
    print(lang_code)  # "en_US"

    # List all supported languages with detection
    languages = list_supported_languages()
    print(f"{len(languages)} languages available")
```

**Key Features:**

- Dictionary-based hyphenation using pyphen (LibreOffice dictionaries)
- Support for 40+ languages
- Automatic language detection (optional, via langdetect)
- Configurable syllable length constraints
- Deterministic extraction (same input = same output)
- Unicode support for accented characters
- Comprehensive metadata and statistics

For complete examples, see `examples/syllable_extraction_example.py`.

---

## Documentation

Full documentation is available and includes:

- **Installation Guide** - Setup instructions
- **Quick Start** - Get started in 5 minutes
- **User Guide** - Comprehensive usage patterns and examples
- **API Reference** - Complete API documentation
- **Development Guide** - Contributing and development setup

### Building Documentation Locally

To build and view the documentation on your machine:

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build the HTML documentation
cd docs
make html

# View the documentation
open build/html/index.html  # macOS
xdg-open build/html/index.html  # Linux
start build/html/index.html  # Windows
```

To clean and rebuild:

```bash
make clean && make html
```

### Online Documentation

> **Coming Soon:** Documentation will be automatically hosted on ReadTheDocs when the repository is public.

---

## Non-Goals

This project deliberately does **not**:

- Encode lore, narrative meaning, or symbolism
- Distinguish between characters, places, organisations, or objects
- Imply cultural, regional, or historical identity
- Enforce genre-specific naming conventions
- Perform runtime natural-language processing
- Act as a world-building or storytelling system

All such concerns are expected to be handled by consuming applications.

---

## Architecture Overview

At a high level, the system works as follows:

1. Phonetic or syllabic units are derived from language corpora  
   *(analysis and build-time only)*
2. These units are stored as neutral, reusable data
3. Names are generated by recombining units using weighted rules and constraints
4. The system emits pronounceable name strings, without semantic awareness

Natural language toolkits (such as NLTK) may be used during **analysis or build phases**,  
but are intentionally excluded from the runtime generation path.

This keeps generation fast, deterministic, and easy to embed.

---

## Usage

`pipeworks_name_generation` is intended to be consumed programmatically.

Typical use cases include:

- Character name generation
- Place and location naming
- Organisation or faction names
- Artefact or object labels
- Procedural or generative world systems

The generator itself does not distinguish between these uses.

---

## Design Philosophy

Names generated by this system are **structural**, not narrative.

They are designed to feel:

- plausible
- consistent
- pronounceable

…but not authoritative.

Meaning, history, and interpretation are applied later, elsewhere.

---

## Licence

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

You are free to use, modify, and distribute this software under the terms of the GPL.  
Improvements and derivative works must remain open under the same licence.

See the `LICENSE` file for full details.

---

## Status

This project is under active development.  
APIs and internal structures may change as the system stabilises.
