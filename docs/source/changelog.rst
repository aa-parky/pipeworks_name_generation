Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[Unreleased]
------------

Nothing yet.

[0.1.0] - 2026-01-04
--------------------

Initial proof of concept release (Phase 1).

Added
^^^^^

* ``NameGenerator`` class with deterministic name generation
* ``generate(seed, syllables)`` method for single name generation
* ``generate_batch(count, base_seed, unique)`` method for batch generation
* Hardcoded "simple" pattern with ~30 syllables
* Comprehensive test suite with >80% coverage
* Type hints for all public APIs
* Google-style docstrings
* Sphinx documentation
* Development tooling (pytest, ruff, mypy, black)
* GitHub Actions CI/CD pipeline
* GPL-3.0-or-later license

Features
^^^^^^^^

* **Deterministic generation:** Same seed always produces same name
* **Phonetic plausibility:** Names are pronounceable and natural-sounding
* **Zero runtime dependencies:** Lightweight and fast
* **Batch generation:** Generate multiple unique names efficiently
* **Syllable control:** Specify exact syllable counts (1-N)
* **Well-tested:** Comprehensive test coverage with edge cases

Known Limitations
^^^^^^^^^^^^^^^^^

Phase 1 intentionally has these limitations (will be addressed in future phases):

* Only "simple" pattern available (hardcoded syllables)
* No pattern loading from YAML files
* No phonotactic constraints
* No CLI interface
* Limited syllable pool (~30 syllables)
* No custom pattern support

[0.0.0] - 2025-12-XX
--------------------

Project initialization.

Added
^^^^^

* Repository structure
* Initial project configuration
* Development environment setup
* CLAUDE.md guidance document
