"""
Data models for syllable extraction results.

This module defines the data structures used to represent extraction results
and their associated metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class ExtractionResult:
    """
    Container for syllable extraction results and associated metadata.

    This dataclass stores both the extracted syllables and all relevant
    metadata about the extraction process for reporting and persistence.

    Attributes:
        syllables: Set of unique syllables extracted from the input text
        language_code: Pyphen language/locale code used for hyphenation
        min_syllable_length: Minimum syllable length constraint
        max_syllable_length: Maximum syllable length constraint
        input_path: Path to the input text file
        timestamp: When the extraction was performed
        only_hyphenated: Whether whole words were excluded
        length_distribution: Map of syllable length to count
        sample_syllables: Representative sample of extracted syllables
        total_words: Total words found in source text
        skipped_unhyphenated: Words skipped because they couldn't be hyphenated
        rejected_syllables: Syllables rejected due to length constraints
        processed_words: Words that were successfully processed
    """

    syllables: Set[str]
    language_code: str
    min_syllable_length: int
    max_syllable_length: int
    input_path: Path
    timestamp: datetime = field(default_factory=datetime.now)
    only_hyphenated: bool = True
    length_distribution: Dict[int, int] = field(default_factory=dict)
    sample_syllables: List[str] = field(default_factory=list)
    total_words: int = 0
    skipped_unhyphenated: int = 0
    rejected_syllables: int = 0
    processed_words: int = 0

    def __post_init__(self):
        """Calculate derived fields after initialization."""
        # Calculate length distribution
        for syllable in self.syllables:
            length = len(syllable)
            self.length_distribution[length] = self.length_distribution.get(length, 0) + 1

        # Generate sample syllables (first 15, sorted)
        sample_size = min(15, len(self.syllables))
        self.sample_syllables = sorted(self.syllables)[:sample_size]

    def format_metadata(self) -> str:
        """
        Format extraction metadata as a human-readable string.

        Returns:
            Multi-line string containing all extraction metadata formatted
            for display or file output.
        """
        lines = []
        lines.append("=" * 70)
        lines.append("SYLLABLE EXTRACTION METADATA")
        lines.append("=" * 70)
        lines.append(f"Extraction Date:    {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Language Code:      {self.language_code}")
        lines.append(
            f"Syllable Length:    {self.min_syllable_length}-{self.max_syllable_length} characters"
        )
        lines.append(f"Input File:         {self.input_path}")
        lines.append(f"Unique Syllables:   {len(self.syllables)}")
        lines.append(f"Only Hyphenated:    {'Yes' if self.only_hyphenated else 'No'}")
        lines.append("=" * 70)
        
        # Processing statistics
        lines.append("\nProcessing Statistics:")
        lines.append(f"  Total Words:        {self.total_words:,}")
        lines.append(f"  Processed Words:    {self.processed_words:,}")
        lines.append(f"  Skipped (unhyph):   {self.skipped_unhyphenated:,}")
        lines.append(f"  Rejected Syllables: {self.rejected_syllables:,}")
        if self.total_words > 0:
            processed_pct = (self.processed_words / self.total_words) * 100
            skipped_pct = (self.skipped_unhyphenated / self.total_words) * 100
            lines.append(f"  Process Rate:       {processed_pct:.1f}%")
            lines.append(f"  Skip Rate:          {skipped_pct:.1f}%")

        # Length distribution
        if self.length_distribution:
            lines.append("\nSyllable Length Distribution:")
            for length in sorted(self.length_distribution.keys()):
                count = self.length_distribution[length]
                bar = "█" * min(40, count)
                lines.append(f"  {length:2d} chars: {count:4d} {bar}")

        # Sample syllables
        if self.sample_syllables:
            lines.append(f"\nSample Syllables (first {len(self.sample_syllables)}):")
            for syllable in self.sample_syllables:
                lines.append(f"  - {syllable}")
            if len(self.syllables) > len(self.sample_syllables):
                lines.append(f"  ... and {len(self.syllables) - len(self.sample_syllables)} more")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)
