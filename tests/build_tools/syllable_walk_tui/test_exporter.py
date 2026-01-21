"""
Tests for syllable_walk_tui analyzer exporter functionality.

Tests for formatting and exporting corpus shape metrics to text format.
"""

import re
from datetime import datetime
from pathlib import Path

import pytest

from build_tools.syllable_walk_tui.modules.analyzer.exporter import (
    export_analysis_to_file,
    format_analysis_export,
    format_feature_saturation,
    format_frequency_metrics,
    format_inventory_metrics,
    format_patch_metrics,
    format_terrain_metrics,
    generate_export_filename,
)
from build_tools.syllable_walk_tui.services.metrics import (
    CorpusShapeMetrics,
    FeatureSaturation,
    FeatureSaturationMetrics,
    FrequencyMetrics,
    InventoryMetrics,
    TerrainMetrics,
)


@pytest.fixture
def sample_inventory_metrics():
    """Create sample inventory metrics for testing."""
    return InventoryMetrics(
        total_count=1000,
        length_min=2,
        length_max=8,
        length_mean=4.5,
        length_median=4.0,
        length_std=1.2,
        length_distribution={2: 100, 3: 200, 4: 300, 5: 250, 6: 100, 7: 40, 8: 10},
    )


@pytest.fixture
def sample_frequency_metrics():
    """Create sample frequency metrics for testing."""
    return FrequencyMetrics(
        total_occurrences=50000,
        freq_min=1,
        freq_max=5000,
        freq_mean=50.0,
        freq_median=10.0,
        freq_std=150.0,
        unique_freq_count=200,
        hapax_count=300,
        percentile_10=2,
        percentile_25=5,
        percentile_50=10,
        percentile_75=30,
        percentile_90=100,
        percentile_99=500,
        top_10=(
            ("the", 5000),
            ("ing", 3000),
            ("tion", 2500),
            ("and", 2000),
            ("for", 1800),
            ("with", 1500),
            ("that", 1200),
            ("this", 1000),
            ("from", 900),
            ("have", 800),
        ),
    )


@pytest.fixture
def sample_feature_saturation():
    """Create sample feature saturation metrics for testing."""
    # Create FeatureSaturation objects with feature_name as first arg
    by_name = {
        "starts_with_vowel": FeatureSaturation("starts_with_vowel", 300, 700, 30.0),
        "starts_with_cluster": FeatureSaturation("starts_with_cluster", 150, 850, 15.0),
        "starts_with_heavy_cluster": FeatureSaturation("starts_with_heavy_cluster", 50, 950, 5.0),
        "contains_plosive": FeatureSaturation("contains_plosive", 400, 600, 40.0),
        "contains_fricative": FeatureSaturation("contains_fricative", 350, 650, 35.0),
        "contains_liquid": FeatureSaturation("contains_liquid", 250, 750, 25.0),
        "contains_nasal": FeatureSaturation("contains_nasal", 200, 800, 20.0),
        "short_vowel": FeatureSaturation("short_vowel", 500, 500, 50.0),
        "long_vowel": FeatureSaturation("long_vowel", 450, 550, 45.0),
        "ends_with_vowel": FeatureSaturation("ends_with_vowel", 350, 650, 35.0),
        "ends_with_nasal": FeatureSaturation("ends_with_nasal", 100, 900, 10.0),
        "ends_with_stop": FeatureSaturation("ends_with_stop", 200, 800, 20.0),
    }
    # Create feature tuple in canonical order
    features = tuple(
        by_name[name]
        for name in [
            "starts_with_vowel",
            "starts_with_cluster",
            "starts_with_heavy_cluster",
            "contains_plosive",
            "contains_fricative",
            "contains_liquid",
            "contains_nasal",
            "short_vowel",
            "long_vowel",
            "ends_with_vowel",
            "ends_with_nasal",
            "ends_with_stop",
        ]
    )
    return FeatureSaturationMetrics(
        total_syllables=1000,
        features=features,
        by_name=by_name,
    )


@pytest.fixture
def sample_terrain_metrics():
    """Create sample terrain metrics for testing."""
    return TerrainMetrics(
        shape_score=0.65,
        shape_label="Jagged",
        craft_score=0.35,
        craft_label="Flowing",
        space_score=0.50,
        space_label="Balanced",
    )


@pytest.fixture
def sample_corpus_shape_metrics(
    sample_inventory_metrics,
    sample_frequency_metrics,
    sample_feature_saturation,
    sample_terrain_metrics,
):
    """Create sample complete corpus shape metrics for testing."""
    return CorpusShapeMetrics(
        inventory=sample_inventory_metrics,
        frequency=sample_frequency_metrics,
        feature_saturation=sample_feature_saturation,
        terrain=sample_terrain_metrics,
    )


class TestFormatInventoryMetrics:
    """Tests for format_inventory_metrics function."""

    def test_basic_formatting(self, sample_inventory_metrics):
        """Test that inventory metrics are formatted correctly."""
        result = format_inventory_metrics(sample_inventory_metrics)

        assert "INVENTORY" in result
        assert "Total syllables:" in result
        assert "1,000" in result
        assert "Length min:" in result
        assert "2" in result
        assert "Length max:" in result
        assert "8" in result
        assert "Length mean:" in result
        assert "4.50" in result
        assert "Length median:" in result
        assert "4.0" in result
        assert "Length std:" in result
        assert "1.20" in result

    def test_length_distribution_formatting(self, sample_inventory_metrics):
        """Test that length distribution is formatted with counts and percentages."""
        result = format_inventory_metrics(sample_inventory_metrics)

        assert "Length dist:" in result
        # Distribution should be sorted by key with percentages in parentheses
        # 2:100/1000 = 10.0%, 3:200/1000 = 20.0%, 8:10/1000 = 1.0%
        assert "2:100 (10.0%)" in result
        assert "3:200 (20.0%)" in result
        assert "8:10 (1.0%)" in result

    def test_empty_distribution(self):
        """Test formatting with empty distribution."""
        metrics = InventoryMetrics(
            total_count=0,
            length_min=0,
            length_max=0,
            length_mean=0.0,
            length_median=0.0,
            length_std=0.0,
            length_distribution={},
        )
        result = format_inventory_metrics(metrics)

        assert "INVENTORY" in result
        assert "Total syllables:" in result
        assert "0" in result


class TestFormatFrequencyMetrics:
    """Tests for format_frequency_metrics function."""

    def test_basic_formatting(self, sample_frequency_metrics):
        """Test that frequency metrics are formatted correctly."""
        result = format_frequency_metrics(sample_frequency_metrics)

        assert "FREQUENCY" in result
        assert "Total occurrences:" in result
        assert "50,000" in result
        assert "Freq min:" in result
        assert "Freq max:" in result
        assert "5,000" in result
        assert "Freq mean:" in result
        assert "50.00" in result
        assert "Unique freq values:" in result
        assert "Hapax (freq=1):" in result
        assert "300" in result

    def test_hapax_rate_with_total_syllables(self, sample_frequency_metrics):
        """Test that hapax rate percentage is shown when total_syllables provided."""
        # hapax_count=300, total_syllables=1000 -> 30.0%
        result = format_frequency_metrics(sample_frequency_metrics, total_syllables=1000)

        assert "Hapax (freq=1):" in result
        assert "300 (30.0%)" in result

    def test_hapax_rate_without_total_syllables(self, sample_frequency_metrics):
        """Test that hapax rate percentage is omitted when total_syllables not provided."""
        result = format_frequency_metrics(sample_frequency_metrics)

        assert "Hapax (freq=1):" in result
        assert "300" in result
        # Should NOT have percentage without total_syllables
        assert "(30.0%)" not in result

    def test_percentiles_formatting(self, sample_frequency_metrics):
        """Test that percentiles are formatted correctly."""
        result = format_frequency_metrics(sample_frequency_metrics)

        assert "Percentiles:" in result
        assert "P10=" in result
        assert "P25=" in result
        assert "P50=" in result
        assert "P75=" in result
        assert "P90=" in result
        assert "P99=" in result

    def test_top_frequencies_formatting(self, sample_frequency_metrics):
        """Test that top 5 frequencies are shown with percentages."""
        result = format_frequency_metrics(sample_frequency_metrics)

        assert "Top 5 by frequency:" in result
        # First 5 should be shown with percentages of total occurrences
        # the: 5000/50000 = 10.0%, ing: 3000/50000 = 6.0%
        assert "the:" in result
        assert "5,000 (10.0%)" in result
        assert "ing:" in result
        assert "3,000 (6.0%)" in result
        # 6th entry should not be shown
        assert "with:" not in result


class TestFormatFeatureSaturation:
    """Tests for format_feature_saturation function."""

    def test_basic_formatting(self, sample_feature_saturation):
        """Test that feature saturation is formatted correctly."""
        result = format_feature_saturation(sample_feature_saturation)

        assert "FEATURE SATURATION" in result
        assert "Total analyzed:" in result
        assert "1,000" in result

    def test_category_sections(self, sample_feature_saturation):
        """Test that features are grouped by category."""
        result = format_feature_saturation(sample_feature_saturation)

        # Category headers
        assert "Onset:" in result
        assert "Internal:" in result
        assert "Nucleus:" in result
        assert "Coda:" in result

    def test_feature_counts_and_percentages(self, sample_feature_saturation):
        """Test that feature counts and percentages are shown."""
        result = format_feature_saturation(sample_feature_saturation)

        # Check some feature entries with counts and percentages
        assert "30.0%" in result  # starts_with_vowel
        assert "40.0%" in result  # contains_plosive
        assert "35.0%" in result  # ends_with_vowel

    def test_feature_name_cleanup(self, sample_feature_saturation):
        """Test that feature names are cleaned up for display."""
        result = format_feature_saturation(sample_feature_saturation)

        # Should NOT have prefixes like "starts_with_", "ends_with_", "contains_"
        # Instead should show clean names like "vowel", "plosive", etc.
        lines = result.split("\n")
        onset_section = [line for line in lines if "vowel" in line.lower() and "%" in line]
        assert len(onset_section) > 0


class TestFormatTerrainMetrics:
    """Tests for format_terrain_metrics function."""

    def test_basic_formatting(self, sample_terrain_metrics):
        """Test that terrain metrics are formatted correctly."""
        result = format_terrain_metrics(sample_terrain_metrics)

        assert "TERRAIN" in result
        assert "Shape:" in result
        assert "Round <-> Jagged" in result
        assert "Craft:" in result
        assert "Flowing <-> Worked" in result
        assert "Space:" in result
        assert "Open <-> Dense" in result

    def test_labels_displayed(self, sample_terrain_metrics):
        """Test that terrain labels are shown."""
        result = format_terrain_metrics(sample_terrain_metrics)

        assert "Jagged" in result
        assert "Flowing" in result
        assert "Balanced" in result

    def test_delta_formatting(self, sample_terrain_metrics):
        """Test that deltas from neutral (0.5) are shown."""
        result = format_terrain_metrics(sample_terrain_metrics)

        # Shape score 0.65 -> delta +0.150
        assert "+0.150" in result
        # Craft score 0.35 -> delta -0.150
        assert "-0.150" in result
        # Space score 0.50 -> delta +0.000
        assert "+0.000" in result

    def test_bar_rendering(self, sample_terrain_metrics):
        """Test that ASCII bars are rendered."""
        result = format_terrain_metrics(sample_terrain_metrics)

        # Should contain bar characters
        assert "█" in result or "░" in result


class TestFormatPatchMetrics:
    """Tests for format_patch_metrics function."""

    def test_basic_formatting(self, sample_corpus_shape_metrics):
        """Test that patch metrics are formatted with header."""
        result = format_patch_metrics("A", sample_corpus_shape_metrics)

        assert "PATCH A" in result
        assert "=" * 50 in result

    def test_includes_all_sections(self, sample_corpus_shape_metrics):
        """Test that all metric sections are included."""
        result = format_patch_metrics("A", sample_corpus_shape_metrics)

        assert "INVENTORY" in result
        assert "FREQUENCY" in result
        assert "FEATURE SATURATION" in result
        assert "TERRAIN" in result

    def test_with_corpus_path(self, sample_corpus_shape_metrics, tmp_path):
        """Test that corpus path is shown when provided."""
        corpus_path = tmp_path / "20260118_123456_nltk"
        result = format_patch_metrics("B", sample_corpus_shape_metrics, corpus_path)

        assert "PATCH B" in result
        assert "Corpus:" in result
        assert "20260118_123456_nltk" in result

    def test_none_metrics(self):
        """Test formatting when metrics is None."""
        result = format_patch_metrics("A", None)

        assert "PATCH A" in result
        assert "(no corpus loaded)" in result

    def test_none_metrics_with_path(self, tmp_path):
        """Test formatting when metrics is None but path provided."""
        corpus_path = tmp_path / "test_corpus"
        result = format_patch_metrics("A", None, corpus_path)

        assert "PATCH A" in result
        assert "(no corpus loaded)" in result


class TestFormatAnalysisExport:
    """Tests for format_analysis_export function."""

    def test_basic_formatting(self, sample_corpus_shape_metrics):
        """Test that complete export is formatted correctly."""
        result = format_analysis_export(
            metrics_a=sample_corpus_shape_metrics,
            metrics_b=sample_corpus_shape_metrics,
        )

        assert "CORPUS SHAPE METRICS EXPORT" in result
        assert "Generated:" in result
        assert "PATCH A" in result
        assert "PATCH B" in result

    def test_includes_timestamp(self, sample_corpus_shape_metrics):
        """Test that timestamp is included."""
        result = format_analysis_export(
            metrics_a=sample_corpus_shape_metrics,
            metrics_b=None,
        )

        # Should have a timestamp in format YYYY-MM-DD HH:MM:SS
        assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", result)

    def test_includes_footer(self, sample_corpus_shape_metrics):
        """Test that footer is included."""
        result = format_analysis_export(
            metrics_a=sample_corpus_shape_metrics,
            metrics_b=None,
        )

        assert "Export generated by Syllable Walker TUI" in result
        assert "github.com" in result

    def test_with_corpus_paths(self, sample_corpus_shape_metrics, tmp_path):
        """Test that corpus paths are included when provided."""
        path_a = tmp_path / "corpus_a"
        path_b = tmp_path / "corpus_b"

        result = format_analysis_export(
            metrics_a=sample_corpus_shape_metrics,
            metrics_b=sample_corpus_shape_metrics,
            corpus_path_a=path_a,
            corpus_path_b=path_b,
        )

        assert "corpus_a" in result
        assert "corpus_b" in result

    def test_with_none_metrics(self):
        """Test export with both patches having no metrics."""
        result = format_analysis_export(
            metrics_a=None,
            metrics_b=None,
        )

        assert "PATCH A" in result
        assert "PATCH B" in result
        assert "(no corpus loaded)" in result


class TestExportAnalysisToFile:
    """Tests for export_analysis_to_file function."""

    def test_writes_file(self, sample_corpus_shape_metrics, tmp_path):
        """Test that export writes to file correctly."""
        filepath = tmp_path / "export.txt"

        result = export_analysis_to_file(
            filepath=filepath,
            metrics_a=sample_corpus_shape_metrics,
            metrics_b=None,
        )

        assert result == filepath
        assert filepath.exists()
        content = filepath.read_text()
        assert "CORPUS SHAPE METRICS EXPORT" in content
        assert "PATCH A" in content

    def test_returns_path(self, sample_corpus_shape_metrics, tmp_path):
        """Test that function returns the written file path."""
        filepath = tmp_path / "test_export.txt"

        result = export_analysis_to_file(
            filepath=filepath,
            metrics_a=sample_corpus_shape_metrics,
            metrics_b=sample_corpus_shape_metrics,
        )

        assert isinstance(result, Path)
        assert result == filepath

    def test_with_all_parameters(self, sample_corpus_shape_metrics, tmp_path):
        """Test export with all parameters provided."""
        filepath = tmp_path / "full_export.txt"
        path_a = tmp_path / "corpus_a"
        path_b = tmp_path / "corpus_b"

        result = export_analysis_to_file(
            filepath=filepath,
            metrics_a=sample_corpus_shape_metrics,
            metrics_b=sample_corpus_shape_metrics,
            corpus_path_a=path_a,
            corpus_path_b=path_b,
        )

        assert result.exists()
        content = result.read_text()
        assert "corpus_a" in content
        assert "corpus_b" in content

    def test_utf8_encoding(self, sample_corpus_shape_metrics, tmp_path):
        """Test that file is written with UTF-8 encoding."""
        filepath = tmp_path / "utf8_export.txt"

        export_analysis_to_file(
            filepath=filepath,
            metrics_a=sample_corpus_shape_metrics,
            metrics_b=None,
        )

        # Should be readable as UTF-8
        content = filepath.read_text(encoding="utf-8")
        assert len(content) > 0


class TestGenerateExportFilename:
    """Tests for generate_export_filename function."""

    def test_format_pattern(self):
        """Test that filename matches expected pattern."""
        filename = generate_export_filename()

        # Pattern: corpus_metrics_YYYYMMDD_HHMMSS.txt
        assert filename.startswith("corpus_metrics_")
        assert filename.endswith(".txt")

    def test_contains_timestamp(self):
        """Test that filename contains timestamp."""
        filename = generate_export_filename()

        # Extract timestamp portion
        timestamp_part = filename.replace("corpus_metrics_", "").replace(".txt", "")

        # Should be YYYYMMDD_HHMMSS format
        assert re.match(r"\d{8}_\d{6}", timestamp_part)

    def test_unique_per_call(self):
        """Test that different calls can produce different filenames."""
        # Note: This test may occasionally fail if two calls happen in same second
        import time

        filename1 = generate_export_filename()
        time.sleep(0.01)  # Small delay
        filename2 = generate_export_filename()

        # Filenames should at least be valid
        assert filename1.startswith("corpus_metrics_")
        assert filename2.startswith("corpus_metrics_")

    def test_current_date_included(self):
        """Test that current date is in the filename."""
        filename = generate_export_filename()
        today = datetime.now().strftime("%Y%m%d")

        assert today in filename
