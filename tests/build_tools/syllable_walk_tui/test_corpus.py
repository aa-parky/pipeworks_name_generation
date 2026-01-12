"""
Tests for syllable_walk_tui corpus validation.

Tests validation logic for NLTK and Pyphen corpus directories without loading data.
"""

import json

from build_tools.syllable_walk_tui.corpus import get_corpus_info, validate_corpus_directory


class TestValidateCorpusDirectory:
    """Tests for corpus directory validation."""

    def test_valid_nltk_corpus(self, tmp_path):
        """Test validation of valid NLTK corpus directory."""
        corpus_dir = tmp_path / "nltk_corpus"
        corpus_dir.mkdir()

        # Create required NLTK files
        (corpus_dir / "nltk_syllables_unique.txt").write_text("hel\nlo\nworld\n")
        (corpus_dir / "nltk_syllables_frequencies.json").write_text(
            json.dumps({"hel": 1, "lo": 2, "world": 1})
        )

        is_valid, corpus_type, error = validate_corpus_directory(corpus_dir)

        assert is_valid is True
        assert corpus_type == "NLTK"
        assert error is None

    def test_valid_pyphen_corpus(self, tmp_path):
        """Test validation of valid Pyphen corpus directory."""
        corpus_dir = tmp_path / "pyphen_corpus"
        corpus_dir.mkdir()

        # Create required Pyphen files
        (corpus_dir / "pyphen_syllables_unique.txt").write_text("hel\nlo\nworld\n")
        (corpus_dir / "pyphen_syllables_frequencies.json").write_text(
            json.dumps({"hel": 1, "lo": 2, "world": 1})
        )

        is_valid, corpus_type, error = validate_corpus_directory(corpus_dir)

        assert is_valid is True
        assert corpus_type == "Pyphen"
        assert error is None

    def test_both_corpus_types_present_prefers_nltk(self, tmp_path):
        """Test that NLTK is preferred when both corpus types exist."""
        corpus_dir = tmp_path / "mixed_corpus"
        corpus_dir.mkdir()

        # Create both NLTK and Pyphen files
        (corpus_dir / "nltk_syllables_unique.txt").write_text("nltk\n")
        (corpus_dir / "nltk_syllables_frequencies.json").write_text(json.dumps({"nltk": 1}))
        (corpus_dir / "pyphen_syllables_unique.txt").write_text("pyphen\n")
        (corpus_dir / "pyphen_syllables_frequencies.json").write_text(json.dumps({"pyphen": 1}))

        is_valid, corpus_type, error = validate_corpus_directory(corpus_dir)

        assert is_valid is True
        assert corpus_type == "NLTK"  # Should prefer NLTK
        assert error is None

    def test_missing_unique_file_nltk(self, tmp_path):
        """Test invalid corpus with missing NLTK unique file."""
        corpus_dir = tmp_path / "incomplete_nltk"
        corpus_dir.mkdir()

        # Only frequencies file, missing unique file
        (corpus_dir / "nltk_syllables_frequencies.json").write_text(json.dumps({"test": 1}))

        is_valid, corpus_type, error = validate_corpus_directory(corpus_dir)

        assert is_valid is False
        assert corpus_type is None
        assert "No corpus files found" in error

    def test_missing_frequencies_file_nltk(self, tmp_path):
        """Test invalid corpus with missing NLTK frequencies file."""
        corpus_dir = tmp_path / "incomplete_nltk"
        corpus_dir.mkdir()

        # Only unique file, missing frequencies file
        (corpus_dir / "nltk_syllables_unique.txt").write_text("test\n")

        is_valid, corpus_type, error = validate_corpus_directory(corpus_dir)

        assert is_valid is False
        assert corpus_type is None
        assert "No corpus files found" in error

    def test_missing_unique_file_pyphen(self, tmp_path):
        """Test invalid corpus with missing Pyphen unique file."""
        corpus_dir = tmp_path / "incomplete_pyphen"
        corpus_dir.mkdir()

        # Only frequencies file
        (corpus_dir / "pyphen_syllables_frequencies.json").write_text(json.dumps({"test": 1}))

        is_valid, corpus_type, error = validate_corpus_directory(corpus_dir)

        assert is_valid is False
        assert corpus_type is None
        assert "No corpus files found" in error

    def test_missing_frequencies_file_pyphen(self, tmp_path):
        """Test invalid corpus with missing Pyphen frequencies file."""
        corpus_dir = tmp_path / "incomplete_pyphen"
        corpus_dir.mkdir()

        # Only unique file
        (corpus_dir / "pyphen_syllables_unique.txt").write_text("test\n")

        is_valid, corpus_type, error = validate_corpus_directory(corpus_dir)

        assert is_valid is False
        assert corpus_type is None
        assert "No corpus files found" in error

    def test_nonexistent_directory(self, tmp_path):
        """Test validation of nonexistent directory."""
        nonexistent = tmp_path / "does_not_exist"

        is_valid, corpus_type, error = validate_corpus_directory(nonexistent)

        assert is_valid is False
        assert corpus_type is None
        assert "does not exist" in error.lower()

    def test_file_instead_of_directory(self, tmp_path):
        """Test validation when path points to a file instead of directory."""
        file_path = tmp_path / "not_a_directory.txt"
        file_path.write_text("content")

        is_valid, corpus_type, error = validate_corpus_directory(file_path)

        assert is_valid is False
        assert corpus_type is None
        assert "not a directory" in error.lower()

    def test_empty_directory(self, tmp_path):
        """Test validation of empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        is_valid, corpus_type, error = validate_corpus_directory(empty_dir)

        assert is_valid is False
        assert corpus_type is None
        assert "No corpus files found" in error

    def test_directory_with_wrong_files(self, tmp_path):
        """Test validation of directory with unrelated files."""
        corpus_dir = tmp_path / "wrong_files"
        corpus_dir.mkdir()

        # Create unrelated files
        (corpus_dir / "readme.txt").write_text("readme")
        (corpus_dir / "data.csv").write_text("data")

        is_valid, corpus_type, error = validate_corpus_directory(corpus_dir)

        assert is_valid is False
        assert corpus_type is None
        assert "No corpus files found" in error

    def test_invalid_json_in_frequencies(self, tmp_path):
        """Test that validation still passes even if JSON is malformed (validation doesn't parse)."""
        corpus_dir = tmp_path / "bad_json"
        corpus_dir.mkdir()

        # Create files but with invalid JSON
        (corpus_dir / "nltk_syllables_unique.txt").write_text("test\n")
        (corpus_dir / "nltk_syllables_frequencies.json").write_text("not valid json {{{")

        # Validation only checks file existence, not content
        is_valid, corpus_type, error = validate_corpus_directory(corpus_dir)

        assert is_valid is True
        assert corpus_type == "NLTK"
        assert error is None

    def test_empty_unique_file(self, tmp_path):
        """Test validation with empty unique syllables file."""
        corpus_dir = tmp_path / "empty_unique"
        corpus_dir.mkdir()

        # Create empty files
        (corpus_dir / "nltk_syllables_unique.txt").write_text("")
        (corpus_dir / "nltk_syllables_frequencies.json").write_text("{}")

        # Validation only checks existence, not content
        is_valid, corpus_type, error = validate_corpus_directory(corpus_dir)

        assert is_valid is True
        assert corpus_type == "NLTK"
        assert error is None


class TestGetCorpusInfo:
    """Tests for corpus info string generation."""

    def test_nltk_corpus_info(self, tmp_path):
        """Test corpus info string for NLTK corpus."""
        corpus_dir = tmp_path / "20260110_115601_nltk"
        corpus_dir.mkdir()

        # Create NLTK files
        (corpus_dir / "nltk_syllables_unique.txt").write_text("hel\nlo\nworld\n")
        (corpus_dir / "nltk_syllables_frequencies.json").write_text(json.dumps({"hel": 5}))

        info = get_corpus_info(corpus_dir)

        assert "NLTK" in info
        assert "20260110_115601_nltk" in info

    def test_pyphen_corpus_info(self, tmp_path):
        """Test corpus info string for Pyphen corpus."""
        corpus_dir = tmp_path / "20260110_143022_pyphen"
        corpus_dir.mkdir()

        # Create Pyphen files
        (corpus_dir / "pyphen_syllables_unique.txt").write_text("py\nphen\n")
        (corpus_dir / "pyphen_syllables_frequencies.json").write_text(json.dumps({"py": 100}))

        info = get_corpus_info(corpus_dir)

        assert "Pyphen" in info
        assert "20260110_143022_pyphen" in info

    def test_corpus_info_format(self, tmp_path):
        """Test corpus info format matches expected pattern."""
        corpus_dir = tmp_path / "test_corpus"
        corpus_dir.mkdir()

        (corpus_dir / "nltk_syllables_unique.txt").write_text("test\n")
        (corpus_dir / "nltk_syllables_frequencies.json").write_text(json.dumps({"test": 1}))

        info = get_corpus_info(corpus_dir)

        # Format: "NLTK (dir_name)"
        assert info == "NLTK (test_corpus)"

    def test_corpus_info_invalid_directory(self, tmp_path):
        """Test corpus info for invalid directory returns error message."""
        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()

        info = get_corpus_info(invalid_dir)

        assert "Invalid" in info
        assert "No corpus files found" in info
