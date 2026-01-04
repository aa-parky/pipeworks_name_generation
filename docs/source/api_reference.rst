API Reference
=============

This page contains the complete API documentation for pipeworks_name_generation.

NameGenerator
-------------

.. autoclass:: pipeworks_name_generation.NameGenerator
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __repr__

Methods
^^^^^^^

generate
""""""""

.. automethod:: pipeworks_name_generation.NameGenerator.generate

generate_batch
""""""""""""""

.. automethod:: pipeworks_name_generation.NameGenerator.generate_batch

Exceptions
----------

ValueError
^^^^^^^^^^

Raised when:

* Invalid pattern specified (only "simple" supported in Phase 1)
* Invalid syllable count (< 1 or > available syllables)
* Cannot generate enough unique names in batch generation

Examples:

.. code-block:: python

    # Invalid pattern
    try:
        gen = NameGenerator(pattern="fantasy")  # Not yet supported
    except ValueError as e:
        print(e)  # "Unknown pattern: 'fantasy'"

    # Invalid syllable count
    gen = NameGenerator(pattern="simple")
    try:
        name = gen.generate(seed=42, syllables=100)  # Too many
    except ValueError as e:
        print(e)  # "Cannot generate 100 syllables..."

    # Batch generation failure
    try:
        names = gen.generate_batch(count=100000, base_seed=0, unique=True)
    except ValueError as e:
        print(e)  # "Could not generate 100000 unique names..."

Type Definitions
----------------

The library uses modern Python type hints. Key types:

* Seeds are ``int``
* Names are ``str``
* Syllable counts are ``int`` or ``Optional[int]``
* Batch results are ``list[str]``

Example with full type annotations:

.. code-block:: python

    from pipeworks_name_generation import NameGenerator

    gen: NameGenerator = NameGenerator(pattern="simple")

    # Single generation
    seed: int = 42
    syllables: int = 2
    name: str = gen.generate(seed=seed, syllables=syllables)

    # Batch generation
    count: int = 10
    base_seed: int = 1000
    unique: bool = True
    names: list[str] = gen.generate_batch(
        count=count,
        base_seed=base_seed,
        unique=unique
    )

Module Contents
---------------

The ``pipeworks_name_generation`` module exports the following:

* ``NameGenerator`` - Main class for name generation
* ``__version__`` - Package version string

.. code-block:: python

    from pipeworks_name_generation import NameGenerator, __version__

    print(__version__)  # "0.1.0-alpha"
    gen = NameGenerator(pattern="simple")

Internal Implementation
-----------------------

.. note::
    The following are internal implementation details and may change between versions.

Syllable Data
^^^^^^^^^^^^^

In Phase 1, syllables are hardcoded in ``generator._SIMPLE_SYLLABLES``:

.. code-block:: python

    _SIMPLE_SYLLABLES = [
        # Soft syllables
        "ka", "la", "thin", "mar", "in", "del",
        "so", "ra", "vyn", "tha", "len", "is",
        "el", "an", "dor", "mir", "eth", "al",
        # Hard syllables
        "grim", "thor", "ak", "bor", "din", "wyn",
        "krag", "durn", "mok", "gor", "thrak", "zar",
    ]

Random Number Generation
^^^^^^^^^^^^^^^^^^^^^^^^^

The library uses ``random.Random(seed)`` to create isolated RNG instances:

.. code-block:: python

    # Creates isolated RNG - does not affect global random state
    rng = random.Random(seed)

    # All randomness uses this isolated RNG
    syllable_count = rng.randint(2, 3)
    chosen = rng.sample(syllables, k=syllable_count)

This ensures determinism and avoids global state contamination.

Syllable Selection
^^^^^^^^^^^^^^^^^^

Syllables are selected using ``rng.sample()`` without replacement:

.. code-block:: python

    chosen = rng.sample(self._syllables, k=syllables)
    name = "".join(chosen).capitalize()

This prevents repetitive syllables like "kakaka" while maintaining determinism.
