Quickstart
==========

This guide will get you started with pipeworks_name_generation in 5 minutes.

Basic Usage
-----------

Generate a single name:

.. code-block:: python

    from pipeworks_name_generation import NameGenerator

    # Create a generator with the "simple" pattern
    gen = NameGenerator(pattern="simple")

    # Generate a name from a seed
    name = gen.generate(seed=42)
    print(name)  # "Kawyn"

Understanding Determinism
--------------------------

The **key feature** of this library is determinism. The same seed always produces
the same name:

.. code-block:: python

    gen = NameGenerator(pattern="simple")

    # These will ALWAYS be equal
    name1 = gen.generate(seed=42)
    name2 = gen.generate(seed=42)
    assert name1 == name2  # ✓ Always true

    # Different seeds produce different names
    name3 = gen.generate(seed=99)
    assert name1 != name3  # ✓ Different

This is critical for games where entity IDs need to map to consistent names.

Batch Generation
----------------

Generate multiple unique names at once:

.. code-block:: python

    gen = NameGenerator(pattern="simple")

    # Generate 10 unique names
    names = gen.generate_batch(
        count=10,
        base_seed=1000,
        unique=True  # Ensure all names are different
    )

    print(names)
    # ['Borkragmar', 'Kragso', 'Thrakrain', 'Alisra', ...]

    # Batch generation is also deterministic
    assert names == gen.generate_batch(count=10, base_seed=1000)

Controlling Syllable Count
---------------------------

Control the number of syllables in generated names:

.. code-block:: python

    gen = NameGenerator(pattern="simple")

    # Generate a 2-syllable name
    short_name = gen.generate(seed=42, syllables=2)
    print(short_name)  # "Kawyn"

    # Generate a 3-syllable name
    long_name = gen.generate(seed=42, syllables=3)
    print(long_name)  # "Kawyndel"

.. note::
    If you don't specify syllables, the generator randomly chooses 2-3
    syllables based on the seed (still deterministic).

Using in Games
--------------

Common pattern for games - use entity ID as seed:

.. code-block:: python

    from pipeworks_name_generation import NameGenerator

    gen = NameGenerator(pattern="simple")

    class NPC:
        def __init__(self, entity_id: int):
            self.id = entity_id
            # Use entity ID as seed for consistent naming
            self.name = gen.generate(seed=entity_id)

    # Every time NPC with ID 12345 is created, it has the same name
    npc1 = NPC(12345)
    npc2 = NPC(12345)
    assert npc1.name == npc2.name  # ✓ Same name every time

Next Steps
----------

* Read the :doc:`user_guide` for advanced usage
* Explore the :doc:`api_reference` for complete API documentation
* Check :doc:`development` if you want to contribute
