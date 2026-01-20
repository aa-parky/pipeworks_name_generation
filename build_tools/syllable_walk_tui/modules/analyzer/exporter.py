"""
Analysis export functionality.

This module provides functions to export corpus shape metrics to text format
for sharing and discussion. Exports are human-readable and include all metrics
displayed on the AnalysisScreen.

Design Philosophy:
    - Mirror the screen display in text form
    - Include timestamps and corpus paths for provenance
    - Pure formatting functions (no side effects except final write)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from build_tools.syllable_walk_tui.services.metrics import (
        CorpusShapeMetrics,
        FeatureSaturationMetrics,
        FrequencyMetrics,
        InventoryMetrics,
        PoleExemplars,
        TerrainMetrics,
    )


def format_inventory_metrics(inv: InventoryMetrics) -> str:
    """
    Format inventory metrics as text.

    Args:
        inv: Inventory metrics to format

    Returns:
        Formatted text block
    """
    lines = [
        "INVENTORY",
        f"  Total syllables:    {inv.total_count:,}",
        f"  Length min:         {inv.length_min}",
        f"  Length max:         {inv.length_max}",
        f"  Length mean:        {inv.length_mean:.2f}",
        f"  Length median:      {inv.length_median:.1f}",
        f"  Length std:         {inv.length_std:.2f}",
    ]

    # Length distribution
    dist_parts = [f"{k}:{v}" for k, v in sorted(inv.length_distribution.items())]
    lines.append(f"  Length dist:        {', '.join(dist_parts)}")

    return "\n".join(lines)


def format_frequency_metrics(freq: FrequencyMetrics) -> str:
    """
    Format frequency metrics as text.

    Args:
        freq: Frequency metrics to format

    Returns:
        Formatted text block
    """
    lines = [
        "FREQUENCY",
        f"  Total occurrences:  {freq.total_occurrences:,}",
        f"  Freq min:           {freq.freq_min:,}",
        f"  Freq max:           {freq.freq_max:,}",
        f"  Freq mean:          {freq.freq_mean:.2f}",
        f"  Freq median:        {freq.freq_median:.1f}",
        f"  Freq std:           {freq.freq_std:.2f}",
        f"  Unique freq values: {freq.unique_freq_count:,}",
        f"  Hapax (freq=1):     {freq.hapax_count:,}",
        "",
        "  Percentiles:",
        f"    P10={freq.percentile_10:,}  P25={freq.percentile_25:,}  "
        f"P50={freq.percentile_50:,}",
        f"    P75={freq.percentile_75:,}  P90={freq.percentile_90:,}  "
        f"P99={freq.percentile_99:,}",
        "",
        "  Top 5 by frequency:",
    ]

    for syl, count in freq.top_10[:5]:
        lines.append(f"    {syl}: {count:,}")

    return "\n".join(lines)


def format_feature_saturation(feat: FeatureSaturationMetrics) -> str:
    """
    Format feature saturation metrics as text.

    Args:
        feat: Feature saturation metrics to format

    Returns:
        Formatted text block
    """
    lines = [
        "FEATURE SATURATION",
        f"  Total analyzed:     {feat.total_syllables:,}",
        "",
    ]

    # Group features by category
    categories = {
        "Onset": ["starts_with_vowel", "starts_with_cluster", "starts_with_heavy_cluster"],
        "Internal": ["contains_plosive", "contains_fricative", "contains_liquid", "contains_nasal"],
        "Nucleus": ["short_vowel", "long_vowel"],
        "Coda": ["ends_with_vowel", "ends_with_nasal", "ends_with_stop"],
    }

    for category, feature_names in categories.items():
        lines.append(f"  {category}:")
        for name in feature_names:
            fs = feat.by_name[name]
            # Clean up feature name for display
            short_name = (
                name.replace("starts_with_", "")
                .replace("ends_with_", "")
                .replace("contains_", "")
                .replace("_", " ")
            )
            lines.append(f"    {short_name:18} {fs.true_count:>6,} ({fs.true_percentage:5.1f}%)")

    return "\n".join(lines)


def _format_exemplars_line(
    exemplars: PoleExemplars | None,
    low_label: str,
    high_label: str,
) -> str | None:
    """
    Format exemplar syllables for both poles of an axis.

    Args:
        exemplars: PoleExemplars containing syllables from each pole, or None
        low_label: Label for low pole (e.g., "round")
        high_label: Label for high pole (e.g., "jagged")

    Returns:
        Formatted string or None if no exemplars
    """
    if exemplars is None:
        return None

    low_str = ", ".join(exemplars.low_pole_exemplars) or "(none)"
    high_str = ", ".join(exemplars.high_pole_exemplars) or "(none)"

    return f"    {low_label}: {low_str}    {high_label}: {high_str}"


def format_terrain_metrics(terrain: TerrainMetrics) -> str:
    """
    Format terrain metrics as text with ASCII bars.

    Hi-fi resolution (30 chars) with center marker and delta display.

    Args:
        terrain: Terrain metrics to format

    Returns:
        Formatted text block with visualization
    """
    bar_width = 30  # Hi-fi resolution
    bar_filled = "█"
    bar_empty = "░"

    def format_delta(score: float) -> str:
        delta = score - 0.5
        sign = "+" if delta >= 0 else ""
        return f"{sign}{delta:.3f}"

    def render_bar(score: float, label: str) -> str:
        filled_count = int(score * bar_width)
        empty_count = bar_width - filled_count
        bar = bar_filled * filled_count + bar_empty * empty_count
        delta = format_delta(score)
        return f"{bar} {label:8} {delta}"

    lines = [
        "TERRAIN",
        "",
        "  Shape: Round <-> Jagged (Bouba/Kiki)",
        f"    {render_bar(terrain.shape_score, terrain.shape_label)}",
    ]
    exemplar_line = _format_exemplars_line(terrain.shape_exemplars, "round", "jagged")
    if exemplar_line:
        lines.append(exemplar_line)
    lines.append("")

    lines.append("  Craft: Flowing <-> Worked (Sung/Forged)")
    lines.append(f"    {render_bar(terrain.craft_score, terrain.craft_label)}")
    exemplar_line = _format_exemplars_line(terrain.craft_exemplars, "flowing", "worked")
    if exemplar_line:
        lines.append(exemplar_line)
    lines.append("")

    lines.append("  Space: Open <-> Dense (Valley/Workshop)")
    lines.append(f"    {render_bar(terrain.space_score, terrain.space_label)}")
    exemplar_line = _format_exemplars_line(terrain.space_exemplars, "open", "dense")
    if exemplar_line:
        lines.append(exemplar_line)

    return "\n".join(lines)


def format_patch_metrics(
    patch_name: str,
    metrics: CorpusShapeMetrics | None,
    corpus_path: Path | None = None,
) -> str:
    """
    Format all metrics for a single patch.

    Args:
        patch_name: "A" or "B"
        metrics: Corpus shape metrics, or None if not loaded
        corpus_path: Optional path to corpus directory

    Returns:
        Formatted text block for entire patch
    """
    header = f"PATCH {patch_name}"
    separator = "=" * 50

    lines = [separator, header, separator]

    if corpus_path:
        lines.append(f"Corpus: {corpus_path.name}")
        lines.append("")

    if metrics is None:
        lines.append("(no corpus loaded)")
        return "\n".join(lines)

    lines.append(format_inventory_metrics(metrics.inventory))
    lines.append("")
    lines.append(format_frequency_metrics(metrics.frequency))
    lines.append("")
    lines.append(format_feature_saturation(metrics.feature_saturation))
    lines.append("")
    lines.append(format_terrain_metrics(metrics.terrain))

    return "\n".join(lines)


def format_analysis_export(
    metrics_a: CorpusShapeMetrics | None,
    metrics_b: CorpusShapeMetrics | None,
    corpus_path_a: Path | None = None,
    corpus_path_b: Path | None = None,
) -> str:
    """
    Format complete analysis export for both patches.

    Args:
        metrics_a: Metrics for Patch A, or None if not loaded
        metrics_b: Metrics for Patch B, or None if not loaded
        corpus_path_a: Optional path to Patch A corpus
        corpus_path_b: Optional path to Patch B corpus

    Returns:
        Complete formatted export text
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    header = [
        "CORPUS SHAPE METRICS EXPORT",
        f"Generated: {timestamp}",
        "",
    ]

    patch_a_text = format_patch_metrics("A", metrics_a, corpus_path_a)
    patch_b_text = format_patch_metrics("B", metrics_b, corpus_path_b)

    footer = [
        "",
        "=" * 50,
        "Export generated by Syllable Walker TUI",
        "https://github.com/aa-parky/pipeworks_name_generation",
    ]

    return "\n".join(header + [patch_a_text, "", patch_b_text] + footer)


def export_analysis_to_file(
    filepath: Path,
    metrics_a: CorpusShapeMetrics | None,
    metrics_b: CorpusShapeMetrics | None,
    corpus_path_a: Path | None = None,
    corpus_path_b: Path | None = None,
) -> Path:
    """
    Export analysis to a text file.

    Args:
        filepath: Path to write the export file
        metrics_a: Metrics for Patch A, or None if not loaded
        metrics_b: Metrics for Patch B, or None if not loaded
        corpus_path_a: Optional path to Patch A corpus
        corpus_path_b: Optional path to Patch B corpus

    Returns:
        Path to the written file

    Raises:
        OSError: If file cannot be written
    """
    content = format_analysis_export(
        metrics_a=metrics_a,
        metrics_b=metrics_b,
        corpus_path_a=corpus_path_a,
        corpus_path_b=corpus_path_b,
    )

    filepath.write_text(content, encoding="utf-8")
    return filepath


def generate_export_filename() -> str:
    """
    Generate a timestamped filename for export.

    Returns:
        Filename like "corpus_metrics_20260118_143022.txt"
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"corpus_metrics_{timestamp}.txt"
