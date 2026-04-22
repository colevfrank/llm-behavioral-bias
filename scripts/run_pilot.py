"""Pilot runner: collects 5 samples per cell (80 calls total) via batch API,
then parses every response and prints a per-cell summary for manual review.

Run with:
    uv run python scripts/run_pilot.py [--smoke-only]

Flags:
    --smoke-only  Just verify auth with one hardcoded call; skip all 16 cells.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api_client import call_model
from src.batch_runner import run_cell
from src.config import (
    Q13_CANONICAL_CARDS,
    SAMPLES_PILOT,
    all_cells,
    raw_output_path,
    stimulus_path,
)
from src.parser import parse_response

SMOKE_PROMPT = "What is 2+2? Reply in JSON with field 'answer'."


# ── Smoke test ─────────────────────────────────────────────────────────────────

def smoke_test():
    print("=== Smoke test ===")
    print(f"Prompt: {SMOKE_PROMPT!r}")
    print("Calling model ...")

    result = call_model(prompt=SMOKE_PROMPT)

    print(f"\nLatency: {result['latency_ms']} ms")
    print(f"Usage:   {result['usage']}")
    print(f"\nRaw text:\n{result['text']}")

    text = result["text"]
    try:
        data = json.loads(text.strip().strip("```json").strip("```").strip())
        answer = data.get("answer")
        print(f"\nParsed answer: {answer!r}")
        if str(answer) == "4":
            print("Auth and response handling: OK")
        else:
            print(f"Unexpected answer value: {answer!r} — check manually")
    except Exception as e:
        print(f"Could not parse response as JSON: {e}")
        print("(API call succeeded — check raw text above)")


# ── Per-cell helpers ───────────────────────────────────────────────────────────

def load_prompt(experiment: str, condition: str) -> str | None:
    path = stimulus_path(experiment, condition)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    prompt = data.get("prompt", "")
    if not prompt or "TODO" in prompt:
        return None
    return prompt


def parse_jsonl(experiment: str, condition: str) -> list[dict]:
    """Read a raw JSONL cell file and return list of parse results."""
    path = raw_output_path(experiment, condition)
    if not path.exists():
        return []

    results = []
    with path.open() as fh:
        for line in fh:
            row = json.loads(line)
            text = row.get("text") or ""
            parsed = parse_response(experiment, condition, text)
            parsed["custom_id"] = row.get("custom_id")
            parsed["raw_text"] = text
            results.append(parsed)
    return results


def print_cell_summary(experiment: str, condition: str, results: list[dict]):
    n = len(results)
    n_ok = sum(1 for r in results if r["parsed_ok"])
    print(f"\n  Parsed: {n_ok}/{n}")

    ok_results = [r for r in results if r["parsed_ok"]]

    if experiment in ("Q1", "Q4", "Q5"):
        n_human_like = sum(1 for r in ok_results if r.get("human_like"))
        print(f"  human_like: {n_human_like}/{n_ok}")
        choices = Counter(
            (r.get("scenario_a_choice"), r.get("scenario_b_choice")) for r in ok_results
        )
        print(f"  Choice distribution (A, B): {dict(choices)}")
    elif experiment == "Q13":
        n_correct = sum(1 for r in ok_results if r.get("correct"))
        n_hle = sum(1 for r in ok_results if r.get("human_like_error"))
        n_other = sum(1 for r in ok_results if r.get("other_error"))
        print(f"  correct: {n_correct}/{n_ok}  human_like_error: {n_hle}/{n_ok}  other: {n_other}/{n_ok}")
        card_dist = Counter(tuple(sorted(r["cards_selected"])) for r in ok_results)
        print(f"  Card-set distribution: {dict(card_dist)}")
        canonical = Q13_CANONICAL_CARDS[condition]
        print(f"  (canonical correct={canonical['correct']}, hle={canonical['human_like_error']})")

    # Failed parses — print raw text for manual review
    failed = [r for r in results if not r["parsed_ok"]]
    if failed:
        print(f"\n  *** {len(failed)} PARSE FAILURES ***")
        for r in failed:
            print(f"    [{r['custom_id']}] error: {r['parse_error']}")
            snippet = (r["raw_text"] or "")[:200].replace("\n", " ")
            print(f"    raw: {snippet!r}")


# ── Main ───────────────────────────────────────────────────────────────────────

def run_pilot():
    cells = all_cells()
    print(f"=== Pilot run: {len(cells)} cells × {SAMPLES_PILOT} samples = {len(cells) * SAMPLES_PILOT} total calls ===\n")

    skipped = []
    for experiment, condition in cells:
        cell = f"{experiment}_{condition}"
        print(f"\n--- Cell: {cell} ---")

        prompt = load_prompt(experiment, condition)
        if prompt is None:
            print("  SKIP: stimulus file missing or not populated")
            skipped.append(cell)
            continue

        run_cell(experiment, condition, prompt, SAMPLES_PILOT)
        results = parse_jsonl(experiment, condition)
        print_cell_summary(experiment, condition, results)

    print("\n=== Pilot complete ===")
    if skipped:
        print(f"Skipped {len(skipped)} cells (unpopulated stimuli): {skipped}")
    print("\nReview parse failures above before running the main experiment.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-only", action="store_true", help="Auth check only, skip pilot cells")
    args = parser.parse_args()

    smoke_test()
    if not args.smoke_only:
        run_pilot()


if __name__ == "__main__":
    main()
