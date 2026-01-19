"""
Tests for pipeline_tui validators module.

Tests directory validation functions for source, output, and corpus directories.
"""

from pathlib import Path
from unittest.mock import patch

from build_tools.pipeline_tui.services.validators import (
    validate_corpus_directory,
    validate_output_directory,
    validate_source_directory,
)


class TestValidateSourceDirectory:
    """Tests for validate_source_directory function."""

    def test_not_a_directory(self, tmp_path: Path) -> None:
        """Test validation fails for non-directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        is_valid, type_label, message = validate_source_directory(file_path)

        assert is_valid is False
        assert type_label == ""
        assert message == "Not a directory"

    def test_nonexistent_path(self, tmp_path: Path) -> None:
        """Test validation fails for nonexistent path."""
        nonexistent = tmp_path / "nonexistent"

        is_valid, type_label, message = validate_source_directory(nonexistent)

        assert is_valid is False
        assert type_label == ""
        assert message == "Not a directory"

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test validation fails for directory with no .txt files."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        is_valid, type_label, message = validate_source_directory(empty_dir)

        assert is_valid is False
        assert type_label == ""
        assert message == "No .txt files found"

    def test_directory_with_other_files_only(self, tmp_path: Path) -> None:
        """Test validation fails when only non-txt files present."""
        dir_path = tmp_path / "other_files"
        dir_path.mkdir()
        (dir_path / "file.md").write_text("markdown")
        (dir_path / "file.py").write_text("python")

        is_valid, type_label, message = validate_source_directory(dir_path)

        assert is_valid is False
        assert type_label == ""
        assert message == "No .txt files found"

    def test_directory_with_direct_txt_files(self, tmp_path: Path) -> None:
        """Test validation passes with direct .txt files."""
        dir_path = tmp_path / "with_txt"
        dir_path.mkdir()
        (dir_path / "file1.txt").write_text("text1")
        (dir_path / "file2.txt").write_text("text2")

        is_valid, type_label, message = validate_source_directory(dir_path)

        assert is_valid is True
        assert type_label == "source"
        assert "Found 2 text file(s)" in message

    def test_directory_with_nested_txt_files(self, tmp_path: Path) -> None:
        """Test validation passes with nested .txt files."""
        dir_path = tmp_path / "nested"
        dir_path.mkdir()
        subdir = dir_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested text")

        is_valid, type_label, message = validate_source_directory(dir_path)

        assert is_valid is True
        assert type_label == "source"
        assert "Found 1 text file(s)" in message

    def test_directory_with_mixed_txt_files(self, tmp_path: Path) -> None:
        """Test message distinguishes direct vs nested files."""
        dir_path = tmp_path / "mixed"
        dir_path.mkdir()
        (dir_path / "direct.txt").write_text("direct")
        subdir = dir_path / "subdir"
        subdir.mkdir()
        (subdir / "nested1.txt").write_text("nested1")
        (subdir / "nested2.txt").write_text("nested2")

        is_valid, type_label, message = validate_source_directory(dir_path)

        assert is_valid is True
        assert type_label == "source"
        assert "Found 3 text file(s)" in message
        assert "1 direct" in message

    def test_only_direct_files_message(self, tmp_path: Path) -> None:
        """Test message when all files are direct (no 'direct' suffix)."""
        dir_path = tmp_path / "only_direct"
        dir_path.mkdir()
        (dir_path / "file1.txt").write_text("text1")
        (dir_path / "file2.txt").write_text("text2")
        (dir_path / "file3.txt").write_text("text3")

        is_valid, type_label, message = validate_source_directory(dir_path)

        assert is_valid is True
        assert "Found 3 text file(s)" in message
        # Should NOT have "(X direct)" when all files are direct
        assert "direct" not in message


class TestValidateOutputDirectory:
    """Tests for validate_output_directory function."""

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test validation fails for nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"

        is_valid, type_label, message = validate_output_directory(nonexistent)

        assert is_valid is False
        assert type_label == ""
        assert message == "Directory does not exist"

    def test_not_a_directory(self, tmp_path: Path) -> None:
        """Test validation fails for file path."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        is_valid, type_label, message = validate_output_directory(file_path)

        assert is_valid is False
        assert type_label == ""
        assert message == "Not a directory"

    def test_empty_valid_directory(self, tmp_path: Path) -> None:
        """Test validation passes for empty directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        is_valid, type_label, message = validate_output_directory(output_dir)

        assert is_valid is True
        assert type_label == "output"
        assert message == "Valid output directory"

    def test_directory_with_existing_pyphen_runs(self, tmp_path: Path) -> None:
        """Test message includes count of pyphen runs."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "20260101_120000_pyphen").mkdir()
        (output_dir / "20260102_120000_pyphen").mkdir()

        is_valid, type_label, message = validate_output_directory(output_dir)

        assert is_valid is True
        assert type_label == "output"
        assert "2 existing runs" in message

    def test_directory_with_existing_nltk_runs(self, tmp_path: Path) -> None:
        """Test message includes count of nltk runs."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "20260101_120000_nltk").mkdir()

        is_valid, type_label, message = validate_output_directory(output_dir)

        assert is_valid is True
        assert type_label == "output"
        assert "1 existing runs" in message

    def test_directory_with_mixed_runs(self, tmp_path: Path) -> None:
        """Test message counts both pyphen and nltk runs."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "20260101_120000_pyphen").mkdir()
        (output_dir / "20260102_120000_nltk").mkdir()
        (output_dir / "20260103_120000_pyphen").mkdir()

        is_valid, type_label, message = validate_output_directory(output_dir)

        assert is_valid is True
        assert type_label == "output"
        assert "3 existing runs" in message

    def test_directory_ignores_non_run_directories(self, tmp_path: Path) -> None:
        """Test that non-run directories are not counted."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "random_dir").mkdir()
        (output_dir / "another_dir").mkdir()

        is_valid, type_label, message = validate_output_directory(output_dir)

        assert is_valid is True
        assert message == "Valid output directory"

    def test_directory_ignores_files(self, tmp_path: Path) -> None:
        """Test that files are not counted as runs."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "20260101_120000_pyphen.txt").write_text("not a dir")

        is_valid, type_label, message = validate_output_directory(output_dir)

        assert is_valid is True
        assert message == "Valid output directory"

    def test_permission_denied(self, tmp_path: Path) -> None:
        """Test validation fails when permission denied."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch("pathlib.Path.iterdir", side_effect=PermissionError("Access denied")):
            is_valid, type_label, message = validate_output_directory(output_dir)

        assert is_valid is False
        assert type_label == ""
        assert message == "Permission denied"


class TestValidateCorpusDirectory:
    """Tests for validate_corpus_directory function."""

    def test_not_a_directory(self, tmp_path: Path) -> None:
        """Test validation fails for non-directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        is_valid, type_label, message = validate_corpus_directory(file_path)

        assert is_valid is False
        assert type_label == ""
        assert message == "Not a directory"

    def test_nonexistent_path(self, tmp_path: Path) -> None:
        """Test validation fails for nonexistent path."""
        nonexistent = tmp_path / "nonexistent"

        is_valid, type_label, message = validate_corpus_directory(nonexistent)

        assert is_valid is False
        assert type_label == ""
        assert message == "Not a directory"

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test validation fails for empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        is_valid, type_label, message = validate_corpus_directory(empty_dir)

        assert is_valid is False
        assert type_label == ""
        assert "No corpus files found" in message

    def test_missing_unique_file(self, tmp_path: Path) -> None:
        """Test validation fails when unique file missing."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        (corpus_dir / "nltk_syllables_frequencies.json").write_text("{}")

        is_valid, type_label, message = validate_corpus_directory(corpus_dir)

        assert is_valid is False
        assert "No corpus files found" in message

    def test_missing_frequencies_file(self, tmp_path: Path) -> None:
        """Test validation fails when frequencies file missing."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        (corpus_dir / "nltk_syllables_unique.txt").write_text("syllable")

        is_valid, type_label, message = validate_corpus_directory(corpus_dir)

        assert is_valid is False
        assert "No corpus files found" in message

    def test_valid_nltk_corpus(self, tmp_path: Path) -> None:
        """Test validation passes for valid NLTK corpus."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        (corpus_dir / "nltk_syllables_unique.txt").write_text("ab\ncd\nef\n")
        (corpus_dir / "nltk_syllables_frequencies.json").write_text("{}")

        is_valid, type_label, message = validate_corpus_directory(corpus_dir)

        assert is_valid is True
        assert type_label == "nltk"
        assert "NLTK corpus" in message
        assert "3 syllables" in message

    def test_valid_pyphen_corpus(self, tmp_path: Path) -> None:
        """Test validation passes for valid pyphen corpus."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        (corpus_dir / "pyphen_syllables_unique.txt").write_text("ab\ncd\n")
        (corpus_dir / "pyphen_syllables_frequencies.json").write_text("{}")

        is_valid, type_label, message = validate_corpus_directory(corpus_dir)

        assert is_valid is True
        assert type_label == "pyphen"
        assert "Pyphen corpus" in message
        assert "2 syllables" in message

    def test_nltk_takes_precedence_over_pyphen(self, tmp_path: Path) -> None:
        """Test NLTK is detected first when both present."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        # Both NLTK and pyphen files
        (corpus_dir / "nltk_syllables_unique.txt").write_text("ab\n")
        (corpus_dir / "nltk_syllables_frequencies.json").write_text("{}")
        (corpus_dir / "pyphen_syllables_unique.txt").write_text("cd\n")
        (corpus_dir / "pyphen_syllables_frequencies.json").write_text("{}")

        is_valid, type_label, message = validate_corpus_directory(corpus_dir)

        assert is_valid is True
        assert type_label == "nltk"

    def test_nltk_corpus_count_error_fallback(self, tmp_path: Path) -> None:
        """Test fallback message when counting fails for NLTK corpus."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        (corpus_dir / "nltk_syllables_unique.txt").write_text("ab\ncd\n")
        (corpus_dir / "nltk_syllables_frequencies.json").write_text("{}")

        with patch("pathlib.Path.open", side_effect=IOError("Read error")):
            is_valid, type_label, message = validate_corpus_directory(corpus_dir)

        assert is_valid is True
        assert type_label == "nltk"
        assert message == "NLTK corpus"

    def test_pyphen_corpus_count_error_fallback(self, tmp_path: Path) -> None:
        """Test fallback message when counting fails for pyphen corpus."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        unique_file = corpus_dir / "pyphen_syllables_unique.txt"
        unique_file.write_text("ab\ncd\n")
        (corpus_dir / "pyphen_syllables_frequencies.json").write_text("{}")

        # Mock open() to fail only for pyphen unique file reads
        original_open = Path.open

        def mock_open(self, *args, **kwargs):
            if "pyphen_syllables_unique" in str(self):
                raise IOError("Read error")
            return original_open(self, *args, **kwargs)

        with patch.object(Path, "open", mock_open):
            is_valid, type_label, message = validate_corpus_directory(corpus_dir)

        assert is_valid is True
        assert type_label == "pyphen"
        assert message == "Pyphen corpus"

    def test_large_corpus_syllable_count(self, tmp_path: Path) -> None:
        """Test syllable count formatting for large corpus."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        # Create file with 1500 syllables
        syllables = "\n".join([f"syl{i}" for i in range(1500)])
        (corpus_dir / "nltk_syllables_unique.txt").write_text(syllables)
        (corpus_dir / "nltk_syllables_frequencies.json").write_text("{}")

        is_valid, type_label, message = validate_corpus_directory(corpus_dir)

        assert is_valid is True
        assert "1,500 syllables" in message
