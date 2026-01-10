"""
Comprehensive test suite for nltk_syllable_normaliser package.

Tests NLTK-specific components and integration with shared normalization pipeline:
1. Fragment cleaning (NLTK-specific preprocessing)
2. NLTK run directory detection
3. In-place processing workflow
4. Output file generation with nltk_ prefix
5. Integration with pyphen normaliser components
"""

import json
from pathlib import Path

import pytest

from build_tools.nltk_syllable_normaliser import (
    FragmentCleaner,
    NormalizationConfig,
    run_full_pipeline,
)
from build_tools.nltk_syllable_normaliser.cli import detect_nltk_run_directories

# ============================================================================
# Test Fragment Cleaner
# ============================================================================


class TestFragmentCleaner:
    """Test FragmentCleaner class for merging single-letter fragments."""

    def test_is_single_letter(self):
        """Test single letter detection."""
        assert FragmentCleaner.is_single_letter("a") is True
        assert FragmentCleaner.is_single_letter("Z") is True
        assert FragmentCleaner.is_single_letter("ab") is False
        assert FragmentCleaner.is_single_letter("1") is False
        assert FragmentCleaner.is_single_letter("") is False

    def test_is_single_vowel(self):
        """Test single vowel detection."""
        assert FragmentCleaner.is_single_vowel("a") is True
        assert FragmentCleaner.is_single_vowel("e") is True
        assert FragmentCleaner.is_single_vowel("i") is True
        assert FragmentCleaner.is_single_vowel("o") is True
        assert FragmentCleaner.is_single_vowel("u") is True
        assert FragmentCleaner.is_single_vowel("y") is True
        assert FragmentCleaner.is_single_vowel("A") is True  # Case insensitive
        assert FragmentCleaner.is_single_vowel("b") is False
        assert FragmentCleaner.is_single_vowel("ae") is False

    def test_clean_fragments_single_vowel_merging(self):
        """Test that single vowels merge with next fragment."""
        cleaner = FragmentCleaner()

        # Single vowel at start
        result = cleaner.clean_fragments(["i", "down"])
        assert result == ["idown"]

        # Single vowel in middle
        result = cleaner.clean_fragments(["the", "a", "bbit"])
        assert result == ["the", "abbit"]

        # Multiple single vowels
        result = cleaner.clean_fragments(["i", "a", "m"])
        assert result == ["ia", "m"]  # i+a merges, m has no next

    def test_clean_fragments_single_consonant_merging(self):
        """Test that single consonants merge with next fragment."""
        cleaner = FragmentCleaner()

        # Single consonant
        result = cleaner.clean_fragments(["r", "abbit"])
        assert result == ["rabbit"]

        # Multiple single consonants
        result = cleaner.clean_fragments(["h", "e", "llo"])
        assert result == ["he", "llo"]  # h+e merges (e is vowel), then separate

    def test_clean_fragments_mixed_cases(self):
        """Test realistic NLTK fragment patterns."""
        cleaner = FragmentCleaner()

        # Real NLTK example: "chapter i down the rabbit hole"
        fragments = ["cha", "pter", "i", "down", "the", "r", "a", "bbit", "ho", "le"]
        result = cleaner.clean_fragments(fragments)
        # i+down → idown, r+a → ra
        assert "idown" in result
        assert "ra" in result

        # Another example
        fragments = ["hel", "lo", "world"]
        result = cleaner.clean_fragments(fragments)
        assert result == ["hel", "lo", "world"]  # No single letters

    def test_clean_fragments_empty_input(self):
        """Test that empty input returns empty output."""
        cleaner = FragmentCleaner()
        assert cleaner.clean_fragments([]) == []

    def test_clean_fragments_single_element(self):
        """Test single-element list handling."""
        cleaner = FragmentCleaner()

        # Single multi-char fragment
        assert cleaner.clean_fragments(["hello"]) == ["hello"]

        # Single single-letter fragment (no next to merge with)
        assert cleaner.clean_fragments(["a"]) == ["a"]

    def test_clean_fragments_preserves_multi_character_fragments(self):
        """Test that multi-character fragments are not modified."""
        cleaner = FragmentCleaner()
        fragments = ["hello", "world", "testing"]
        result = cleaner.clean_fragments(fragments)
        assert result == fragments

    def test_clean_fragments_last_element_never_merges(self):
        """Test that the last fragment never merges (no next available)."""
        cleaner = FragmentCleaner()

        # Last element is single letter
        result = cleaner.clean_fragments(["hello", "a"])
        assert result == ["hello", "a"]  # 'a' can't merge (no next)

    def test_clean_fragments_from_file(self, tmp_path: Path):
        """Test file-based fragment cleaning."""
        cleaner = FragmentCleaner()

        # Create input file
        input_file = tmp_path / "fragments.txt"
        input_file.write_text("i\ndown\nthe\nr\na\nbbit\n", encoding="utf-8")

        output_file = tmp_path / "cleaned.txt"

        # Clean fragments
        original_count, cleaned_count = cleaner.clean_fragments_from_file(
            str(input_file), str(output_file)
        )

        assert original_count == 6
        assert cleaned_count == 4  # idown, the, ra, bbit

        # Verify output content
        cleaned = output_file.read_text(encoding="utf-8").strip().split("\n")
        assert "idown" in cleaned
        assert "the" in cleaned
        assert "ra" in cleaned
        assert "bbit" in cleaned

    def test_clean_fragments_from_file_nonexistent(self, tmp_path: Path):
        """Test that nonexistent file raises FileNotFoundError."""
        cleaner = FragmentCleaner()
        input_file = tmp_path / "nonexistent.txt"
        output_file = tmp_path / "output.txt"

        with pytest.raises(FileNotFoundError):
            cleaner.clean_fragments_from_file(str(input_file), str(output_file))


# ============================================================================
# Test NLTK Run Directory Detection
# ============================================================================


class TestNltkRunDirectoryDetection:
    """Test detection of NLTK run directories."""

    def test_detect_nltk_run_directories_basic(self, tmp_path: Path):
        """Test basic NLTK run directory detection."""
        # Create NLTK run directories
        nltk_dir1 = tmp_path / "20260110_095213_nltk"
        nltk_dir1.mkdir()
        (nltk_dir1 / "syllables").mkdir()

        nltk_dir2 = tmp_path / "20260110_143022_nltk"
        nltk_dir2.mkdir()
        (nltk_dir2 / "syllables").mkdir()

        # Create non-NLTK directory
        other_dir = tmp_path / "20260110_095213_pyphen"
        other_dir.mkdir()
        (other_dir / "syllables").mkdir()

        # Detect
        result = detect_nltk_run_directories(tmp_path)

        assert len(result) == 2
        assert all(d.name.endswith("_nltk") for d in result)
        assert nltk_dir1 in result
        assert nltk_dir2 in result
        assert other_dir not in result

    def test_detect_nltk_run_directories_requires_syllables_subdir(self, tmp_path: Path):
        """Test that directories without syllables/ are ignored."""
        # NLTK directory without syllables/ subdirectory
        nltk_dir = tmp_path / "20260110_095213_nltk"
        nltk_dir.mkdir()

        result = detect_nltk_run_directories(tmp_path)

        assert len(result) == 0  # Should be ignored

    def test_detect_nltk_run_directories_sorted(self, tmp_path: Path):
        """Test that results are sorted chronologically."""
        # Create in reverse order
        nltk_dir3 = tmp_path / "20260110_153022_nltk"
        nltk_dir3.mkdir()
        (nltk_dir3 / "syllables").mkdir()

        nltk_dir1 = tmp_path / "20260110_095213_nltk"
        nltk_dir1.mkdir()
        (nltk_dir1 / "syllables").mkdir()

        nltk_dir2 = tmp_path / "20260110_143022_nltk"
        nltk_dir2.mkdir()
        (nltk_dir2 / "syllables").mkdir()

        result = detect_nltk_run_directories(tmp_path)

        # Should be sorted
        names = [d.name for d in result]
        assert names == sorted(names)

    def test_detect_nltk_run_directories_empty_source(self, tmp_path: Path):
        """Test that empty directory returns empty list."""
        result = detect_nltk_run_directories(tmp_path)
        assert result == []

    def test_detect_nltk_run_directories_nonexistent(self, tmp_path: Path):
        """Test that nonexistent directory raises FileNotFoundError."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            detect_nltk_run_directories(nonexistent)

    def test_detect_nltk_run_directories_not_a_directory(self, tmp_path: Path):
        """Test that file path raises ValueError."""
        file_path = tmp_path / "file.txt"
        file_path.touch()

        with pytest.raises(ValueError, match="not a directory"):
            detect_nltk_run_directories(file_path)


# ============================================================================
# Test Full Pipeline Integration
# ============================================================================


class TestFullPipeline:
    """Integration tests for complete NLTK normalization pipeline."""

    def test_full_pipeline_in_place_processing(self, tmp_path: Path):
        """Test in-place processing creates output files in run directory."""
        # Create mock NLTK run directory
        run_dir = tmp_path / "20260110_095213_nltk"
        syllables_dir = run_dir / "syllables"
        syllables_dir.mkdir(parents=True)

        # Create mock syllable file
        test_file = syllables_dir / "en_US_test.txt"
        test_file.write_text("i\ndown\nthe\nr\na\nbbit\nhel\nlo\n", encoding="utf-8")

        # Run pipeline
        config = NormalizationConfig(min_length=2, max_length=20)
        _ = run_full_pipeline(run_directory=run_dir, config=config, verbose=False)

        # Verify all 5 output files created in run directory (not subdirectory)
        assert (run_dir / "nltk_syllables_raw.txt").exists()
        assert (run_dir / "nltk_syllables_canonicalised.txt").exists()
        assert (run_dir / "nltk_syllables_frequencies.json").exists()
        assert (run_dir / "nltk_syllables_unique.txt").exists()
        assert (run_dir / "nltk_normalization_meta.txt").exists()

        # Verify file prefixes
        output_files = list(run_dir.glob("nltk_*"))
        assert len(output_files) == 5
        assert all(f.name.startswith("nltk_") for f in output_files)

    def test_full_pipeline_fragment_cleaning_applied(self, tmp_path: Path):
        """Test that fragment cleaning reduces syllable count."""
        # Create mock NLTK run directory
        run_dir = tmp_path / "20260110_095213_nltk"
        syllables_dir = run_dir / "syllables"
        syllables_dir.mkdir(parents=True)

        # Create file with many single letters
        test_file = syllables_dir / "test.txt"
        fragments = ["i", "down", "the", "r", "a", "bbit", "h", "o", "le"]
        test_file.write_text("\n".join(fragments) + "\n", encoding="utf-8")

        # Run pipeline
        config = NormalizationConfig(min_length=2, max_length=20)
        result = run_full_pipeline(run_directory=run_dir, config=config, verbose=False)

        # Fragment cleaning should reduce count
        assert result.stats.raw_count == 9
        # After cleaning: i+down=idown, the, r+a=ra, bbit, h+o=ho, le = 6 syllables
        # All pass length filter (min=2): idown(5), the(3), ra(2), bbit(4), ho(2), le(2)
        assert result.stats.after_canonicalization == 6

        # Verify frequencies reflect cleaned syllables
        assert "idown" in result.frequencies
        assert "ra" in result.frequencies
        assert "bbit" in result.frequencies

    def test_full_pipeline_skip_fragment_cleaning(self, tmp_path: Path):
        """Test skip_fragment_cleaning option."""
        # Create mock NLTK run directory
        run_dir = tmp_path / "20260110_095213_nltk"
        syllables_dir = run_dir / "syllables"
        syllables_dir.mkdir(parents=True)

        test_file = syllables_dir / "test.txt"
        test_file.write_text("hello\nworld\ntest\n", encoding="utf-8")

        # Run pipeline with fragment cleaning skipped
        config = NormalizationConfig(min_length=2, max_length=20)
        result = run_full_pipeline(
            run_directory=run_dir, config=config, verbose=False, skip_fragment_cleaning=True
        )

        # Should process without cleaning
        assert result.stats.raw_count == 3
        assert result.stats.after_canonicalization == 3

    def test_full_pipeline_output_content_verification(self, tmp_path: Path):
        """Test that output files contain correct content."""
        # Create mock NLTK run directory
        run_dir = tmp_path / "20260110_095213_nltk"
        syllables_dir = run_dir / "syllables"
        syllables_dir.mkdir(parents=True)

        test_file = syllables_dir / "test.txt"
        test_file.write_text("i\ndown\nthe\nr\na\nbbit\n", encoding="utf-8")

        # Run pipeline
        config = NormalizationConfig(min_length=2, max_length=20)
        _ = run_full_pipeline(run_directory=run_dir, config=config, verbose=False)

        # Verify raw file (before cleaning)
        raw_content = (
            (run_dir / "nltk_syllables_raw.txt").read_text(encoding="utf-8").strip().split("\n")
        )
        assert len(raw_content) == 6
        assert raw_content == ["i", "down", "the", "r", "a", "bbit"]

        # Verify canonical file (after cleaning)
        canonical_content = (
            (run_dir / "nltk_syllables_canonicalised.txt")
            .read_text(encoding="utf-8")
            .strip()
            .split("\n")
        )
        assert "idown" in canonical_content
        assert "the" in canonical_content
        assert "ra" in canonical_content
        assert "bbit" in canonical_content

        # Verify frequencies
        frequencies = json.loads(
            (run_dir / "nltk_syllables_frequencies.json").read_text(encoding="utf-8")
        )
        assert frequencies["idown"] == 1
        assert frequencies["the"] == 1
        assert frequencies["ra"] == 1
        assert frequencies["bbit"] == 1

        # Verify unique
        unique_content = (
            (run_dir / "nltk_syllables_unique.txt").read_text(encoding="utf-8").strip().split("\n")
        )
        assert sorted(unique_content) == ["bbit", "idown", "ra", "the"]

    def test_full_pipeline_multiple_input_files(self, tmp_path: Path):
        """Test processing multiple syllable files."""
        # Create mock NLTK run directory
        run_dir = tmp_path / "20260110_095213_nltk"
        syllables_dir = run_dir / "syllables"
        syllables_dir.mkdir(parents=True)

        # Create multiple files
        file1 = syllables_dir / "file1.txt"
        file1.write_text("hel\nlo\n", encoding="utf-8")

        file2 = syllables_dir / "file2.txt"
        file2.write_text("world\ntest\n", encoding="utf-8")

        # Run pipeline
        config = NormalizationConfig(min_length=2, max_length=20)
        result = run_full_pipeline(run_directory=run_dir, config=config, verbose=False)

        # Should aggregate all files
        assert result.stats.raw_count == 4
        assert len(result.input_files) == 2

    def test_full_pipeline_missing_syllables_directory(self, tmp_path: Path):
        """Test that missing syllables/ directory raises error."""
        run_dir = tmp_path / "20260110_095213_nltk"
        run_dir.mkdir()
        # No syllables/ subdirectory

        config = NormalizationConfig()

        with pytest.raises(FileNotFoundError, match="Syllables directory does not exist"):
            run_full_pipeline(run_directory=run_dir, config=config, verbose=False)

    def test_full_pipeline_nonexistent_run_directory(self, tmp_path: Path):
        """Test that nonexistent run directory raises error."""
        run_dir = tmp_path / "nonexistent"
        config = NormalizationConfig()

        with pytest.raises(FileNotFoundError, match="Run directory does not exist"):
            run_full_pipeline(run_directory=run_dir, config=config, verbose=False)

    def test_full_pipeline_determinism(self, tmp_path: Path):
        """Test that pipeline produces deterministic output."""
        # Create mock NLTK run directory
        run_dir = tmp_path / "20260110_095213_nltk"
        syllables_dir = run_dir / "syllables"
        syllables_dir.mkdir(parents=True)

        test_file = syllables_dir / "test.txt"
        test_file.write_text("i\ndown\nthe\nr\na\nbbit\n", encoding="utf-8")

        config = NormalizationConfig()

        # Run pipeline twice
        result1 = run_full_pipeline(run_directory=run_dir, config=config, verbose=False)

        # Clear outputs
        for f in run_dir.glob("nltk_*"):
            f.unlink()

        result2 = run_full_pipeline(run_directory=run_dir, config=config, verbose=False)

        # Verify identical results
        assert result1.stats.raw_count == result2.stats.raw_count
        assert result1.stats.after_canonicalization == result2.stats.after_canonicalization
        assert result1.stats.unique_canonical == result2.stats.unique_canonical
        assert result1.frequencies == result2.frequencies
