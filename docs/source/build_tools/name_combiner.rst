=============
Name Combiner
=============

.. currentmodule:: build_tools.name_combiner

Overview
--------

.. automodule:: build_tools.name_combiner
   :no-members:

Command-Line Interface
----------------------

.. argparse::
   :module: build_tools.name_combiner.cli
   :func: create_argument_parser
   :prog: python -m build_tools.name_combiner

Output Format
-------------

Input/Output Contract
~~~~~~~~~~~~~~~~~~~~~

**Inputs** (from syllable feature annotator):

- ``<run_directory>/data/pyphen_syllables_annotated.json`` or ``nltk_syllables_annotated.json``

**Output** (auto-detected from run directory):

- ``<run_directory>/candidates/{prefix}_candidates_{N}syl.json``

**Example directory structure after combination:**

.. code-block:: text

    _working/output/20260110_115453_pyphen/
    ├── candidates/
    │   └── pyphen_candidates_2syl.json      ← Generated output
    ├── data/
    │   └── pyphen_syllables_annotated.json  ← Input
    ├── meta/
    ├── syllables/
    └── ...

Output Structure
~~~~~~~~~~~~~~~~

The combiner produces JSON with this structure:

.. code-block:: json

   {
     "metadata": {
       "source_run": "20260110_115453_pyphen",
       "source_annotated": "pyphen_syllables_annotated.json",
       "syllable_count": 2,
       "total_candidates": 10000,
       "seed": 42,
       "frequency_weight": 1.0,
       "aggregation_rule": "majority",
       "generated_at": "2026-01-10T12:00:00Z"
     },
     "candidates": [
       {
         "name": "kali",
         "syllables": ["ka", "li"],
         "features": {
           "starts_with_vowel": false,
           "starts_with_cluster": false,
           "starts_with_heavy_cluster": false,
           "contains_plosive": true,
           "contains_fricative": false,
           "contains_liquid": true,
           "contains_nasal": false,
           "short_vowel": true,
           "long_vowel": false,
           "ends_with_vowel": true,
           "ends_with_nasal": false,
           "ends_with_stop": false
         }
       }
     ]
   }

Feature Aggregation Rules
~~~~~~~~~~~~~~~~~~~~~~~~~

Name-level features are aggregated from syllable-level features using these rules:

- **Onset features** (``starts_with_*``): First syllable only
- **Coda features** (``ends_with_*``): Final syllable only
- **Internal features** (``contains_*``): Boolean OR across all syllables
- **Nucleus features** (``short_vowel``, ``long_vowel``): Majority rule (>50%)

The majority rule for nucleus features was chosen for architectural consistency with other
feature categories (deterministic, binary outcome), and to maintain simplicity in the
selection pipeline while being sufficient for the current 3-class system.

Integration Guide
-----------------

The name combiner sits between the feature annotator and the name selector. It performs
structural combination without policy evaluation - that responsibility belongs to the
name_selector module.

**Typical workflow:**

.. code-block:: bash

   # Step 1: Extract and normalize syllables
   python -m build_tools.pyphen_syllable_extractor --file corpus.txt
   python -m build_tools.pyphen_syllable_normaliser \
     --run-dir _working/output/20260110_115453_pyphen/

   # Step 2: Annotate with features
   python -m build_tools.syllable_feature_annotator \
     --syllables _working/output/20260110_115453_pyphen/pyphen_syllables_unique.txt \
     --frequencies _working/output/20260110_115453_pyphen/pyphen_syllables_frequencies.json

   # Step 3: Generate candidates
   python -m build_tools.name_combiner \
     --run-dir _working/output/20260110_115453_pyphen/ \
     --syllables 2 \
     --count 10000 \
     --seed 42

   # Step 4: Select names (see name_selector)
   python -m build_tools.name_selector \
     --run-dir _working/output/20260110_115453_pyphen/ \
     --candidates candidates/pyphen_candidates_2syl.json \
     --name-class first_name

**When to use this tool:**

- After syllable annotation is complete
- Before selecting names against policies
- When you need large pools of name candidates for filtering
- For deterministic name generation pipelines

Notes
-----

**Determinism:**

The combiner uses ``random.Random(seed)`` for isolated RNG, ensuring the same seed always
produces identical candidates. This is critical for reproducible name generation.

**Frequency weighting:**

- ``frequency_weight=1.0`` (default): High-frequency syllables dominate
- ``frequency_weight=0.0``: Uniform random sampling
- Values between 0-1: Interpolated weighting

**Build-time tool:**

This is a build-time tool only - not used during runtime name generation.

API Reference
-------------

.. automodule:: build_tools.name_combiner
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: build_tools.name_combiner.aggregator
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: build_tools.name_combiner.combiner
   :members:
   :undoc-members:
   :show-inheritance:
