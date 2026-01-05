"""
Syllable extraction toolkit for phonetic name generation.

This package provides tools for extracting syllables from text files using
dictionary-based hyphenation via pyphen's LibreOffice dictionaries.

Main Components:
    - SyllableExtractor: Core extraction class
    - ExtractionResult: Data model for extraction results
    - FileProcessingResult: Result for single file in batch mode
    - BatchResult: Aggregate results for batch processing
    - SUPPORTED_LANGUAGES: Dictionary of supported language codes
    - CLI functions: Interactive and batch command-line interfaces

Usage:
    # Programmatic usage
    from build_tools.syllable_extractor import SyllableExtractor

    extractor = SyllableExtractor('en_US', min_syllable_length=2, max_syllable_length=8)
    syllables = extractor.extract_syllables_from_text("Hello world")

    # CLI usage - Interactive mode
    python -m build_tools.syllable_extractor

    # CLI usage - Batch mode
    python -m build_tools.syllable_extractor --file input.txt --lang en_US
    python -m build_tools.syllable_extractor --source ~/docs/ --recursive --auto

    # Batch processing programmatically
    from build_tools.syllable_extractor import discover_files, process_batch
    from pathlib import Path

    files = discover_files(Path("~/documents"), pattern="*.txt", recursive=True)
    result = process_batch(files, "en_US", min_len=2, max_len=8, output_dir=Path("output"))
"""

# CLI entry point (for python -m usage)
from .cli import (
    discover_files,
    main,
    main_batch,
    main_interactive,
    process_batch,
    process_single_file_batch,
)

# Core extraction functionality
from .extractor import SyllableExtractor

# File I/O operations
from .file_io import DEFAULT_OUTPUT_DIR, generate_output_filename, save_metadata

# Language detection (optional - requires langdetect)
from .language_detection import (
    detect_language_code,
    get_alternative_locales,
    get_default_locale,
    is_detection_available,
    list_supported_languages,
)

# Language configuration
from .languages import (
    SUPPORTED_LANGUAGES,
    get_language_code,
    get_language_name,
    validate_language_code,
)

# Data models
from .models import BatchResult, ExtractionResult, FileProcessingResult

__all__ = [
    # Core classes
    "SyllableExtractor",
    "ExtractionResult",
    "FileProcessingResult",
    "BatchResult",
    # Language utilities
    "SUPPORTED_LANGUAGES",
    "get_language_code",
    "get_language_name",
    "validate_language_code",
    # Language detection (optional)
    "detect_language_code",
    "is_detection_available",
    "get_alternative_locales",
    "get_default_locale",
    "list_supported_languages",
    # File I/O
    "DEFAULT_OUTPUT_DIR",
    "generate_output_filename",
    "save_metadata",
    # CLI - Interactive and Batch
    "main",
    "main_interactive",
    "main_batch",
    # Batch processing utilities
    "discover_files",
    "process_single_file_batch",
    "process_batch",
]

__version__ = "0.1.0"
