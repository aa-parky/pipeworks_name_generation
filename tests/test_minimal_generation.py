"""Minimal test suite to drive initial implementation.

Start with the absolute simplest tests that validate core functionality.
"""

import pytest

from pipeworks_name_generation import NameGenerator


class TestBasicGeneration:
    """Basic name generation tests."""

    def test_generator_creates_deterministic_names(self):
        """Test that same seed produces same name (CRITICAL requirement)."""
        gen = NameGenerator(pattern="simple")

        name1 = gen.generate(seed=42)
        name2 = gen.generate(seed=42)

        assert name1 == name2, "Same seed must produce same name"
        assert isinstance(name1, str), "Name must be a string"
        assert len(name1) > 0, "Name must not be empty"

    def test_different_seeds_produce_different_names(self):
        """Test that different seeds produce different names."""
        gen = NameGenerator(pattern="simple")

        name1 = gen.generate(seed=1)
        name2 = gen.generate(seed=2)

        # Probabilistically, these should be different
        assert name1 != name2, "Different seeds should produce different names"

    def test_generator_accepts_pattern_name(self):
        """Test that generator accepts pattern parameter."""
        # Should not raise
        gen = NameGenerator(pattern="simple")
        assert gen is not None

    def test_generator_rejects_unknown_pattern(self):
        """Test that generator raises on unknown pattern."""
        with pytest.raises(ValueError, match="Unknown pattern"):
            NameGenerator(pattern="nonexistent")

    def test_generated_names_are_capitalized(self):
        """Test that generated names start with capital letter."""
        gen = NameGenerator(pattern="simple")
        name = gen.generate(seed=1)

        assert name[0].isupper(), "Name should start with capital letter"

    def test_optional_syllable_count(self):
        """Test that syllable count can be specified."""
        gen = NameGenerator(pattern="simple")

        # Should not raise
        short_name = gen.generate(seed=1, syllables=2)
        long_name = gen.generate(seed=2, syllables=3)

        assert isinstance(short_name, str)
        assert isinstance(long_name, str)


class TestBatchGeneration:
    """Test batch name generation."""

    def test_generate_batch_returns_list(self):
        """Test that generate_batch returns a list of names."""
        gen = NameGenerator(pattern="simple")
        names = gen.generate_batch(count=5, base_seed=100)

        assert isinstance(names, list)
        assert len(names) == 5
        assert all(isinstance(name, str) for name in names)

    def test_generate_batch_unique_names(self):
        """Test that batch generation produces unique names."""
        gen = NameGenerator(pattern="simple")
        names = gen.generate_batch(count=10, base_seed=100, unique=True)

        # All names should be different
        assert len(names) == len(set(names)), "Names should be unique"

    def test_generate_batch_deterministic(self):
        """Test that batch generation is deterministic."""
        gen = NameGenerator(pattern="simple")

        batch1 = gen.generate_batch(count=5, base_seed=42)
        batch2 = gen.generate_batch(count=5, base_seed=42)

        assert batch1 == batch2, "Same base_seed should produce same batch"
