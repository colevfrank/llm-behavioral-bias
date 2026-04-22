"""Main experiment runner — submits all cells as a single batch via the Batch API.

Run with:
    uv run python scripts/run_main.py [--test | --pilot]

Flags:
    --test    1 sample per cell (verify routing end-to-end)
    --pilot   5 samples per cell
    (default) 50 samples per cell

NOTE: Stimulus files must be fully populated before running.
      Check stimuli/*.json and replace all TODO placeholders.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.batch_runner import run_all_cells
from src.config import (
    SAMPLES_MAIN,
    SAMPLES_PILOT,
    all_cells,
    stimulus_path,
)


def load_prompt(experiment: str, condition: str) -> str | None:
    path = stimulus_path(experiment, condition)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    prompt = data.get("prompt", "")
    if not prompt or "TODO" in prompt:
        return None
    return prompt


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--test", action="store_true", help="1 sample per cell (routing check)")
    group.add_argument("--pilot", action="store_true", help="5 samples per cell")
    args = parser.parse_args()

    if args.test:
        n_samples = 1
    elif args.pilot:
        n_samples = SAMPLES_PILOT
    else:
        n_samples = SAMPLES_MAIN

    # Collect all cells with populated stimuli
    cells_with_prompts: list[tuple[str, str, str]] = []
    skipped = []
    for experiment, condition in all_cells():
        prompt = load_prompt(experiment, condition)
        if prompt is None:
            skipped.append(f"{experiment}_{condition}")
            continue
        cells_with_prompts.append((experiment, condition, prompt))

    if skipped:
        print(f"Skipping {len(skipped)} unpopulated cells: {skipped}\n")

    total = len(cells_with_prompts) * n_samples
    print(f"=== Submitting {len(cells_with_prompts)} cells × {n_samples} samples = {total} requests as ONE batch ===\n")

    if not cells_with_prompts:
        print("No cells to run — populate stimuli files first.")
        return

    counts = run_all_cells(cells_with_prompts, n_samples)

    total_ok = sum(counts.values())
    print(f"\n=== Done: {total_ok}/{total} requests succeeded ===")


if __name__ == "__main__":
    main()
