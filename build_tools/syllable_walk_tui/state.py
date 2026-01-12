"""
State management for Syllable Walker TUI.

This module provides dataclasses for managing application state,
including patch configurations and isolated RNG instances.
"""

import random
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PatchState:
    """
    State for a single patch configuration.

    Maintains isolated RNG instance to avoid global random state contamination.

    Attributes:
        name: Identifier for this patch (e.g., "A" or "B")
        seed: Random seed for reproducible generation
        rng: Isolated Random instance for this patch
        corpus_dir: Path to corpus directory (None if not selected)
        corpus_type: Detected corpus type ("NLTK" or "Pyphen", None if not selected)
        min_length: Minimum syllable length
        max_length: Maximum syllable length
        walk_length: Number of steps in random walk
        freq_bias: Frequency bias (0.0-1.0)
        neighbor_limit: Maximum neighbors to consider
        outputs: Generated names from last generation
    """

    name: str
    seed: int = field(default_factory=lambda: random.SystemRandom().randint(0, 2**32 - 1))
    corpus_dir: Path | None = None
    corpus_type: str | None = None
    min_length: int = 2
    max_length: int = 5
    walk_length: int = 5
    freq_bias: float = 0.5
    neighbor_limit: int = 10
    outputs: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize isolated RNG instance after dataclass initialization."""
        self.rng = random.Random(self.seed)  # nosec B311 - Not for cryptographic use

    def generate_seed(self) -> int:
        """
        Generate a new random seed using system entropy.

        Returns:
            New random seed value

        Note:
            Uses SystemRandom to avoid global random state contamination.
        """
        self.seed = random.SystemRandom().randint(0, 2**32 - 1)
        self.rng = random.Random(self.seed)  # nosec B311 - Not for cryptographic use
        return self.seed


@dataclass
class AppState:
    """
    Global application state.

    Attributes:
        patch_a: Configuration for patch A
        patch_b: Configuration for patch B
        current_focus: Currently focused panel ("patch_a", "patch_b", or "stats")
        last_browse_dir: Last directory browsed (for remembering location)
    """

    patch_a: PatchState = field(default_factory=lambda: PatchState(name="A"))
    patch_b: PatchState = field(default_factory=lambda: PatchState(name="B"))
    current_focus: str = "patch_a"
    last_browse_dir: Path | None = None
