pipeworks_name_generation
==========================

**Phonetically-grounded name generation for games and procedural systems**

A deterministic, context-free name generator that produces pronounceable, neutral names
without imposing semantic meaning. Designed for games where entity IDs need to map to
consistent names across sessions.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   user_guide
   api_reference
   development
   changelog

Features
--------

* **Deterministic**: Same seed always produces the same name
* **Phonetically plausible**: Names are pronounceable and natural-sounding
* **Context-free**: No cultural, historical, or semantic affiliations
* **Lightweight**: Zero runtime dependencies
* **Well-tested**: Comprehensive test suite with >80% coverage

Quick Example
-------------

.. code-block:: python

    from pipeworks_name_generation import NameGenerator

    # Create a generator
    gen = NameGenerator(pattern="simple")

    # Generate a name deterministically
    name = gen.generate(seed=42)
    print(name)  # "Kawyn"

    # Same seed = same name (always!)
    assert gen.generate(seed=42) == name

    # Generate multiple names
    names = gen.generate_batch(count=10, base_seed=1000, unique=True)
    print(names)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
