"""Analysis tools for annotated syllables.

This subpackage provides post-annotation analysis utilities for inspecting
and understanding the annotated syllable corpus.

Available Tools
---------------
**random_sampler**: Random sampling utility for QA and inspection
**feature_signatures**: Feature signature analysis and distribution reporting

Quick Start
-----------
Random sampling::

    $ python -m build_tools.syllable_feature_annotator.analysis.random_sampler --samples 50

Feature signature analysis::

    $ python -m build_tools.syllable_feature_annotator.analysis.feature_signatures

Programmatic Usage
------------------
Random sampling::

    >>> from build_tools.syllable_feature_annotator.analysis import (
    ...     load_annotated_syllables,
    ...     sample_syllables,
    ...     save_samples
    ... )
    >>> records = load_annotated_syllables(Path("data/annotated/syllables_annotated.json"))
    >>> samples = sample_syllables(records, 50, seed=42)
    >>> save_samples(samples, Path("output.json"))

Feature signature analysis::

    >>> from build_tools.syllable_feature_annotator.analysis import (
    ...     run_analysis,
    ...     extract_signature,
    ...     analyze_feature_signatures
    ... )
    >>> result = run_analysis(
    ...     input_path=Path("data/annotated/syllables_annotated.json"),
    ...     output_dir=Path("_working/analysis/"),
    ...     limit=20
    ... )
"""

# Feature signatures exports
from build_tools.syllable_feature_annotator.analysis.feature_signatures import (
    analyze_feature_signatures,
    extract_signature,
    format_signature_report,
    run_analysis,
    save_report,
)
from build_tools.syllable_feature_annotator.analysis.feature_signatures import (
    parse_args as parse_feature_signatures_args,
)

# Random sampler exports
from build_tools.syllable_feature_annotator.analysis.random_sampler import (
    load_annotated_syllables,
    sample_syllables,
    save_samples,
)
from build_tools.syllable_feature_annotator.analysis.random_sampler import (
    parse_arguments as parse_random_sampler_arguments,
)

__all__ = [
    # Random sampler
    "load_annotated_syllables",
    "sample_syllables",
    "save_samples",
    "parse_random_sampler_arguments",
    # Feature signatures
    "extract_signature",
    "analyze_feature_signatures",
    "format_signature_report",
    "run_analysis",
    "save_report",
    "parse_feature_signatures_args",
]
