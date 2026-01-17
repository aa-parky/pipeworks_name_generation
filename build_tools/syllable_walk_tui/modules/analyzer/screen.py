"""
Analysis screen modal component.

This module provides the AnalysisScreen modal for viewing corpus shape metrics.
Displays raw, objective statistics about loaded corpora without interpretation.

Design Philosophy:
    - Raw numbers only, no value judgments
    - Observable facts about corpus structure
    - Users draw their own conclusions
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Label

from build_tools.syllable_walk_tui.services.metrics import CorpusShapeMetrics, TerrainMetrics

# Bar rendering constants
BAR_WIDTH = 15  # Total width of the bar (filled + empty)
BAR_FILLED = "█"
BAR_EMPTY = "░"


def render_terrain_bar(score: float, label: str) -> str:
    """
    Render a terrain axis as an ASCII bar.

    Args:
        score: Value from 0.0 to 1.0
        label: Text label to show after the bar (e.g., "JAGGED")

    Returns:
        Formatted string like "████████░░░░░░░ JAGGED"
    """
    filled_count = int(score * BAR_WIDTH)
    empty_count = BAR_WIDTH - filled_count
    bar = BAR_FILLED * filled_count + BAR_EMPTY * empty_count
    return f"{bar} {label}"


class TerrainDisplay(Vertical):
    """Widget for displaying terrain visualization bars."""

    DEFAULT_CSS = """
    TerrainDisplay {
        width: auto;
        height: auto;
        padding: 0 1;
    }

    TerrainDisplay .terrain-header {
        text-style: bold;
        color: $accent;
    }

    TerrainDisplay .terrain-row {
        color: $text;
    }

    TerrainDisplay .terrain-label {
        color: $text-muted;
    }
    """

    def __init__(self, terrain: TerrainMetrics | None = None) -> None:
        """
        Initialize terrain display.

        Args:
            terrain: Computed terrain metrics, or None if not available
        """
        super().__init__()
        self.terrain = terrain

    def compose(self) -> ComposeResult:
        """Create terrain display layout."""
        yield Label("TERRAIN", classes="terrain-header")
        yield Label("", classes="terrain-row")

        if self.terrain is None:
            yield Label("(no data)", classes="terrain-label")
            return

        # Shape axis (Round ↔ Jagged)
        yield Label("  Shape:", classes="terrain-label")
        yield Label(
            f"    {render_terrain_bar(self.terrain.shape_score, self.terrain.shape_label)}",
            classes="terrain-row",
        )

        # Craft axis (Flowing ↔ Worked)
        yield Label("  Craft:", classes="terrain-label")
        yield Label(
            f"    {render_terrain_bar(self.terrain.craft_score, self.terrain.craft_label)}",
            classes="terrain-row",
        )

        # Space axis (Open ↔ Dense)
        yield Label("  Space:", classes="terrain-label")
        yield Label(
            f"    {render_terrain_bar(self.terrain.space_score, self.terrain.space_label)}",
            classes="terrain-row",
        )


class FeatureSaturationDisplay(Vertical):
    """Widget for displaying feature saturation metrics."""

    DEFAULT_CSS = """
    FeatureSaturationDisplay {
        width: auto;
        height: auto;
    }

    FeatureSaturationDisplay .feat-header {
        text-style: bold;
        color: $text;
    }

    FeatureSaturationDisplay .feat-row {
        color: $text;
    }

    FeatureSaturationDisplay .feat-label {
        color: $text-muted;
    }
    """

    def __init__(self, metrics: CorpusShapeMetrics | None = None) -> None:
        """Initialize feature saturation display."""
        super().__init__()
        self.metrics = metrics

    def compose(self) -> ComposeResult:
        """Create feature saturation display."""
        if self.metrics is None:
            yield Label("(no data)", classes="feat-label")
            return

        feat = self.metrics.feature_saturation

        yield Label("FEATURE SATURATION", classes="feat-header")
        yield Label(f"  Total analyzed:     {feat.total_syllables:,}", classes="feat-row")
        yield Label("", classes="feat-row")

        # Group features by category
        onset_features = ["starts_with_vowel", "starts_with_cluster", "starts_with_heavy_cluster"]
        internal_features = [
            "contains_plosive",
            "contains_fricative",
            "contains_liquid",
            "contains_nasal",
        ]
        nucleus_features = ["short_vowel", "long_vowel"]
        coda_features = ["ends_with_vowel", "ends_with_nasal", "ends_with_stop"]

        yield Label("  Onset:", classes="feat-label")
        for name in onset_features:
            fs = feat.by_name[name]
            short_name = name.replace("starts_with_", "").replace("_", " ")
            yield Label(
                f"    {short_name:18} {fs.true_count:>6,} ({fs.true_percentage:5.1f}%)",
                classes="feat-row",
            )

        yield Label("  Internal:", classes="feat-label")
        for name in internal_features:
            fs = feat.by_name[name]
            short_name = name.replace("contains_", "").replace("_", " ")
            yield Label(
                f"    {short_name:18} {fs.true_count:>6,} ({fs.true_percentage:5.1f}%)",
                classes="feat-row",
            )

        yield Label("  Nucleus:", classes="feat-label")
        for name in nucleus_features:
            fs = feat.by_name[name]
            short_name = name.replace("_", " ")
            yield Label(
                f"    {short_name:18} {fs.true_count:>6,} ({fs.true_percentage:5.1f}%)",
                classes="feat-row",
            )

        yield Label("  Coda:", classes="feat-label")
        for name in coda_features:
            fs = feat.by_name[name]
            short_name = name.replace("ends_with_", "").replace("_", " ")
            yield Label(
                f"    {short_name:18} {fs.true_count:>6,} ({fs.true_percentage:5.1f}%)",
                classes="feat-row",
            )


class MetricsDisplay(Vertical):
    """Widget for displaying corpus shape metrics."""

    DEFAULT_CSS = """
    MetricsDisplay {
        width: 100%;
        height: auto;
        padding: 0 1;
    }

    MetricsDisplay .metrics-header {
        text-style: bold;
        color: $accent;
        margin-bottom: 0;
    }

    MetricsDisplay .metrics-subheader {
        text-style: bold;
        color: $text;
        margin-top: 1;
    }

    MetricsDisplay .metrics-row {
        color: $text;
    }

    MetricsDisplay .metrics-dim {
        color: $text-muted;
    }

    MetricsDisplay .feature-terrain-row {
        height: auto;
        margin-top: 1;
    }
    """

    def __init__(self, patch_name: str, metrics: CorpusShapeMetrics | None = None) -> None:
        """
        Initialize metrics display.

        Args:
            patch_name: "A" or "B" to identify the patch
            metrics: Computed corpus shape metrics, or None if not loaded
        """
        super().__init__()
        self.patch_name = patch_name
        self.metrics = metrics

    def compose(self) -> ComposeResult:
        """Create metrics display layout."""
        yield Label(f"PATCH {self.patch_name}", classes="metrics-header")
        yield Label("─" * 40, classes="metrics-dim")

        if self.metrics is None:
            yield Label("(no corpus loaded)", classes="metrics-dim")
            return

        # === INVENTORY METRICS ===
        inv = self.metrics.inventory
        yield Label("INVENTORY", classes="metrics-subheader")
        yield Label(f"  Total syllables:    {inv.total_count:,}", classes="metrics-row")
        yield Label(f"  Length min:         {inv.length_min}", classes="metrics-row")
        yield Label(f"  Length max:         {inv.length_max}", classes="metrics-row")
        yield Label(f"  Length mean:        {inv.length_mean:.2f}", classes="metrics-row")
        yield Label(f"  Length median:      {inv.length_median:.1f}", classes="metrics-row")
        yield Label(f"  Length std:         {inv.length_std:.2f}", classes="metrics-row")

        # Length distribution (compact)
        dist_str = "  Length dist:        "
        dist_parts = [f"{k}:{v}" for k, v in sorted(inv.length_distribution.items())]
        yield Label(dist_str + ", ".join(dist_parts[:6]), classes="metrics-row")
        if len(dist_parts) > 6:
            yield Label("                      " + ", ".join(dist_parts[6:]), classes="metrics-row")

        # === FREQUENCY METRICS ===
        freq = self.metrics.frequency
        yield Label("FREQUENCY", classes="metrics-subheader")
        yield Label(f"  Total occurrences:  {freq.total_occurrences:,}", classes="metrics-row")
        yield Label(f"  Freq min:           {freq.freq_min:,}", classes="metrics-row")
        yield Label(f"  Freq max:           {freq.freq_max:,}", classes="metrics-row")
        yield Label(f"  Freq mean:          {freq.freq_mean:.2f}", classes="metrics-row")
        yield Label(f"  Freq median:        {freq.freq_median:.1f}", classes="metrics-row")
        yield Label(f"  Freq std:           {freq.freq_std:.2f}", classes="metrics-row")
        yield Label(f"  Unique freq values: {freq.unique_freq_count:,}", classes="metrics-row")
        yield Label(f"  Hapax (freq=1):     {freq.hapax_count:,}", classes="metrics-row")

        # Percentiles
        yield Label("  Percentiles:", classes="metrics-row")
        yield Label(
            f"    P10={freq.percentile_10:,}  P25={freq.percentile_25:,}  "
            f"P50={freq.percentile_50:,}",
            classes="metrics-row",
        )
        yield Label(
            f"    P75={freq.percentile_75:,}  P90={freq.percentile_90:,}  "
            f"P99={freq.percentile_99:,}",
            classes="metrics-row",
        )

        # Top 5 syllables
        yield Label("  Top 5 by frequency:", classes="metrics-row")
        for syl, count in freq.top_10[:5]:
            yield Label(f"    {syl}: {count:,}", classes="metrics-row")

        # === FEATURE SATURATION + TERRAIN (side by side) ===
        with Horizontal(classes="feature-terrain-row"):
            yield FeatureSaturationDisplay(self.metrics)
            yield TerrainDisplay(self.metrics.terrain)


class AnalysisScreen(Screen):
    """
    Modal screen for viewing corpus shape metrics.

    Displays raw, objective statistics about loaded corpora:
    - Inventory metrics (counts, lengths)
    - Frequency distribution metrics
    - Feature saturation per phonetic feature

    Design Philosophy:
        Raw numbers only, no interpretation or judgment.
        Users observe and draw their own conclusions.

    Keybindings:
        Esc: Close screen and return to main view
        q: Close screen
    """

    BINDINGS = [
        ("escape", "close_screen", "Close"),
        ("q", "close_screen", "Close"),
    ]

    DEFAULT_CSS = """
    AnalysisScreen {
        background: $surface;
    }

    #analysis-header {
        dock: top;
        height: 1;
        background: $primary;
        text-style: bold;
        text-align: center;
    }

    #analysis-content {
        width: 100%;
        height: 1fr;
    }

    .patch-metrics {
        width: 1fr;
        height: 100%;
        border: solid $primary;
    }

    #analysis-footer {
        dock: bottom;
        height: 1;
        background: $primary-darken-1;
        padding: 0 1;
        color: $text;
        text-align: center;
    }
    """

    def __init__(
        self,
        metrics_a: CorpusShapeMetrics | None = None,
        metrics_b: CorpusShapeMetrics | None = None,
    ) -> None:
        """
        Initialize analysis screen with pre-computed metrics.

        Args:
            metrics_a: Pre-computed metrics for Patch A, or None if not loaded
            metrics_b: Pre-computed metrics for Patch B, or None if not loaded

        Note:
            Metrics should be computed by the app before pushing this screen,
            as self.app is not available during compose().
        """
        super().__init__()
        self.metrics_a = metrics_a
        self.metrics_b = metrics_b

    def compose(self) -> ComposeResult:
        """Create analysis screen layout."""
        # Header
        yield Label("CORPUS SHAPE METRICS", id="analysis-header", classes="analysis-title")

        # Main content: side-by-side metrics (using pre-computed metrics)
        with Horizontal(id="analysis-content"):
            with VerticalScroll(classes="patch-metrics"):
                yield MetricsDisplay("A", self.metrics_a)
            with VerticalScroll(classes="patch-metrics"):
                yield MetricsDisplay("B", self.metrics_b)

        # Footer
        yield Label("Press Esc or q to close", id="analysis-footer", classes="footer-hint")

    def action_close_screen(self) -> None:
        """Close this screen and return to main view."""
        self.app.pop_screen()
