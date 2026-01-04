Development
===========

This guide is for contributors and developers working on pipeworks_name_generation.

Development Setup
-----------------

Prerequisites
^^^^^^^^^^^^^

* Python 3.12 or higher
* git
* Virtual environment tool (venv, virtualenv, conda, etc.)

Clone and Setup
^^^^^^^^^^^^^^^

.. code-block:: bash

    # Clone repository
    git clone https://github.com/aa-parky/pipeworks_name_generation.git
    cd pipeworks_name_generation

    # Create virtual environment
    python3.12 -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate

    # Install in development mode with dev dependencies
    pip install -e ".[dev]"

Development Commands
--------------------

Testing
^^^^^^^

.. code-block:: bash

    # Run all tests with coverage
    pytest

    # Run specific test file
    pytest tests/test_minimal_generation.py

    # Run specific test
    pytest tests/test_minimal_generation.py::TestBasicGeneration::test_generator_creates_deterministic_names

    # Run verbose
    pytest -v

    # Run with coverage report
    pytest --cov=pipeworks_name_generation --cov-report=html

Linting
^^^^^^^

.. code-block:: bash

    # Lint with ruff
    ruff check .

    # Auto-fix linting issues
    ruff check --fix .

Type Checking
^^^^^^^^^^^^^

.. code-block:: bash

    # Type check with mypy
    mypy pipeworks_name_generation/

Formatting
^^^^^^^^^^

.. code-block:: bash

    # Format with black (line length: 100)
    black pipeworks_name_generation/ tests/

Documentation
^^^^^^^^^^^^^

.. code-block:: bash

    # Build documentation
    cd docs
    make html

    # View documentation
    open build/html/index.html  # macOS
    xdg-open build/html/index.html  # Linux
    start build/html/index.html  # Windows

Project Structure
-----------------

.. code-block:: text

    pipeworks_name_generation/
    ├── pipeworks_name_generation/   # Core library code
    │   ├── __init__.py             # Package exports
    │   └── generator.py            # NameGenerator implementation
    ├── tests/                       # pytest test suite
    │   ├── __init__.py
    │   └── test_minimal_generation.py
    ├── examples/                    # Usage examples
    │   └── minimal_proof_of_concept.py
    ├── docs/                        # Sphinx documentation
    │   ├── source/
    │   └── build/
    ├── data/                        # Pattern files (future)
    ├── build_tools/                 # Build-time tools (future)
    ├── scripts/                     # Utility scripts
    ├── pyproject.toml              # Project configuration
    ├── CLAUDE.md                   # AI assistant guidance
    └── README.md                   # Project overview

Critical Design Principles
--------------------------

Determinism is Paramount
^^^^^^^^^^^^^^^^^^^^^^^^

The same seed **must always** produce the same name. This is the most important
requirement:

.. code-block:: python

    # This test MUST ALWAYS pass
    gen = NameGenerator(pattern="simple")
    assert gen.generate(seed=42) == gen.generate(seed=42)

**Implementation:**

* Use ``random.Random(seed)`` to create isolated RNG instances
* NEVER use ``random.seed()`` (global state)
* All randomness must flow from the seed parameter

Zero Runtime Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^

The core generator has no runtime dependencies (by design). This keeps it:

* Fast
* Lightweight
* Easy to integrate
* Minimal security surface

**Note:** Build-time tools (Phase 2+) can use heavy libraries like NLTK, but
these must NEVER be runtime dependencies.

Context-Free Generation
^^^^^^^^^^^^^^^^^^^^^^^

Names are structural only - no semantic meaning, culture, or lore:

* No cultural/historical affiliations
* No genre-specific patterns (fantasy, sci-fi, etc.)
* No embedded meaning
* Applications provide context, not the generator

Development Phases
------------------

Phase 1: Proof of Concept (Current)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Status:** Complete

* Minimal working implementation
* Hardcoded syllables in ``generator.py``
* Only "simple" pattern
* Deterministic generation verified
* Basic test suite

**Intentional Limitations:**

* No YAML pattern loading
* No phonotactic constraints
* No CLI
* Limited syllable pool

Phase 2: Pattern System (Planned)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Goals:**

* Load patterns from YAML files in ``data/`` directory
* Multiple pattern sets (simple, complex, etc.)
* Pattern validation and error handling
* Expanded syllable pools

**Design:**

.. code-block:: yaml

    # data/patterns/simple.yaml
    name: simple
    description: Basic pronounceable syllables
    syllables:
      - ka
      - la
      - thin
      # ...
    constraints:
      min_syllables: 2
      max_syllables: 4

Phase 3: Build Tools (Planned)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Goals:**

* Syllable extraction from text corpora
* Phonotactic analysis tools
* Pattern generation utilities
* Quality validation tools

**Location:** ``build_tools/`` directory

**Dependencies:** NLTK, spacy, etc. (build-time only!)

Phase 4: Advanced Features (Future)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Phonotactic constraints (no invalid sound combinations)
* Weighted syllable selection
* Pattern mixing and blending
* CLI interface
* Performance optimization

Contributing
------------

We welcome contributions! Here's how to contribute:

1. **Fork the repository**
2. **Create a feature branch:** ``git checkout -b feature/my-feature``
3. **Make your changes** following the guidelines below
4. **Add tests** for new functionality
5. **Ensure all tests pass:** ``pytest``
6. **Lint your code:** ``ruff check . && mypy pipeworks_name_generation/``
7. **Commit your changes:** ``git commit -m "Add my feature"``
8. **Push to your fork:** ``git push origin feature/my-feature``
9. **Open a Pull Request**

Contribution Guidelines
-----------------------

Code Style
^^^^^^^^^^

* Follow PEP 8 (enforced by ruff)
* Line length: 100 characters
* Use type hints for all functions
* Google-style docstrings

Testing Requirements
^^^^^^^^^^^^^^^^^^^^

All changes must maintain determinism:

.. code-block:: python

    def test_determinism():
        """All generation must be deterministic."""
        gen = NameGenerator(pattern="simple")
        assert gen.generate(seed=42) == gen.generate(seed=42)

    def test_batch_determinism():
        """Batch generation must be deterministic."""
        gen = NameGenerator(pattern="simple")
        batch1 = gen.generate_batch(count=5, base_seed=42)
        batch2 = gen.generate_batch(count=5, base_seed=42)
        assert batch1 == batch2

* Write tests for all new features
* Aim for >80% code coverage
* Test edge cases and error conditions
* Use parametrized tests for multiple scenarios

Documentation Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^

* Update docstrings for modified functions
* Add examples to user guide for new features
* Update API reference if adding public methods
* Update CLAUDE.md for significant architectural changes

License
-------

This project is licensed under GPL-3.0-or-later. All contributions must remain GPL.

By contributing, you agree to license your contributions under the GPL-3.0-or-later license.

Roadmap
-------

**Phase 1 (Current):** Proof of concept with hardcoded syllables ✓

**Phase 2 (Next):** Pattern loading system

* YAML pattern files
* Multiple pattern sets
* Pattern validation

**Phase 3:** Build tools for corpus analysis

* Syllable extraction
* Phonotactic analysis
* Pattern generation utilities

**Phase 4:** Advanced features

* CLI interface
* Phonotactic constraints
* Performance optimization
* Additional pattern sets

Getting Help
------------

* **Issues:** https://github.com/aa-parky/pipeworks_name_generation/issues
* **Discussions:** https://github.com/aa-parky/pipeworks_name_generation/discussions
* **Email:** your.email@example.com

Resources
---------

* :doc:`api_reference` - Complete API documentation
* :doc:`user_guide` - Detailed usage guide
* ``CLAUDE.md`` - Guidance for AI assistants working on this project
* ``examples/`` - Working code examples
