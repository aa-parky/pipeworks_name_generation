User Guide
==========

This guide provides detailed information about using pipeworks_name_generation.

Design Philosophy
-----------------

The generator is built on these principles:

**Context-Free**
    Names have no inherent meaning, culture, or lore. They are purely structural
    and phonetic. Your application provides the context.

**Deterministic**
    Same seed = same name, always. This is critical for games where entity IDs
    must map to consistent names across sessions.

**Phonetically Plausible**
    Names use syllable combinations that are pronounceable and natural-sounding
    in many languages.

**Lightweight**
    Zero runtime dependencies. The generator is fast and minimal.

Patterns
--------

Currently in Phase 1 (proof of concept), only the ``"simple"`` pattern is available.

Simple Pattern
^^^^^^^^^^^^^^

The simple pattern uses hardcoded syllables that create pronounceable names:

.. code-block:: python

    gen = NameGenerator(pattern="simple")
    name = gen.generate(seed=42)  # "Kawyn"

Available syllables in the simple pattern include both soft and hard sounds:

* Soft: ka, la, thin, mar, in, del, so, ra, vyn, tha, len, is, el, an, dor, mir, eth, al
* Hard: grim, thor, ak, bor, din, wyn, krag, durn, mok, gor, thrak, zar

Future Patterns
^^^^^^^^^^^^^^^

In Phase 2+, additional patterns will be added:

* Loading from YAML pattern files
* Multiple pattern sets (fantasy, sci-fi, neutral, etc.)
* Custom user-defined patterns
* Phonotactic constraints

Deterministic Generation
-------------------------

Understanding Seeds
^^^^^^^^^^^^^^^^^^^

Seeds are integers that determine the randomness used in generation:

.. code-block:: python

    gen = NameGenerator(pattern="simple")

    # Same seed always produces same name
    assert gen.generate(seed=1) == gen.generate(seed=1)
    assert gen.generate(seed=2) == gen.generate(seed=2)

    # Different seeds produce different names
    assert gen.generate(seed=1) != gen.generate(seed=2)

This determinism is implemented using Python's ``random.Random(seed)`` to create
isolated random number generators, avoiding global state contamination.

Using Entity IDs as Seeds
^^^^^^^^^^^^^^^^^^^^^^^^^^

The most common pattern in games:

.. code-block:: python

    def get_npc_name(entity_id: int) -> str:
        """Get consistent name for an entity."""
        gen = NameGenerator(pattern="simple")
        return gen.generate(seed=entity_id)

    # Entity 12345 always gets the same name
    name1 = get_npc_name(12345)
    name2 = get_npc_name(12345)
    assert name1 == name2  # ✓ Always true

Batch Generation
----------------

Generating Multiple Names
^^^^^^^^^^^^^^^^^^^^^^^^^

Generate many names efficiently:

.. code-block:: python

    gen = NameGenerator(pattern="simple")

    # Generate 100 unique names
    names = gen.generate_batch(
        count=100,
        base_seed=1000,
        unique=True
    )

    assert len(names) == 100
    assert len(set(names)) == 100  # All unique

How Batch Generation Works
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``generate_batch`` method:

1. Starts with ``base_seed``
2. Generates a name using that seed
3. If ``unique=True`` and name already exists, increments seed and tries again
4. Continues until ``count`` names are generated

.. code-block:: python

    # These will be the same because deterministic
    batch1 = gen.generate_batch(count=5, base_seed=1000)
    batch2 = gen.generate_batch(count=5, base_seed=1000)
    assert batch1 == batch2

Uniqueness Constraints
^^^^^^^^^^^^^^^^^^^^^^

With ``unique=True``, the generator ensures no duplicates:

.. code-block:: python

    names = gen.generate_batch(count=50, base_seed=0, unique=True)
    assert len(names) == len(set(names))  # No duplicates

If unable to generate enough unique names (rare with large syllable pool),
raises ``ValueError``.

Syllable Control
----------------

Controlling Length
^^^^^^^^^^^^^^^^^^

Specify exact syllable counts:

.. code-block:: python

    gen = NameGenerator(pattern="simple")

    # Short names (2 syllables)
    short = gen.generate(seed=42, syllables=2)

    # Medium names (3 syllables)
    medium = gen.generate(seed=42, syllables=3)

    # Long names (4 syllables)
    long = gen.generate(seed=42, syllables=4)

Default Behavior
^^^^^^^^^^^^^^^^

If you don't specify syllables, the generator randomly chooses 2-3:

.. code-block:: python

    # Randomly chooses 2 or 3 syllables (deterministic to seed)
    name = gen.generate(seed=42)

Integration Examples
--------------------

Game NPC System
^^^^^^^^^^^^^^^

.. code-block:: python

    from pipeworks_name_generation import NameGenerator

    class NPCManager:
        def __init__(self):
            self.generator = NameGenerator(pattern="simple")

        def get_npc_name(self, entity_id: int) -> str:
            """Get consistent name for NPC entity."""
            return self.generator.generate(seed=entity_id)

        def populate_town(self, town_id: int, npc_count: int) -> list[str]:
            """Generate consistent names for all NPCs in a town."""
            # Use town_id as base_seed for reproducible town populations
            return self.generator.generate_batch(
                count=npc_count,
                base_seed=town_id * 10000,  # Offset to avoid collisions
                unique=True
            )

Procedural World Generation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pipeworks_name_generation import NameGenerator

    class WorldGenerator:
        def __init__(self, world_seed: int):
            self.world_seed = world_seed
            self.name_gen = NameGenerator(pattern="simple")

        def get_location_name(self, x: int, y: int) -> str:
            """Get deterministic name for location coordinates."""
            # Combine world seed with coordinates
            location_seed = hash((self.world_seed, x, y)) % (2**31)
            return self.name_gen.generate(seed=location_seed)

        def generate_region_names(self, region_id: int, count: int) -> list[str]:
            """Generate names for all locations in a region."""
            base_seed = self.world_seed + region_id
            return self.name_gen.generate_batch(
                count=count,
                base_seed=base_seed,
                unique=True
            )

Current Limitations (Phase 1)
------------------------------

The proof of concept has these intentional limitations:

* Only "simple" pattern available (hardcoded syllables)
* No pattern loading from files
* No phonotactic constraints
* No CLI interface
* Limited syllable pool (~30 syllables)

These will be addressed in future phases. See :doc:`development` for roadmap.

Best Practices
--------------

1. **Use entity IDs as seeds** for consistent naming across game sessions
2. **Cache generator instances** if generating many names (lightweight but still an object)
3. **Use batch generation** when populating areas with many entities
4. **Offset seeds** to avoid collisions between different systems (e.g., NPCs vs locations)
5. **Document your seed schemes** so you can recreate names later

Troubleshooting
---------------

Names are not consistent
^^^^^^^^^^^^^^^^^^^^^^^^

Ensure you're using the exact same seed:

.. code-block:: python

    # ✓ Correct - same seed
    name1 = gen.generate(seed=42)
    name2 = gen.generate(seed=42)

    # ✗ Wrong - different seeds
    name1 = gen.generate(seed=42)
    name2 = gen.generate(seed=43)  # Different!

Cannot generate enough unique names
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The simple pattern has ~30 syllables. With 2-3 syllables per name, you can
generate thousands of unique combinations, but extremely large batch requests
may fail:

.. code-block:: python

    try:
        # This might fail if requesting too many unique names
        names = gen.generate_batch(count=10000, base_seed=0, unique=True)
    except ValueError as e:
        print(f"Could not generate enough unique names: {e}")

Solution: Generate in smaller batches or wait for Phase 2 with larger syllable pools.

Next Steps
----------

* Explore the :doc:`api_reference` for detailed API documentation
* Check :doc:`development` to contribute or understand the roadmap
