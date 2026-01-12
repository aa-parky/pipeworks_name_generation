"""
Corpus directory validation and utilities for Syllable Walker TUI.

This module provides functions for validating corpus directories
without loading the actual corpus data.
"""

from pathlib import Path


def validate_corpus_directory(path: Path) -> tuple[bool, str | None, str | None]:
    """
    Validate that a directory contains valid corpus files.

    Checks for either NLTK or Pyphen corpus structure:
    - nltk_syllables_unique.txt + nltk_syllables_frequencies.json
    - pyphen_syllables_unique.txt + pyphen_syllables_frequencies.json

    Args:
        path: Directory path to validate

    Returns:
        Tuple of (is_valid, corpus_type, error_message)
        - is_valid: True if valid corpus directory
        - corpus_type: "NLTK" or "Pyphen" if valid, None otherwise
        - error_message: Error description if invalid, None otherwise

    Examples:
        >>> validate_corpus_directory(Path("/path/to/20260110_115601_nltk"))
        (True, "NLTK", None)

        >>> validate_corpus_directory(Path("/invalid/path"))
        (False, None, "Directory does not exist")
    """
    # Check directory exists
    if not path.exists():
        return (False, None, "Directory does not exist")

    if not path.is_dir():
        return (False, None, "Path is not a directory")

    # Check for NLTK corpus
    nltk_syllables = path / "nltk_syllables_unique.txt"
    nltk_frequencies = path / "nltk_syllables_frequencies.json"

    if nltk_syllables.exists() and nltk_frequencies.exists():
        # Validate both are files
        if not nltk_syllables.is_file():
            return (False, None, "nltk_syllables_unique.txt is not a file")
        if not nltk_frequencies.is_file():
            return (False, None, "nltk_syllables_frequencies.json is not a file")

        return (True, "NLTK", None)

    # Check for Pyphen corpus
    pyphen_syllables = path / "pyphen_syllables_unique.txt"
    pyphen_frequencies = path / "pyphen_syllables_frequencies.json"

    if pyphen_syllables.exists() and pyphen_frequencies.exists():
        # Validate both are files
        if not pyphen_syllables.is_file():
            return (False, None, "pyphen_syllables_unique.txt is not a file")
        if not pyphen_frequencies.is_file():
            return (False, None, "pyphen_syllables_frequencies.json is not a file")

        return (True, "Pyphen", None)

    # No valid corpus found
    return (
        False,
        None,
        "No corpus files found. Directory must contain either:\n"
        "  - nltk_syllables_unique.txt + nltk_syllables_frequencies.json\n"
        "  - pyphen_syllables_unique.txt + pyphen_syllables_frequencies.json",
    )


def get_corpus_info(path: Path) -> str:
    """
    Get display-friendly corpus information string.

    Args:
        path: Path to corpus directory

    Returns:
        Short description string for UI display

    Examples:
        >>> get_corpus_info(Path("/path/to/20260110_115601_nltk"))
        "NLTK (20260110_115601_nltk)"
    """
    is_valid, corpus_type, error = validate_corpus_directory(path)

    if not is_valid:
        return f"Invalid: {error}"

    # Extract directory name for display
    dir_name = path.name

    return f"{corpus_type} ({dir_name})"
