"""
Analysis screen modal component.

This module provides the AnalysisScreen modal for viewing corpus shape metrics.
Displays raw, objective statistics about loaded corpora without interpretation.

Design Philosophy:
    - Raw numbers only, no value judgments
    - Observable facts about corpus structure
    - Users draw their own conclusions
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Label

from build_tools.syllable_walk_tui.modules.analyzer.exporter import (
    export_analysis_to_file,
    generate_export_filename,
)
from build_tools.syllable_walk_tui.services.metrics import (
    CorpusShapeMetrics,
    TerrainMetrics,
    compute_terrain_metrics,
)
from build_tools.syllable_walk_tui.services.terrain_weights import (
    AxisWeights,
    TerrainWeights,
    create_default_terrain_weights,
)

# Bar rendering constants - Hi-fi resolution (Harbeth P3 grade)
BAR_WIDTH = 30  # Doubled from 15 for better resolution
BAR_FILLED = "█"
BAR_EMPTY = "░"

# Short names for features (for compact weight display)
FEATURE_SHORT_NAMES: dict[str, str] = {
    "contains_liquid": "liq",
    "contains_nasal": "nas",
    "contains_plosive": "plo",
    "contains_fricative": "fri",
    "ends_with_vowel": "v_end",
    "ends_with_stop": "stop",
    "ends_with_nasal": "n_end",
    "starts_with_vowel": "v_sta",
    "starts_with_cluster": "clus",
    "starts_with_heavy_cluster": "h_cl",
    "short_vowel": "sh_v",
    "long_vowel": "lg_v",
}


def format_delta(score: float) -> str:
    """
    Format score as delta from neutral (0.5).

    Args:
        score: Value from 0.0 to 1.0

    Returns:
        Formatted string like "+0.047" or "-0.023"
    """
    delta = score - 0.5
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.3f}"


def render_terrain_bar(score: float, label: str) -> str:
    """
    Render a terrain axis as an ASCII bar with pole labels.

    The bar shows position between two poles. Delta from neutral (0.5)
    is the key precision indicator.

    Args:
        score: Value from 0.0 to 1.0
        label: Text label to show after the bar (e.g., "JAGGED")

    Returns:
        Formatted string with bar, label, and delta
    """
    filled_count = int(score * BAR_WIDTH)
    empty_count = BAR_WIDTH - filled_count
    bar = BAR_FILLED * filled_count + BAR_EMPTY * empty_count
    delta = format_delta(score)
    return f"{bar} {label:8} {delta}"


def format_weight_chip(feature: str, weight: float, selected: bool = False) -> str:
    """
    Format a weight as a compact chip for display.

    Args:
        feature: Feature name
        weight: Weight value
        selected: If True, highlight this chip

    Returns:
        Formatted chip like "[liq:-0.8]" or ">>liq:-0.8<<" if selected
    """
    short = FEATURE_SHORT_NAMES.get(feature, feature[:4])
    sign = "+" if weight >= 0 else ""
    if selected:
        return f"[reverse]{short}:{sign}{weight:.1f}[/reverse]"
    return f"{short}:{sign}{weight:.1f}"


def format_weights_row(
    axis_weights: AxisWeights,
    axis_index: int,
    selected_axis: int,
    selected_weight: int,
) -> str:
    """
    Format all weights for an axis as a single row.

    Args:
        axis_weights: The weights for this axis
        axis_index: Index of this axis (0=shape, 1=craft, 2=space)
        selected_axis: Currently selected axis index
        selected_weight: Currently selected weight index within the axis

    Returns:
        Formatted string with all weight chips
    """
    chips = []
    for i, (feature, weight) in enumerate(axis_weights.items()):
        is_selected = (axis_index == selected_axis) and (i == selected_weight)
        chips.append(format_weight_chip(feature, weight, is_selected))
    return "    " + "  ".join(chips)


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

        # Shape axis (Round ↔ Jagged) - Bouba/Kiki
        yield Label("  Shape: Round ↔ Jagged (Bouba/Kiki)", classes="terrain-label")
        yield Label(
            f"    {render_terrain_bar(self.terrain.shape_score, self.terrain.shape_label)}",
            classes="terrain-row",
        )
        yield Label("", classes="terrain-row")

        # Craft axis (Flowing ↔ Worked) - Sung/Forged
        yield Label("  Craft: Flowing ↔ Worked (Sung/Forged)", classes="terrain-label")
        yield Label(
            f"    {render_terrain_bar(self.terrain.craft_score, self.terrain.craft_label)}",
            classes="terrain-row",
        )
        yield Label("", classes="terrain-row")

        # Space axis (Open ↔ Dense) - Valley/Workshop
        yield Label("  Space: Open ↔ Dense (Valley/Workshop)", classes="terrain-label")
        yield Label(
            f"    {render_terrain_bar(self.terrain.space_score, self.terrain.space_label)}",
            classes="terrain-row",
        )


class WeightsModal(Screen):
    """Modal dialog for editing terrain weights for Patch A and Patch B independently."""

    BINDINGS = [
        ("escape", "close_modal", "Close"),
        ("q", "close_modal", "Close"),
        ("tab", "next_weight", "Next weight"),
        ("shift+tab", "prev_weight", "Prev weight"),
        ("k", "increase_weight", "Increase"),
        ("j", "decrease_weight", "Decrease"),
        ("r", "reset_weights", "Reset"),
    ]

    DEFAULT_CSS = """
    WeightsModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #weights-dialog {
        width: 100;
        height: auto;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    .dialog-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .patch-header {
        text-style: bold;
        color: $primary;
        margin-top: 1;
        text-align: center;
    }

    .axis-row {
        height: auto;
        width: 100%;
    }

    .axis-label {
        width: 8;
        color: $text-muted;
    }

    .weights-value {
        width: 1fr;
        color: $text;
    }

    .dialog-footer {
        color: $text-muted;
        text-align: center;
        margin-top: 1;
        border-top: solid $primary;
        padding-top: 1;
    }
    """

    def __init__(
        self,
        weights_a: TerrainWeights,
        weights_b: TerrainWeights,
        on_close_callback: Callable[[], None] | None = None,
    ) -> None:
        """
        Initialize weights modal.

        Args:
            weights_a: TerrainWeights for Patch A (modified in place)
            weights_b: TerrainWeights for Patch B (modified in place)
            on_close_callback: Function to call when modal closes
        """
        super().__init__()
        self.weights_a = weights_a
        self.weights_b = weights_b
        self.on_close_callback = on_close_callback

        # Selection state: patch (0=A, 1=B), axis (0-2), weight index
        self.selected_patch = 0
        self.selected_axis = 0
        self.selected_weight = 0

        # Build navigation positions for both patches
        self._positions: list[tuple[int, int, int, str]] = []  # (patch, axis, weight, feature)
        self._build_positions()

    def _build_positions(self) -> None:
        """Build flat list of all weight positions for Tab navigation."""
        self._positions = []
        for patch_idx, weights in enumerate([self.weights_a, self.weights_b]):
            axes = [weights.shape, weights.craft, weights.space]
            for axis_idx, axis in enumerate(axes):
                for weight_idx, feature in enumerate(axis.feature_names()):
                    self._positions.append((patch_idx, axis_idx, weight_idx, feature))

    def _get_current_weights(self) -> TerrainWeights:
        """Get the currently selected patch's weights."""
        return self.weights_a if self.selected_patch == 0 else self.weights_b

    def _get_current_axis(self) -> AxisWeights:
        """Get the currently selected axis weights."""
        weights = self._get_current_weights()
        if self.selected_axis == 0:
            return weights.shape
        elif self.selected_axis == 1:
            return weights.craft
        else:
            return weights.space

    def _get_current_feature(self) -> str:
        """Get the currently selected feature name."""
        axis = self._get_current_axis()
        features = axis.feature_names()
        if 0 <= self.selected_weight < len(features):
            return features[self.selected_weight]
        return ""

    def _flat_index(self) -> int:
        """Get flat index in _positions for current selection."""
        for i, (patch, axis, weight, _) in enumerate(self._positions):
            if (
                patch == self.selected_patch
                and axis == self.selected_axis
                and weight == self.selected_weight
            ):
                return i
        return 0

    def _set_from_flat_index(self, idx: int) -> None:
        """Set selection from flat index."""
        if 0 <= idx < len(self._positions):
            self.selected_patch, self.selected_axis, self.selected_weight, _ = self._positions[idx]

    def _format_patch_weights(self, weights: TerrainWeights, patch_idx: int) -> list[str]:
        """Format weights for a single patch."""
        lines = []
        axis_names = ["Shape", "Craft", "Space"]
        axes = [weights.shape, weights.craft, weights.space]

        for axis_idx, (name, axis) in enumerate(zip(axis_names, axes)):
            lines.append(f"  {name}:")
            row = format_weights_row(
                axis,
                axis_idx,
                self.selected_axis if self.selected_patch == patch_idx else -1,
                self.selected_weight if self.selected_patch == patch_idx else -1,
            )
            lines.append(row)
        return lines

    def compose(self) -> ComposeResult:
        """Create weights dialog layout."""
        with Vertical(id="weights-dialog"):
            yield Label("TERRAIN WEIGHTS", classes="dialog-title")

            # Patch A
            yield Label("─── PATCH A ───", classes="patch-header")
            with Horizontal(classes="axis-row"):
                yield Label("Shape:", classes="axis-label")
                yield Label("", classes="weights-value", id="a-shape", markup=True)
            with Horizontal(classes="axis-row"):
                yield Label("Craft:", classes="axis-label")
                yield Label("", classes="weights-value", id="a-craft", markup=True)
            with Horizontal(classes="axis-row"):
                yield Label("Space:", classes="axis-label")
                yield Label("", classes="weights-value", id="a-space", markup=True)

            # Patch B
            yield Label("─── PATCH B ───", classes="patch-header")
            with Horizontal(classes="axis-row"):
                yield Label("Shape:", classes="axis-label")
                yield Label("", classes="weights-value", id="b-shape", markup=True)
            with Horizontal(classes="axis-row"):
                yield Label("Craft:", classes="axis-label")
                yield Label("", classes="weights-value", id="b-craft", markup=True)
            with Horizontal(classes="axis-row"):
                yield Label("Space:", classes="axis-label")
                yield Label("", classes="weights-value", id="b-space", markup=True)

            yield Label(
                "\\[Tab] navigate  \\[j/k] adjust  \\[r] reset  \\[q] close",
                classes="dialog-footer",
            )

    def on_mount(self) -> None:
        """Initialize display after mounting."""
        self._refresh_weights()

    def _refresh_weights(self) -> None:
        """Refresh the weights display for both patches."""
        # Determine selection for each patch
        sel_a_axis = self.selected_axis if self.selected_patch == 0 else -1
        sel_a_weight = self.selected_weight if self.selected_patch == 0 else -1
        sel_b_axis = self.selected_axis if self.selected_patch == 1 else -1
        sel_b_weight = self.selected_weight if self.selected_patch == 1 else -1

        # Update Patch A
        self.query_one("#a-shape", Label).update(
            format_weights_row(self.weights_a.shape, 0, sel_a_axis, sel_a_weight)
        )
        self.query_one("#a-craft", Label).update(
            format_weights_row(self.weights_a.craft, 1, sel_a_axis, sel_a_weight)
        )
        self.query_one("#a-space", Label).update(
            format_weights_row(self.weights_a.space, 2, sel_a_axis, sel_a_weight)
        )

        # Update Patch B
        self.query_one("#b-shape", Label).update(
            format_weights_row(self.weights_b.shape, 0, sel_b_axis, sel_b_weight)
        )
        self.query_one("#b-craft", Label).update(
            format_weights_row(self.weights_b.craft, 1, sel_b_axis, sel_b_weight)
        )
        self.query_one("#b-space", Label).update(
            format_weights_row(self.weights_b.space, 2, sel_b_axis, sel_b_weight)
        )

    def action_close_modal(self) -> None:
        """Close the modal and trigger callback."""
        if self.on_close_callback:
            self.on_close_callback()
        self.app.pop_screen()

    def action_next_weight(self) -> None:
        """Navigate to next weight (Tab)."""
        idx = self._flat_index()
        idx = (idx + 1) % len(self._positions)
        self._set_from_flat_index(idx)
        self._refresh_weights()

    def action_prev_weight(self) -> None:
        """Navigate to previous weight (Shift+Tab)."""
        idx = self._flat_index()
        idx = (idx - 1) % len(self._positions)
        self._set_from_flat_index(idx)
        self._refresh_weights()

    def action_decrease_weight(self) -> None:
        """Decrease selected weight by 0.1 (j key)."""
        feature = self._get_current_feature()
        axis = self._get_current_axis()
        current = axis.get(feature)
        axis.set(feature, round(current - 0.1, 1))
        self._refresh_weights()

    def action_increase_weight(self) -> None:
        """Increase selected weight by 0.1 (k key)."""
        feature = self._get_current_feature()
        axis = self._get_current_axis()
        current = axis.get(feature)
        axis.set(feature, round(current + 0.1, 1))
        self._refresh_weights()

    def action_reset_weights(self) -> None:
        """Reset current patch's weights to defaults."""
        defaults = create_default_terrain_weights()
        if self.selected_patch == 0:
            self.weights_a.shape = defaults.shape
            self.weights_a.craft = defaults.craft
            self.weights_a.space = defaults.space
            self.notify("Patch A weights reset")
        else:
            self.weights_b.shape = defaults.shape
            self.weights_b.craft = defaults.craft
            self.weights_b.space = defaults.space
            self.notify("Patch B weights reset")
        self._build_positions()
        self._refresh_weights()


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

    def __init__(
        self,
        patch_name: str,
        metrics: CorpusShapeMetrics | None = None,
    ) -> None:
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
    - Terrain visualization

    Design Philosophy:
        Raw numbers only, no interpretation or judgment.
        Users observe and draw their own conclusions.

    Keybindings:
        Esc: Close screen and return to main view
        q: Close screen
        e: Export metrics to text file
        w: Open weights editor modal
    """

    BINDINGS = [
        ("escape", "close_screen", "Close"),
        ("q", "close_screen", "Close"),
        ("e", "export_metrics", "Export"),
        ("w", "open_weights", "Weights"),
    ]

    DEFAULT_CSS = """
    AnalysisScreen {
        background: $surface;
    }

    #analysis-header {
        dock: top;
        height: 1;
        background: $boost;
        color: $text;
        text-style: bold;
        text-align: center;
    }

    #analysis-content {
        width: 100%;
        height: 1fr;
    }

    .patch-metrics {
        width: 1fr;
        height: auto;
        border: solid $primary;
        overflow-y: auto;
    }

    #analysis-footer {
        dock: bottom;
        height: 1;
        background: $boost;
        color: $text;
        padding: 0 1;
        text-align: center;
    }
    """

    def __init__(
        self,
        metrics_a: CorpusShapeMetrics | None = None,
        metrics_b: CorpusShapeMetrics | None = None,
        corpus_path_a: Path | None = None,
        corpus_path_b: Path | None = None,
        export_dir: Path | None = None,
    ) -> None:
        """
        Initialize analysis screen with pre-computed metrics.

        Args:
            metrics_a: Pre-computed metrics for Patch A, or None if not loaded
            metrics_b: Pre-computed metrics for Patch B, or None if not loaded
            corpus_path_a: Path to Patch A corpus directory
            corpus_path_b: Path to Patch B corpus directory
            export_dir: Directory for exports (defaults to _working/)

        Note:
            Metrics should be computed by the app before pushing this screen,
            as self.app is not available during compose().
        """
        super().__init__()
        self.metrics_a = metrics_a
        self.metrics_b = metrics_b
        self.corpus_path_a = corpus_path_a
        self.corpus_path_b = corpus_path_b
        self.export_dir = export_dir or Path("_working")

        # Store feature saturation for re-computing terrain with different weights
        self.feature_saturation_a = metrics_a.feature_saturation if metrics_a else None
        self.feature_saturation_b = metrics_b.feature_saturation if metrics_b else None

        # Independent weights for each patch (mutable, shared with weights modal)
        self.weights_a = create_default_terrain_weights()
        self.weights_b = create_default_terrain_weights()

    def _recompute_terrain(self) -> None:
        """Recompute terrain metrics with current weights for each patch."""
        if self.feature_saturation_a and self.metrics_a:
            new_terrain = compute_terrain_metrics(self.feature_saturation_a, self.weights_a)
            self.metrics_a = CorpusShapeMetrics(
                inventory=self.metrics_a.inventory,
                frequency=self.metrics_a.frequency,
                feature_saturation=self.metrics_a.feature_saturation,
                terrain=new_terrain,
            )
        if self.feature_saturation_b and self.metrics_b:
            new_terrain = compute_terrain_metrics(self.feature_saturation_b, self.weights_b)
            self.metrics_b = CorpusShapeMetrics(
                inventory=self.metrics_b.inventory,
                frequency=self.metrics_b.frequency,
                feature_saturation=self.metrics_b.feature_saturation,
                terrain=new_terrain,
            )

    def _refresh_display(self) -> None:
        """Refresh the screen with updated metrics."""
        content = self.query_one("#analysis-content", Horizontal)
        content.remove_children()

        patch_a = Vertical(MetricsDisplay("A", self.metrics_a), classes="patch-metrics")
        patch_b = Vertical(MetricsDisplay("B", self.metrics_b), classes="patch-metrics")
        content.mount(patch_a, patch_b)

    def compose(self) -> ComposeResult:
        """Create analysis screen layout."""
        # Header
        yield Label("CORPUS SHAPE METRICS", id="analysis-header", classes="analysis-title")

        # Main content: side-by-side metrics
        with Horizontal(id="analysis-content"):
            with Vertical(classes="patch-metrics"):
                yield MetricsDisplay("A", self.metrics_a)
            with Vertical(classes="patch-metrics"):
                yield MetricsDisplay("B", self.metrics_b)

        # Footer
        yield Label(
            "\\[w] weights  \\[e] export  |  \\[Esc] or \\[q] close",
            id="analysis-footer",
            classes="footer-hint",
        )

    def action_close_screen(self) -> None:
        """Close this screen and return to main view."""
        self.app.pop_screen()

    def action_export_metrics(self) -> None:
        """Export metrics to a text file."""
        self.export_dir.mkdir(parents=True, exist_ok=True)

        filename = generate_export_filename()
        filepath = self.export_dir / filename

        try:
            export_analysis_to_file(
                filepath=filepath,
                metrics_a=self.metrics_a,
                metrics_b=self.metrics_b,
                corpus_path_a=self.corpus_path_a,
                corpus_path_b=self.corpus_path_b,
            )
            self.notify(f"Exported to {filepath}", title="Export Complete", severity="information")
        except OSError as e:
            self.notify(f"Export failed: {e}", title="Export Error", severity="error")

    def action_open_weights(self) -> None:
        """Open the weights editor modal."""

        def on_weights_closed() -> None:
            """Callback when weights modal closes."""
            self._recompute_terrain()
            self._refresh_display()

        self.app.push_screen(WeightsModal(self.weights_a, self.weights_b, on_weights_closed))
