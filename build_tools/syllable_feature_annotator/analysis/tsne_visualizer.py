"""t-SNE Visualization for Feature Signature Space

This build-time analysis tool creates a t-SNE (t-distributed Stochastic Neighbor Embedding)
visualization of the feature signature space in the annotated syllable corpus.

t-SNE is a dimensionality reduction technique that projects high-dimensional feature vectors
into 2D space while preserving local structure. This visualization helps identify:
- Clustering patterns in the feature space
- Syllable similarity based on phonetic features
- Natural groupings and outliers in the corpus

The visualization uses:
- Position (x, y): t-SNE projection of 12-dimensional feature vectors
- Size: Syllable frequency (larger points = more common syllables)
- Color: Syllable frequency (warmer colors = more common syllables)

Technical Details:
- Uses Hamming distance metric (optimal for binary feature vectors)
- Perplexity=30 (balances local vs global structure)
- Fixed random seed for reproducibility (seed=42)

Output Formats:
- Static PNG: High-resolution matplotlib visualization (always generated)
- Interactive HTML: Plotly-based interactive visualization (optional, requires --interactive flag)

Usage:
    # Generate static PNG visualization with default paths
    python -m build_tools.syllable_feature_annotator.analysis.tsne_visualizer

    # Generate both static PNG and interactive HTML
    python -m build_tools.syllable_feature_annotator.analysis.tsne_visualizer \\
        --interactive \\
        --save-mapping

    # Custom input/output paths
    python -m build_tools.syllable_feature_annotator.analysis.tsne_visualizer \\
        --input data/annotated/syllables_annotated.json \\
        --output _working/analysis/tsne/ \\
        --interactive

    # Adjust t-SNE parameters
    python -m build_tools.syllable_feature_annotator.analysis.tsne_visualizer \\
        --perplexity 50 \\
        --random-state 123 \\
        --interactive

    # High-resolution output with interactive HTML
    python -m build_tools.syllable_feature_annotator.analysis.tsne_visualizer \\
        --dpi 600 \\
        --interactive \\
        --save-mapping

Programmatic Usage:
    >>> from pathlib import Path
    >>> from build_tools.syllable_feature_annotator.analysis import (
    ...     run_tsne_visualization,
    ...     extract_feature_matrix
    ... )
    >>> result = run_tsne_visualization(
    ...     input_path=Path("data/annotated/syllables_annotated.json"),
    ...     output_dir=Path("_working/analysis/tsne/"),
    ...     perplexity=30,
    ...     random_state=42,
    ...     interactive=True,
    ...     save_mapping=True
    ... )
    >>> print(f"Static visualization: {result['output_path']}")
    >>> print(f"Interactive HTML: {result['interactive_path']}")
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt  # type: ignore[import-not-found]
import numpy as np  # type: ignore[import-not-found]

# Optional dependency: Plotly for interactive visualizations
try:
    import plotly.graph_objects as go  # type: ignore[import-not-found]

    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False

# Calculate project root (this file is in build_tools/syllable_feature_annotator/analysis/)
ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Default paths
DEFAULT_INPUT = ROOT / "data" / "annotated" / "syllables_annotated.json"
DEFAULT_OUTPUT_DIR = ROOT / "_working" / "analysis" / "tsne"

# All features tracked by the annotator (order matters for consistent feature vectors)
ALL_FEATURES = [
    "contains_liquid",
    "contains_plosive",
    "contains_fricative",
    "contains_nasal",
    "long_vowel",
    "short_vowel",
    "starts_with_vowel",
    "starts_with_cluster",
    "starts_with_heavy_cluster",
    "ends_with_vowel",
    "ends_with_stop",
    "ends_with_nasal",
]


def load_annotated_data(input_path: Path) -> List[Dict]:
    """Load annotated syllable corpus from JSON file.

    Args:
        input_path: Path to syllables_annotated.json

    Returns:
        List of annotated syllable records, each containing:
            - syllable (str): The syllable text
            - frequency (int): Occurrence count in corpus
            - features (dict): Boolean feature flags

    Raises:
        FileNotFoundError: If input file does not exist
        json.JSONDecodeError: If input file is not valid JSON
        ValueError: If input data structure is invalid
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_path.open(encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records).__name__}")

    if not records:
        raise ValueError("Input file contains no records")

    # Validate first record has expected structure
    if not all(key in records[0] for key in ["syllable", "frequency", "features"]):
        raise ValueError("Records missing required keys: syllable, frequency, features")

    return records


def extract_feature_matrix(records: List[Dict]) -> Tuple[np.ndarray, List[int]]:
    """Extract feature matrix and frequency vector from annotated records.

    Converts the feature dictionaries into a numerical matrix suitable for t-SNE.
    Each row represents a syllable, each column represents a feature (0 or 1).

    Args:
        records: List of annotated syllable records

    Returns:
        Tuple of (feature_matrix, frequencies):
            - feature_matrix: numpy array of shape (n_syllables, 12) with binary values
            - frequencies: List of frequency counts for each syllable

    Example:
        >>> records = [
        ...     {
        ...         "syllable": "ka",
        ...         "frequency": 187,
        ...         "features": {"contains_liquid": False, "contains_plosive": True, ...}
        ...     }
        ... ]
        >>> matrix, freqs = extract_feature_matrix(records)
        >>> matrix.shape
        (1, 12)
        >>> freqs
        [187]
    """
    feature_matrix = []
    frequencies = []

    for record in records:
        # Extract feature values in consistent order
        feature_vector = [int(record["features"].get(feat, False)) for feat in ALL_FEATURES]
        feature_matrix.append(feature_vector)
        frequencies.append(record["frequency"])

    return np.array(feature_matrix), frequencies


def create_tsne_visualization(
    feature_matrix: np.ndarray,
    frequencies: List[int],
    perplexity: int = 30,
    random_state: int = 42,
) -> Tuple[plt.Figure, np.ndarray]:
    """Create t-SNE visualization of feature space.

    Applies t-SNE dimensionality reduction to project 12-dimensional feature vectors
    into 2D space, then creates a scatter plot visualization.

    Args:
        feature_matrix: Binary feature matrix (n_syllables x 12)
        frequencies: Frequency count for each syllable
        perplexity: t-SNE perplexity parameter (balance between local/global structure).
                   Typical range: 5-50. Higher values consider more neighbors.
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (figure, tsne_coordinates):
            - figure: matplotlib Figure object
            - tsne_coordinates: numpy array of shape (n_syllables, 2) with 2D projections

    Notes:
        - Uses Hamming distance metric (optimal for binary features)
        - Perplexity default of 30 works well for most corpus sizes (100-10,000 syllables)
        - Fixed random_state ensures reproducible visualizations
        - Processing time scales roughly O(n^2) with corpus size
    """
    try:
        from sklearn.manifold import TSNE  # type: ignore[import-not-found]
    except ImportError as e:
        raise ImportError(
            "scikit-learn is required for t-SNE visualization. "
            "Install with: pip install scikit-learn"
        ) from e

    # Apply t-SNE with Hamming distance (optimal for binary features)
    tsne = TSNE(
        n_components=2,
        perplexity=perplexity,
        random_state=random_state,
        metric="hamming",
    )
    tsne_coords = tsne.fit_transform(feature_matrix)

    # Create visualization
    fig, ax = plt.subplots(figsize=(14, 10))

    # Convert frequencies to numpy array for scaling
    freq_array = np.array(frequencies)

    # Create scatter plot
    # - Position: t-SNE coordinates
    # - Size: frequency * 2 (larger points for common syllables)
    # - Color: frequency (viridis colormap)
    # - Alpha: 0.6 for slight transparency to show overlapping points
    scatter = ax.scatter(
        tsne_coords[:, 0],
        tsne_coords[:, 1],
        c=freq_array,
        s=freq_array * 2,  # Size proportional to frequency
        cmap="viridis",
        alpha=0.6,
        edgecolors="black",
        linewidth=0.5,
    )

    # Configure plot appearance
    ax.set_title(
        "t-SNE: Feature Signature Space\n(Size and color = frequency)",
        fontsize=16,
        fontweight="bold",
    )
    ax.set_xlabel("t-SNE Dimension 1", fontsize=12)
    ax.set_ylabel("t-SNE Dimension 2", fontsize=12)

    # Add colorbar
    plt.colorbar(scatter, ax=ax, label="Frequency Count")

    plt.tight_layout()

    return fig, tsne_coords


def create_interactive_visualization(
    records: List[Dict],
    tsne_coords: np.ndarray,
) -> "go.Figure":
    """Create interactive Plotly visualization of t-SNE feature space.

    This function generates an interactive HTML-compatible visualization with:
    - Hover tooltips showing syllable text, frequency, and active features
    - Interactive zoom, pan, and export controls
    - Frequency-based point sizing and coloring
    - High-quality rendering suitable for exploration

    Args:
        records: List of annotated syllable records from load_annotated_data().
                Each record must contain:
                - syllable (str): The syllable text
                - frequency (int): Occurrence count
                - features (dict): Boolean feature flags (12 features)
        tsne_coords: t-SNE 2D coordinates with shape (n_syllables, 2)

    Returns:
        Plotly Figure object with configured interactive scatter plot

    Raises:
        ImportError: If Plotly is not installed

    Example:
        >>> records = load_annotated_data(Path("syllables_annotated.json"))
        >>> feature_matrix, frequencies = extract_feature_matrix(records)
        >>> fig, tsne_coords = create_tsne_visualization(feature_matrix, frequencies)
        >>> interactive_fig = create_interactive_visualization(records, tsne_coords)
        >>> interactive_fig.show()  # Display in browser

    Notes:
        - Point size uses log1p scale for better visibility across frequency ranges
        - Viridis colormap provides perceptually uniform coloring
        - Hover text limited to 4 features for readability (shows +N more if applicable)
        - Plotly CDN used for smaller file size when saving HTML
    """
    if not _PLOTLY_AVAILABLE:
        raise ImportError(
            "Plotly is required for interactive visualization. " "Install with: pip install plotly"
        )

    # Extract data for visualization
    syllables = [r["syllable"] for r in records]
    frequencies = np.array([r["frequency"] for r in records])

    # Build rich hover text with syllable details
    hover_texts = []
    for record in records:
        active_features = [feat for feat, val in record["features"].items() if val]
        hover_text = (
            f"<b>{record['syllable']}</b><br>"
            f"Frequency: {record['frequency']:,}<br>"
            f"Features: {len(active_features)}/12<br>"
            f"<i>{', '.join(active_features[:4])}</i>"
        )
        if len(active_features) > 4:
            hover_text += f"<br><i>... +{len(active_features)-4} more</i>"
        hover_texts.append(hover_text)

    # Create figure with main scatter trace
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=tsne_coords[:, 0],
            y=tsne_coords[:, 1],
            mode="markers",
            marker=dict(
                size=np.log1p(frequencies) * 3,  # Log scale for better visibility
                color=frequencies,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Frequency"),
                line=dict(width=0.5, color="black"),
                opacity=0.7,
            ),
            text=syllables,
            hovertext=hover_texts,
            hoverinfo="text",
            customdata=[[i] for i in range(len(records))],  # Store index for future callbacks
            name="Syllables",
        )
    )

    # Configure layout for optimal viewing
    fig.update_layout(
        title={
            "text": "t-SNE: Feature Signature Space (Interactive)",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 20, "family": "Arial, sans-serif"},
        },
        xaxis_title="t-SNE Dimension 1",
        yaxis_title="t-SNE Dimension 2",
        hovermode="closest",
        width=1200,
        height=900,
        template="plotly_white",
        showlegend=True,
    )

    return fig


def save_visualization(
    fig: plt.Figure,
    output_dir: Path,
    dpi: int = 300,
    perplexity: int = 30,
    random_state: int = 42,
) -> Tuple[Path, Path]:
    """Save t-SNE visualization to file with metadata.

    Args:
        fig: matplotlib Figure object to save
        output_dir: Directory to save visualization in
        dpi: Resolution in dots per inch (default: 300 for publication quality)
        perplexity: t-SNE perplexity parameter used for generation (for metadata)
        random_state: Random seed used for generation (for metadata)

    Returns:
        Tuple of (visualization_path, metadata_path):
            - visualization_path: Path to saved PNG file
            - metadata_path: Path to saved metadata text file
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    viz_path = output_dir / f"{timestamp}.tsne_visualization.png"
    meta_path = output_dir / f"{timestamp}.tsne_metadata.txt"

    # Save figure
    fig.savefig(str(viz_path), dpi=dpi, bbox_inches="tight")

    # Save metadata
    metadata = [
        "t-SNE VISUALIZATION METADATA",
        "=" * 60,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Output file: {viz_path.name}",
        f"Resolution: {dpi} DPI",
        "",
        "ALGORITHM PARAMETERS",
        "-" * 60,
        "Method: t-SNE (t-distributed Stochastic Neighbor Embedding)",
        f"Perplexity: {perplexity}",
        f"Random state: {random_state}",
        "Distance metric: Hamming (optimal for binary features)",
        "Dimensions: 2D projection of 12-dimensional binary feature space",
        "Features: 12 phonetic features (onset, internal, nucleus, coda)",
        "",
        "VISUALIZATION ENCODING",
        "-" * 60,
        "X-axis: t-SNE Dimension 1",
        "Y-axis: t-SNE Dimension 2",
        "Point size: Proportional to syllable frequency",
        "Point color: Syllable frequency (viridis colormap)",
        "Edge color: Black outline for visibility",
        "",
        "INTERPRETATION GUIDE",
        "-" * 60,
        "- Nearby points: Similar phonetic feature patterns",
        "- Clusters: Natural groupings in feature space",
        "- Large/bright points: High-frequency syllables",
        "- Small/dark points: Low-frequency syllables",
        "- Isolated points: Unique or rare feature combinations",
        "",
        "=" * 60,
    ]

    meta_path.write_text("\n".join(metadata), encoding="utf-8")

    return viz_path, meta_path


def save_interactive_visualization(
    fig: "go.Figure",
    output_dir: Path,
    perplexity: int = 30,
    random_state: int = 42,
) -> Path:
    """Save interactive Plotly visualization as standalone HTML file.

    Creates a self-contained HTML file with embedded Plotly visualization that can be:
    - Opened directly in any web browser
    - Shared with collaborators
    - Embedded in reports or documentation
    - Explored with zoom, pan, hover, and export controls

    The HTML file uses Plotly CDN for JavaScript dependencies, resulting in smaller
    file sizes while maintaining full functionality.

    Args:
        fig: Plotly Figure object from create_interactive_visualization()
        output_dir: Directory to save HTML file in (created if doesn't exist)
        perplexity: t-SNE perplexity parameter used for generation (for metadata footer)
        random_state: Random seed used for generation (for metadata footer)

    Returns:
        Path to saved HTML file with timestamped filename

    Raises:
        ImportError: If Plotly is not installed

    Example:
        >>> records = load_annotated_data(Path("syllables_annotated.json"))
        >>> feature_matrix, frequencies = extract_feature_matrix(records)
        >>> fig_static, tsne_coords = create_tsne_visualization(feature_matrix, frequencies)
        >>> fig_interactive = create_interactive_visualization(records, tsne_coords)
        >>> html_path = save_interactive_visualization(fig_interactive, Path("_working/analysis/tsne/"))
        >>> print(f"Saved to: {html_path}")

    Notes:
        - Output filename format: YYYYMMDD_HHMMSS.tsne_interactive.html
        - File includes metadata footer with algorithm parameters
        - Plotly mode bar configured with additional tools (hoverclosest, hovercompare)
        - Export to PNG button configured for high-resolution output (1600x1200, 2x scale)
        - HTML is self-contained except for Plotly CDN dependency
    """
    if not _PLOTLY_AVAILABLE:
        raise ImportError("Plotly is required for interactive visualization.")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename matching existing convention
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = output_dir / f"{timestamp}.tsne_interactive.html"

    # Save as standalone HTML with configuration
    fig.write_html(
        str(html_path),
        include_plotlyjs="cdn",  # Use CDN for smaller file size
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToAdd": ["hoverclosest", "hovercompare"],
            "toImageButtonOptions": {
                "format": "png",
                "filename": f"tsne_interactive_{timestamp}",
                "height": 1200,
                "width": 1600,
                "scale": 2,
            },
        },
    )

    # Append metadata footer to HTML
    metadata_html = f"""
<!-- t-SNE Visualization Metadata -->
<div style="margin: 20px; padding: 15px; background-color: #f5f5f5;
            border-radius: 8px; font-family: 'Courier New', monospace; font-size: 13px;
            border: 1px solid #ddd;">
    <div style="font-weight: bold; font-size: 14px; margin-bottom: 10px; color: #333;">
        t-SNE Visualization Parameters
    </div>
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 4px; color: #666;">Algorithm:</td>
            <td style="padding: 4px; color: #000;">t-SNE (t-distributed Stochastic Neighbor Embedding)</td>
        </tr>
        <tr>
            <td style="padding: 4px; color: #666;">Perplexity:</td>
            <td style="padding: 4px; color: #000;">{perplexity}</td>
        </tr>
        <tr>
            <td style="padding: 4px; color: #666;">Random State:</td>
            <td style="padding: 4px; color: #000;">{random_state}</td>
        </tr>
        <tr>
            <td style="padding: 4px; color: #666;">Distance Metric:</td>
            <td style="padding: 4px; color: #000;">Hamming (optimal for binary features)</td>
        </tr>
        <tr>
            <td style="padding: 4px; color: #666;">Generated:</td>
            <td style="padding: 4px; color: #000;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
        </tr>
    </table>
    <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 11px; color: #777;">
        <b>Usage:</b> Hover over points to see syllable details. Use toolbar for zoom, pan, and export.
    </div>
</div>
"""

    # Append metadata to HTML file
    with open(html_path, "a", encoding="utf-8") as f:
        f.write(metadata_html)

    return html_path


def _save_tsne_mapping(
    records: List[Dict],
    tsne_coords: np.ndarray,
    output_dir: Path,
    timestamp: str,
) -> Path:
    """Save syllable→features→coordinates mapping as JSON.

    This creates a self-contained mapping file that links:
    - Syllable text
    - Frequency count
    - 2D t-SNE coordinates
    - Complete feature dictionary

    Useful for:
    - Post-hoc cluster analysis
    - Cross-referencing visualizations
    - Interactive exploration (future feature)
    - Sharing visualizations with collaborators

    Args:
        records: List of annotated syllable records from input
        tsne_coords: numpy array of t-SNE 2D coordinates (shape: n_syllables × 2)
        output_dir: Directory to save mapping file in
        timestamp: Timestamp string for filename (format: YYYYMMDD_HHMMSS)

    Returns:
        Path to saved mapping JSON file

    Example output structure:
        [
            {
                "syllable": "kran",
                "frequency": 7,
                "tsne_x": -2.34,
                "tsne_y": 5.67,
                "features": {
                    "contains_liquid": true,
                    "contains_plosive": true,
                    ...
                }
            },
            ...
        ]

    Notes:
        - Coordinates are converted from numpy to native Python floats for JSON serialization
        - Array indices preserve order from input file
        - All 12 features are included in each record
        - File is formatted with indent=2 for human readability
    """
    mapping_path = output_dir / f"{timestamp}.tsne_mapping.json"

    # Build mapping: combine records with their t-SNE coordinates
    mapping = [
        {
            "syllable": records[i]["syllable"],
            "frequency": records[i]["frequency"],
            "tsne_x": float(tsne_coords[i, 0]),  # Convert numpy float to Python float
            "tsne_y": float(tsne_coords[i, 1]),  # Convert numpy float to Python float
            "features": records[i]["features"],
        }
        for i in range(len(records))
    ]

    # Save as formatted JSON
    mapping_path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")

    return mapping_path


def run_tsne_visualization(
    input_path: Path,
    output_dir: Path,
    perplexity: int = 30,
    random_state: int = 42,
    dpi: int = 300,
    verbose: bool = False,
    save_mapping: bool = False,
    interactive: bool = False,
) -> Dict:
    """Run the complete t-SNE visualization pipeline.

    This is the main entry point for programmatic use. It handles the full workflow:
    1. Load annotated syllables
    2. Extract feature matrix
    3. Apply t-SNE dimensionality reduction
    4. Create visualization
    5. Save outputs (PNG + optional HTML + optional mapping)

    Args:
        input_path: Path to syllables_annotated.json
        output_dir: Directory to save visualization outputs
        perplexity: t-SNE perplexity parameter (default: 30)
        random_state: Random seed for reproducibility (default: 42)
        dpi: Output resolution in dots per inch (default: 300)
        verbose: Print detailed progress information
        save_mapping: Save syllable→features→coordinates mapping as JSON (default: False)
        interactive: Generate interactive HTML visualization (requires Plotly, default: False)

    Returns:
        Dictionary containing:
            - syllable_count: Number of syllables visualized
            - feature_count: Number of features (always 12)
            - output_path: Path to saved visualization PNG
            - metadata_path: Path to saved metadata file
            - tsne_coordinates: numpy array of 2D coordinates
            - mapping_path: Path to mapping JSON (None if save_mapping=False)
            - interactive_path: Path to interactive HTML (None if interactive=False or Plotly unavailable)

    Raises:
        FileNotFoundError: If input file does not exist
        ImportError: If required dependencies are missing
        ValueError: If input data is invalid

    Example:
        >>> from pathlib import Path
        >>> result = run_tsne_visualization(
        ...     input_path=Path("data/annotated/syllables_annotated.json"),
        ...     output_dir=Path("_working/analysis/tsne/"),
        ...     interactive=True,
        ...     save_mapping=True
        ... )
        >>> print(f"Visualized {result['syllable_count']} syllables")
        >>> print(f"Interactive HTML: {result['interactive_path']}")
    """
    if verbose:
        print(f"Loading data from: {input_path}")

    # Load annotated syllables
    records = load_annotated_data(input_path)

    if verbose:
        print(f"Loaded {len(records):,} annotated syllables")
        print("Extracting feature matrix...")

    # Extract feature matrix and frequencies
    feature_matrix, frequencies = extract_feature_matrix(records)

    if verbose:
        print(f"Feature matrix shape: {feature_matrix.shape}")
        print("Running t-SNE (this may take a minute)...")

    # Create t-SNE visualization
    fig, tsne_coords = create_tsne_visualization(
        feature_matrix, frequencies, perplexity, random_state
    )

    if verbose:
        print("Saving visualization...")

    # Save outputs
    viz_path, meta_path = save_visualization(fig, output_dir, dpi, perplexity, random_state)

    # Conditionally save mapping file
    mapping_path = None
    if save_mapping:
        timestamp = viz_path.stem.split(".")[0]  # Extract timestamp from viz filename
        mapping_path = _save_tsne_mapping(records, tsne_coords, output_dir, timestamp)
        if verbose:
            print(f"✓ Mapping saved to: {mapping_path}")

    # Conditionally save interactive HTML visualization
    interactive_path = None
    if interactive:
        if not _PLOTLY_AVAILABLE:
            print("Warning: Plotly not available. Skipping interactive visualization.")
            print("Install with: pip install plotly")
        else:
            if verbose:
                print("Creating interactive visualization...")
            interactive_fig = create_interactive_visualization(records, tsne_coords)
            interactive_path = save_interactive_visualization(
                interactive_fig, output_dir, perplexity, random_state
            )
            if verbose:
                print(f"✓ Interactive HTML saved to: {interactive_path}")

    # Clean up matplotlib figure
    plt.close(fig)

    return {
        "syllable_count": len(records),
        "feature_count": len(ALL_FEATURES),
        "output_path": viz_path,
        "metadata_path": meta_path,
        "tsne_coordinates": tsne_coords,
        "mapping_path": mapping_path,
        "interactive_path": interactive_path,
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace with validated parameters
    """
    parser = argparse.ArgumentParser(
        description="Generate t-SNE visualization of feature signature space",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate visualization with default settings
  python -m build_tools.syllable_feature_annotator.analysis.tsne_visualizer

  # Custom input/output paths
  python -m build_tools.syllable_feature_annotator.analysis.tsne_visualizer \\
    --input data/annotated/syllables_annotated.json \\
    --output _working/analysis/tsne/

  # Adjust t-SNE parameters
  python -m build_tools.syllable_feature_annotator.analysis.tsne_visualizer \\
    --perplexity 50 \\
    --random-state 123

  # High-resolution output
  python -m build_tools.syllable_feature_annotator.analysis.tsne_visualizer \\
    --dpi 600

  # Verbose output
  python -m build_tools.syllable_feature_annotator.analysis.tsne_visualizer --verbose
        """,
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to syllables_annotated.json (default: {DEFAULT_INPUT})",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for visualizations (default: {DEFAULT_OUTPUT_DIR})",
    )

    parser.add_argument(
        "--perplexity",
        type=int,
        default=30,
        help="t-SNE perplexity parameter (default: 30, range: 5-50)",
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Output resolution in DPI (default: 300)",
    )

    parser.add_argument(
        "--save-mapping",
        action="store_true",
        help="Save syllable→features→coordinates mapping as JSON (default: False)",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Generate interactive HTML visualization in addition to static PNG (requires Plotly)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress information",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the t-SNE visualization tool."""
    args = parse_args()

    # Validate input file exists
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        print("Have you run the syllable feature annotator yet?")
        print("Expected path: data/annotated/syllables_annotated.json")
        return

    # Validate perplexity range
    if not 5 <= args.perplexity <= 50:
        print(f"Warning: Perplexity {args.perplexity} is outside typical range (5-50)")
        print("This may produce suboptimal results.")

    # Add helpful note if --interactive used without --save-mapping
    if args.interactive and not args.save_mapping:
        print("Note: Interactive visualization works best with --save-mapping enabled")
        print("      to enable coordinate reuse and feature exploration.\n")

    if not args.verbose:
        print(f"Generating t-SNE visualization from: {args.input}")
        print(f"Output directory: {args.output}")
        print()

    try:
        # Run visualization
        result = run_tsne_visualization(
            input_path=args.input,
            output_dir=args.output,
            perplexity=args.perplexity,
            random_state=args.random_state,
            dpi=args.dpi,
            verbose=args.verbose,
            save_mapping=args.save_mapping,
            interactive=args.interactive,
        )

        # Display summary
        print(f"✓ Visualized {result['syllable_count']:,} syllables")
        print(f"✓ Projected {result['feature_count']} features into 2D space")
        print(f"✓ Visualization saved to: {result['output_path']}")
        print(f"✓ Metadata saved to: {result['metadata_path']}")
        if result["mapping_path"]:
            print(f"✓ Mapping saved to: {result['mapping_path']}")
        if result["interactive_path"]:
            print(f"✓ Interactive HTML saved to: {result['interactive_path']}")

    except ImportError as e:
        print(f"Error: {e}")
        print("\nRequired dependencies:")
        print("  pip install scikit-learn matplotlib numpy pandas")
        return

    except Exception as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":
    main()
