"""Main experiment runner — submits all 16 cells via the Batch API.

Run with:
    uv run python scripts/run_main.py [--pilot]

Flags:
    --pilot   Run 5 samples per cell instead of 50 (for piloting)

NOTE: Stimulus files must be fully populated before running.
      Check stimuli/*.json and replace all TODO placeholders.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.batch_runner import run_cell
from src.config import (
    SAMPLES_MAIN,
    SAMPLES_PILOT,
    all_cells,
    stimulus_path,
)


def load_prompt(experiment: str, condition: str) -> str:
    path = stimulus_path(experiment, condition)
    if not path.exists():
        raise FileNotFoundError(f"Stimulus file missing: {path}")
    data = json.loads(path.read_text())
    prompt = data.get("prompt", "")
    if not prompt or "TODO" in prompt:
        raise ValueError(f"Stimulus file not populated: {path}")
    return prompt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true", help="Run 5 samples per cell")
    args = parser.parse_args()

    n_samples = SAMPLES_PILOT if args.pilot else SAMPLES_MAIN
    cells = all_cells()

    print(f"=== Main run: {len(cells)} cells × {n_samples} samples = {len(cells) * n_samples} total calls ===\n")

    for experiment, condition in cells:
        cell = f"{experiment}_{condition}"
        print(f"\n--- Cell: {cell} ---")
        try:
            prompt = load_prompt(experiment, condition)
        except (FileNotFoundError, ValueError) as e:
            print(f"  SKIP: {e}")
            continue
        run_cell(experiment, condition, prompt, n_samples)

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
