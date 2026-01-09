"""
Command-line interface for syllable normalization pipeline.

This module provides the main CLI entry point for the syllable_normaliser tool,
which transforms raw syllable files through a 3-step pipeline: aggregation,
canonicalization, and frequency analysis.
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

from .aggregator import FileAggregator, discover_input_files
from .frequency import FrequencyAnalyzer
from .models import NormalizationConfig, NormalizationResult, NormalizationStats
from .normalizer import normalize_batch


def run_full_pipeline(
    input_files: List[Path], output_dir: Path, config: NormalizationConfig, verbose: bool = False
) -> NormalizationResult:
    """
    Run complete 3-step normalization pipeline.

    Executes the full normalization workflow:
    1. Aggregate all input files → syllables_raw.txt
    2. Canonicalize syllables → syllables_canonicalised.txt
    3. Frequency analysis → syllables_frequencies.json, syllables_unique.txt,
       normalization_meta.txt

    Args:
        input_files: List of input .txt files to process.
        output_dir: Directory where output files will be saved.
        config: NormalizationConfig specifying normalization parameters.
        verbose: If True, print detailed progress information.

    Returns:
        NormalizationResult containing all outputs, statistics, and file paths.

    Example:
        >>> from pathlib import Path
        >>> config = NormalizationConfig()
        >>> files = [Path("corpus1.txt"), Path("corpus2.txt")]
        >>> result = run_full_pipeline(
        ...     input_files=files,
        ...     output_dir=Path("_working/normalized"),
        ...     config=config,
        ...     verbose=True
        ... )
        >>> result.stats.raw_count
        1523
        >>> result.stats.unique_canonical
        412
    """
    start_time = time.time()
    timestamp = datetime.now()

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define output file paths
    raw_file = output_dir / "syllables_raw.txt"
    canonical_file = output_dir / "syllables_canonicalised.txt"
    frequency_file = output_dir / "syllables_frequencies.json"
    unique_file = output_dir / "syllables_unique.txt"
    meta_file = output_dir / "normalization_meta.txt"

    print("\n" + "=" * 70)
    print("SYLLABLE NORMALIZATION PIPELINE")
    print("=" * 70)
    print(f"Input Files:         {len(input_files)} files")
    print(f"Output Directory:    {output_dir}")
    print(f"Timestamp:           {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Step 1: Aggregate files
    print("\n⏳ Step 1: Aggregating input files...")
    aggregator = FileAggregator()
    raw_syllables = aggregator.aggregate_files(input_files)
    aggregator.save_raw_syllables(raw_syllables, raw_file)

    raw_count = len(raw_syllables)
    print(f"✓ Aggregated {raw_count:,} syllables → {raw_file.name}")

    if verbose:
        print(f"  Sample: {raw_syllables[:5]}")

    # Step 2: Canonicalization
    print("\n⏳ Step 2: Canonicalizing syllables...")
    canonical_syllables, rejection_stats = normalize_batch(raw_syllables, config)

    # Save canonicalized syllables
    with canonical_file.open("w", encoding="utf-8") as f:
        for syllable in canonical_syllables:
            f.write(f"{syllable}\n")

    after_canonicalization = len(canonical_syllables)
    print(f"✓ Canonicalized {after_canonicalization:,} syllables → {canonical_file.name}")

    rejected_total = (
        rejection_stats["rejected_empty"]
        + rejection_stats["rejected_charset"]
        + rejection_stats["rejected_length"]
    )
    print(f"  Rejected: {rejected_total:,} syllables")

    if verbose:
        print(f"    Empty: {rejection_stats['rejected_empty']:,}")
        print(f"    Invalid charset: {rejection_stats['rejected_charset']:,}")
        print(f"    Length constraint: {rejection_stats['rejected_length']:,}")
        print(f"  Sample canonical: {canonical_syllables[:5]}")

    # Step 3: Frequency analysis
    print("\n⏳ Step 3: Analyzing frequencies...")
    analyzer = FrequencyAnalyzer()

    # Calculate frequencies
    frequencies = analyzer.calculate_frequencies(canonical_syllables)
    analyzer.save_frequencies(frequencies, frequency_file)
    print(f"✓ Saved frequency data → {frequency_file.name}")

    # Extract unique syllables
    unique_syllables = analyzer.extract_unique_syllables(canonical_syllables)
    analyzer.save_unique_syllables(unique_syllables, unique_file)
    unique_count = len(unique_syllables)
    print(f"✓ Extracted {unique_count:,} unique syllables → {unique_file.name}")

    if verbose:
        # Show top 5 most frequent
        entries = analyzer.create_frequency_entries(frequencies)
        print("\n  Top 5 most frequent:")
        for entry in entries[:5]:
            print(
                f"    {entry.canonical:10s} ({entry.frequency:5,} occurrences, {entry.percentage:5.1f}%)"
            )

    # Create statistics object
    stats = NormalizationStats(
        raw_count=raw_count,
        after_canonicalization=after_canonicalization,
        rejected_charset=rejection_stats["rejected_charset"],
        rejected_length=rejection_stats["rejected_length"],
        rejected_empty=rejection_stats["rejected_empty"],
        unique_canonical=unique_count,
        processing_time=time.time() - start_time,
    )

    # Create result object
    result = NormalizationResult(
        config=config,
        stats=stats,
        frequencies=frequencies,
        unique_syllables=unique_syllables,
        input_files=input_files,
        output_dir=output_dir,
        timestamp=timestamp,
        raw_file=raw_file,
        canonical_file=canonical_file,
        frequency_file=frequency_file,
        unique_file=unique_file,
        meta_file=meta_file,
    )

    # Save metadata report
    print("\n⏳ Generating metadata report...")
    metadata_content = result.format_metadata()
    with meta_file.open("w", encoding="utf-8") as f:
        f.write(metadata_content)
    print(f"✓ Saved metadata report → {meta_file.name}")

    # Print summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"Total Time:          {stats.processing_time:.2f}s")
    print(f"Raw Syllables:       {stats.raw_count:,}")
    print(f"Canonical:           {stats.after_canonicalization:,}")
    print(f"Unique Canonical:    {stats.unique_canonical:,}")
    print(f"Rejection Rate:      {stats.rejection_rate:.1f}%")
    print("=" * 70)
    print(f"\nAll output files saved to: {output_dir}")
    print()

    return result


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.

    Returns:
        Configured ArgumentParser for the syllable_normaliser CLI.
    """
    parser = argparse.ArgumentParser(
        prog="syllable_normaliser",
        description=(
            "Normalize syllables through a 3-step pipeline: "
            "aggregation → canonicalization → frequency analysis"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples
========

.. code-block:: bash

   # Process all .txt files in a directory
   python -m build_tools.syllable_normaliser --source data/corpus/ --output _working/normalized/

   # Recursive directory scan
   python -m build_tools.syllable_normaliser --source data/ --recursive --output results/

   # Custom syllable length constraints
   python -m build_tools.syllable_normaliser --source data/ --min 3 --max 10

   # Verbose output with detailed statistics
   python -m build_tools.syllable_normaliser --source data/ --verbose

Output Files
============

- **syllables_raw.txt**: Aggregated raw syllables (all occurrences)
- **syllables_canonicalised.txt**: Normalized canonical syllables
- **syllables_frequencies.json**: Frequency intelligence (syllable → count)
- **syllables_unique.txt**: Deduplicated canonical syllable inventory
- **normalization_meta.txt**: Detailed statistics and metadata report
        """,
    )

    # Input options
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Source directory containing input .txt files",
    )

    parser.add_argument(
        "--pattern",
        type=str,
        default="*.txt",
        help="File pattern for discovery (default: *.txt)",
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan source directory recursively",
    )

    # Output options
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("_working/normalized"),
        help="Output directory for generated files (default: _working/normalized)",
    )

    # Normalization parameters
    parser.add_argument(
        "--min",
        type=int,
        default=2,
        dest="min_length",
        help="Minimum syllable length in characters (default: 2)",
    )

    parser.add_argument(
        "--max",
        type=int,
        default=20,
        dest="max_length",
        help="Maximum syllable length in characters (default: 20)",
    )

    parser.add_argument(
        "--charset",
        type=str,
        default="abcdefghijklmnopqrstuvwxyz",
        help="Allowed character set (default: abcdefghijklmnopqrstuvwxyz)",
    )

    parser.add_argument(
        "--unicode-form",
        type=str,
        default="NFKD",
        choices=["NFC", "NFD", "NFKC", "NFKD"],
        help="Unicode normalization form (default: NFKD)",
    )

    # Display options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed processing information",
    )

    return parser


def main() -> int:
    """
    Main entry point for syllable_normaliser CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        # Validate source directory
        if not args.source.exists():
            print(f"❌ Error: Source directory does not exist: {args.source}", file=sys.stderr)
            return 1

        if not args.source.is_dir():
            print(f"❌ Error: Source path is not a directory: {args.source}", file=sys.stderr)
            return 1

        # Discover input files
        print(f"\n⏳ Discovering input files in {args.source}...")
        print(f"   Pattern: {args.pattern}")
        print(f"   Recursive: {args.recursive}")

        input_files = discover_input_files(
            source_dir=args.source,
            pattern=args.pattern,
            recursive=args.recursive,
        )

        if not input_files:
            print(f"❌ Error: No files found matching pattern '{args.pattern}'", file=sys.stderr)
            return 1

        print(f"✓ Found {len(input_files)} input files")

        if args.verbose:
            print("\nInput files:")
            for i, file_path in enumerate(input_files, 1):
                print(f"  {i:3d}. {file_path}")

        # Create normalization config
        config = NormalizationConfig(
            min_length=args.min_length,
            max_length=args.max_length,
            allowed_charset=args.charset,
            unicode_form=args.unicode_form,
        )

        # Run pipeline
        run_full_pipeline(
            input_files=input_files,
            output_dir=args.output,
            config=config,
            verbose=args.verbose,
        )

        return 0

    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
