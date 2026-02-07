"""
Name selector execution service.

Mirrors the CLI behavior of build_tools.name_selector.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from build_tools.name_selector.name_class import get_default_policy_path, load_name_classes
from build_tools.name_selector.selector import compute_selection_statistics, select_names
from build_tools.syllable_walk_tui.services.exporter import export_names_to_txt

if TYPE_CHECKING:
    from build_tools.syllable_walk_tui.modules.generator import CombinerState, SelectorState
    from build_tools.syllable_walk_tui.modules.oscillator import PatchState


@dataclass
class SelectorResult:
    """Result from selector execution."""

    selected: list[dict]
    selected_names: list[str]
    output_path: Path
    meta_output: dict
    error: str | None = None


def run_selector(
    patch: "PatchState",
    combiner_state: "CombinerState",
    selector_state: "SelectorState",
) -> SelectorResult:
    """
    Run name_selector for a patch (mirrors CLI behavior exactly).

    This function mirrors the CLI:
        python -m build_tools.name_selector \\
            --run-dir <patch.corpus_dir> \\
            --candidates <from combiner output> \\
            --name-class <name_class> \\
            --count <count> \\
            --mode <mode>

    Output is written to: <run-dir>/selections/{prefix}_{name_class}_{N}syl.json

    TUI Extension:
        When combiner_state.syllable_mode == "all":
        - Writes a combined selection file: {prefix}_{name_class}_all.json
        - Also writes per-length selections: {prefix}_{name_class}_2syl/3syl/4syl.json
        - Exports matching .txt files for each JSON output

    Args:
        patch: PatchState with corpus data
        combiner_state: CombinerState for candidates path and seed
        selector_state: SelectorState with selection parameters

    Returns:
        SelectorResult with selected names and metadata

    Note:
        Caller is responsible for validating patch state and combiner output
        before calling.
    """
    # Extract values for clarity
    run_dir = patch.corpus_dir
    prefix = patch.corpus_type.lower() if patch.corpus_type else "nltk"
    selector = selector_state
    combiner = combiner_state

    # Validate required data
    if not run_dir:
        return SelectorResult(
            selected=[],
            selected_names=[],
            output_path=Path(),
            meta_output={},
            error="No corpus directory set",
        )

    if not combiner.last_output_path:
        return SelectorResult(
            selected=[],
            selected_names=[],
            output_path=Path(),
            meta_output={},
            error="No candidates generated. Run Generate Candidates first.",
        )

    candidates_path = Path(combiner.last_output_path)
    if not candidates_path.exists():
        return SelectorResult(
            selected=[],
            selected_names=[],
            output_path=Path(),
            meta_output={},
            error=f"Candidates file not found: {candidates_path.name}",
        )

    try:
        # Load candidates
        with open(candidates_path, encoding="utf-8") as f:
            candidates_data = json.load(f)
        candidates = candidates_data.get("candidates", [])

        if not candidates:
            return SelectorResult(
                selected=[],
                selected_names=[],
                output_path=Path(),
                meta_output={},
                error="No candidates in file",
            )

        # Load policy
        policy_path = get_default_policy_path()
        policies = load_name_classes(policy_path)

        if selector.name_class not in policies:
            return SelectorResult(
                selected=[],
                selected_names=[],
                output_path=Path(),
                meta_output={},
                error=f"Unknown name class: {selector.name_class}",
            )

        policy = policies[selector.name_class]

        # Compute statistics
        stats = compute_selection_statistics(
            candidates, policy, mode=selector.mode  # type: ignore[arg-type]
        )

        # Select names (combined set)
        selected = select_names(
            candidates,
            policy,
            count=selector.count,
            mode=selector.mode,  # type: ignore[arg-type]
            order=selector.order,  # type: ignore[arg-type]
            seed=combiner.seed,
        )

        # Prepare output directory
        selections_dir = run_dir / "selections"
        selections_dir.mkdir(parents=True, exist_ok=True)

        # Extract syllable count from combiner state (supports "all" in TUI)
        if combiner.syllable_mode == "all":
            syllables_label = "all"
            output_filename = f"{prefix}_{selector.name_class}_all.json"
        else:
            syllables_label = str(combiner.syllables)
            output_filename = f"{prefix}_{selector.name_class}_{syllables_label}syl.json"
        output_path = selections_dir / output_filename

        # Build output structure
        output = {
            "metadata": {
                "source_candidates": candidates_path.name,
                "name_class": selector.name_class,
                "policy_description": policy.description,
                "policy_file": str(policy_path),
                "mode": selector.mode,
                "order": selector.order,
                "seed": combiner.seed,
                "total_evaluated": stats["total_evaluated"],
                "admitted": stats["admitted"],
                "rejected": stats["rejected"],
                "rejection_reasons": stats["rejection_reasons"],
                "score_distribution": stats["score_distribution"],
                "output_count": len(selected),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "selections": selected,
        }

        # Write output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        # Auto-export TXT for combined output when using "all"
        if combiner.syllable_mode == "all":
            export_names_to_txt([s["name"] for s in selected], str(output_path))

        warnings: list[str] = []

        # If "all", also generate per-syllable selections + txt
        if combiner.syllable_mode == "all":
            missing: list[str] = []
            candidates_files = combiner.last_candidates_files or {}
            for syllable_count in ["2", "3", "4"]:
                candidates_file = candidates_files.get(syllable_count)
                if not candidates_file:
                    missing.append(syllable_count)
                    continue

                per_path = Path(candidates_file)
                if not per_path.exists():
                    missing.append(syllable_count)
                    continue

                with open(per_path, encoding="utf-8") as f:
                    per_candidates_data = json.load(f)
                per_candidates = per_candidates_data.get("candidates", [])

                if not per_candidates:
                    continue

                per_stats = compute_selection_statistics(
                    per_candidates, policy, mode=selector.mode  # type: ignore[arg-type]
                )

                per_selected = select_names(
                    per_candidates,
                    policy,
                    count=selector.count,
                    mode=selector.mode,  # type: ignore[arg-type]
                    order=selector.order,  # type: ignore[arg-type]
                    seed=combiner.seed,
                )

                per_output_filename = f"{prefix}_{selector.name_class}_{syllable_count}syl.json"
                per_output_path = selections_dir / per_output_filename

                per_output = {
                    "metadata": {
                        "source_candidates": Path(candidates_file).name,
                        "name_class": selector.name_class,
                        "policy_description": policy.description,
                        "policy_file": str(policy_path),
                        "mode": selector.mode,
                        "order": selector.order,
                        "seed": combiner.seed,
                        "total_evaluated": per_stats["total_evaluated"],
                        "admitted": per_stats["admitted"],
                        "rejected": per_stats["rejected"],
                        "rejection_reasons": per_stats["rejection_reasons"],
                        "score_distribution": per_stats["score_distribution"],
                        "output_count": len(per_selected),
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    "selections": per_selected,
                }

                with open(per_output_path, "w", encoding="utf-8") as f:
                    json.dump(per_output, f, indent=2)

                export_names_to_txt([s["name"] for s in per_selected], str(per_output_path))

            if missing:
                warnings.append(
                    "Missing candidates files for syllable counts: " + ", ".join(missing)
                )

        # Build meta file
        meta_output = {
            "tool": "name_selector",
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "arguments": {
                "run_dir": str(run_dir),
                "candidates": str(candidates_path),
                "name_class": selector.name_class,
                "policy_file": str(policy_path),
                "count": selector.count,
                "mode": selector.mode,
                "order": selector.order,
                "seed": combiner.seed,
            },
            "input": {
                "candidates_file": str(candidates_path),
                "candidates_loaded": len(candidates),
                "policy_file": str(policy_path),
                "policy_name": selector.name_class,
                "policy_description": policy.description,
            },
            "output": {
                "selections_file": str(output_path),
                "selections_count": len(selected),
            },
            "statistics": {
                "total_evaluated": stats["total_evaluated"],
                "admitted": stats["admitted"],
                "admitted_percentage": (
                    round(stats["admitted"] / stats["total_evaluated"] * 100, 2)
                    if stats["total_evaluated"] > 0
                    else 0
                ),
                "rejected": stats["rejected"],
                "rejection_reasons": stats["rejection_reasons"],
                "score_distribution": stats["score_distribution"],
                "mode": selector.mode,
                "source_prefix": prefix,
                "syllable_count": syllables_label,
            },
        }

        if warnings:
            meta_output["warnings"] = warnings

        # Write meta file
        meta_filename = f"{prefix}_selector_meta.json"
        meta_path = selections_dir / meta_filename
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_output, f, indent=2)

        # Extract names for convenience
        selected_names = [s["name"] for s in selected]

        return SelectorResult(
            selected=selected,
            selected_names=selected_names,
            output_path=output_path,
            meta_output=meta_output,
            error=None,
        )

    except Exception as e:
        return SelectorResult(
            selected=[],
            selected_names=[],
            output_path=Path(),
            meta_output={},
            error=str(e),
        )
