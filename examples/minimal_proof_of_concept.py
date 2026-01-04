"""Minimal proof of concept - the simplest possible working example.

This file defines what we WANT the API to look like.
If this code runs successfully, we've succeeded.
"""

from pipeworks_name_generation import NameGenerator


def test_basic_generation():
    """Test basic name generation."""
    print("Testing pipeworks_name_generation proof of concept...")
    print()

    # Goal: Generate a name deterministically
    gen = NameGenerator(pattern="simple")

    # Generate names
    name1 = gen.generate(seed=42)
    name2 = gen.generate(seed=42)
    name3 = gen.generate(seed=99)

    print(f"Name with seed=42: {name1}")
    print(f"Same seed again:   {name2}")
    print(f"Different seed:    {name3}")
    print()

    # Verify determinism (critical requirement!)
    assert name1 == name2, "Determinism broken!"
    print("✓ Determinism verified: same seed = same name")

    # Verify different seeds produce different results
    assert name1 != name3, "Different seeds should produce different names"
    print("✓ Randomness verified: different seeds = different names")


def test_batch_generation():
    """Test batch name generation."""
    print()
    print("Testing batch generation...")

    gen = NameGenerator(pattern="simple")
    names = gen.generate_batch(count=10, base_seed=1000, unique=True)

    print(f"Generated {len(names)} names:")
    for i, name in enumerate(names, 1):
        print(f"  {i:2}. {name}")

    print("✓ Batch generation works!")
    print(f"✓ All unique: {len(names) == len(set(names))}")


def main():
    """Run all proof of concept tests."""
    test_basic_generation()
    test_batch_generation()

    print()
    print("=" * 50)
    print("SUCCESS! Proof of concept works.")
    print("=" * 50)


if __name__ == "__main__":
    main()
