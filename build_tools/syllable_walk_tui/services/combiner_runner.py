"""
Name combiner execution service.

Mirrors the CLI behavior of build_tools.name_combiner.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from build_tools.name_combiner.combiner import combine_syllables

if TYPE_CHECKING:
    from build_tools.syllable_walk_tui.modules.generator import CombinerState
    from build_tools.syllable_walk_tui.modules.oscillator import PatchState


@dataclass
class CombinerResult:
    """Result from combiner execution."""

    candidates: list[dict]
    output_path: Path
    meta_output: dict
    error: str | None = None


def run_combiner(
    patch: "PatchState",
    combiner_state: "CombinerState",
) -> CombinerResult:
    """
    Run name_combiner for a patch (mirrors CLI behavior exactly).

    This function mirrors the CLI:
        python -m build_tools.name_combiner \\
            --run-dir <patch.corpus_dir> \\
            --syllables <syllables> \\
            --count <count> \\
            --seed <seed> \\
            --frequency-weight <frequency_weight>

    Output is written to: <run-dir>/candidates/{prefix}_candidates_{N}syl.json

    TUI Extension:
        When combiner_state.syllable_mode == "all", this function also:
        - Generates candidates for 2, 3, and 4 syllables
        - Writes per-length files: {prefix}_candidates_2syl.json, etc.
        - Writes a combined file: {prefix}_candidates_all.json
        - Returns combined candidates in the result

    Args:
        patch: PatchState with corpus data
        combiner_state: CombinerState with generation parameters

    Returns:
        CombinerResult with generated candidates and metadata

    Note:
        Caller is responsible for validating patch state before calling.
    """
    # Extract values for clarity
    run_dir = patch.corpus_dir
    prefix = patch.corpus_type.lower() if patch.corpus_type else "nltk"
    comb = combiner_state

    # Validate required data
    if not run_dir:
        return CombinerResult(
            candidates=[],
            output_path=Path(),
            meta_output={},
            error="No corpus directory set",
        )

    if not patch.annotated_data:
        return CombinerResult(
            candidates=[],
            output_path=Path(),
            meta_output={},
            error="Annotated data not loaded",
        )

    try:
        # === Prepare output directory (mirrors CLI) ===
        candidates_dir = run_dir / "candidates"
        candidates_dir.mkdir(parents=True, exist_ok=True)

        # Determine syllable counts
        if comb.syllable_mode == "all":
            syllable_counts = [2, 3, 4]
        else:
            syllable_counts = [comb.syllables]

        all_candidates: list[dict] = []
        per_syllable_files: dict[str, str] = {}
        per_syllable_counts: dict[str, int] = {}
        last_output_path: Path | None = None

        # === Generate candidates per syllable count ===
        for syllable_count in syllable_counts:
            candidates = combine_syllables(
                annotated_data=patch.annotated_data,
                syllable_count=syllable_count,
                count=comb.count,
                seed=comb.seed,
                frequency_weight=comb.frequency_weight,
            )

            output_filename = f"{prefix}_candidates_{syllable_count}syl.json"
            output_path = candidates_dir / output_filename

            output = {
                "metadata": {
                    "source_run": run_dir.name,
                    "source_annotated": f"{prefix}_syllables_annotated.json",
                    "syllable_count": syllable_count,
                    "total_candidates": len(candidates),
                    "seed": comb.seed,
                    "frequency_weight": comb.frequency_weight,
                    "aggregation_rule": "majority",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
                "candidates": candidates,
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2)

            per_syllable_files[str(syllable_count)] = str(output_path)
            per_syllable_counts[str(syllable_count)] = len(candidates)
            last_output_path = output_path

            if comb.syllable_mode == "all":
                all_candidates.extend(candidates)
            else:
                all_candidates = candidates

        # === If "all", also write combined file ===
        if comb.syllable_mode == "all":
            combined_filename = f"{prefix}_candidates_all.json"
            combined_path = candidates_dir / combined_filename
            combined_output = {
                "metadata": {
                    "source_run": run_dir.name,
                    "source_annotated": f"{prefix}_syllables_annotated.json",
                    "syllable_count": "all",
                    "syllable_counts": syllable_counts,
                    "total_candidates": len(all_candidates),
                    "seed": comb.seed,
                    "frequency_weight": comb.frequency_weight,
                    "aggregation_rule": "majority",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "candidates_files": per_syllable_files,
                },
                "candidates": all_candidates,
            }
            with open(combined_path, "w", encoding="utf-8") as f:
                json.dump(combined_output, f, indent=2)
            last_output_path = combined_path

        if last_output_path is None:
            raise ValueError("No candidates were generated")

        # === Build meta file (mirrors CLI with TUI extensions) ===
        unique_names = len(set(c["name"] for c in all_candidates))
        unique_percentage = unique_names / len(all_candidates) * 100 if all_candidates else 0
        syllables_arg = "all" if comb.syllable_mode == "all" else comb.syllables

        meta_output = {
            "tool": "name_combiner",
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "arguments": {
                "run_dir": str(run_dir),
                "syllables": syllables_arg,
                "syllable_mode": comb.syllable_mode,
                "syllable_counts": syllable_counts,
                "count": comb.count,
                "seed": comb.seed,
                "frequency_weight": comb.frequency_weight,
            },
            "output": {
                "candidates_file": str(last_output_path),
                "candidates_generated": len(all_candidates),
                "unique_names": unique_names,
                "unique_percentage": round(unique_percentage, 2),
                "candidates_files": per_syllable_files,
                "per_syllable_counts": per_syllable_counts,
            },
        }

        meta_path = candidates_dir / f"{prefix}_combiner_meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_output, f, indent=2)

        return CombinerResult(
            candidates=all_candidates,
            output_path=last_output_path,
            meta_output=meta_output,
            error=None,
        )

    except Exception as e:
        return CombinerResult(
            candidates=[],
            output_path=Path(),
            meta_output={},
            error=str(e),
        )
