"""Batch API submission and retrieval for one experimental cell."""

import json
import os
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from src.config import MODEL, TEMPERATURE, raw_output_path

load_dotenv()

POLL_INTERVAL_S = 30  # seconds between status checks


def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set.")
    return anthropic.Anthropic(api_key=api_key)


def _make_request(
    custom_id: str,
    prompt: str,
    temperature: float,
) -> dict:
    """Build one BatchRequest for the Messages Batch API."""
    return {
        "custom_id": custom_id,
        "params": {
            "model": MODEL,
            "max_tokens": 4096,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        },
    }


def submit_batch(
    experiment: str,
    condition: str,
    prompt: str,
    n_samples: int,
    temperature: float = TEMPERATURE,
) -> str:
    """Submit a batch for one (experiment, condition) cell.

    Args:
        experiment:  e.g. "Q1"
        condition:   e.g. "0", "A", "B", "C"
        prompt:      The full user-facing prompt string.
        n_samples:   How many independent samples to request.
        temperature: Sampling temperature.

    Returns:
        batch_id (str) — save this to poll later.
    """
    client = _get_client()

    requests = [
        _make_request(
            custom_id=f"{experiment}_{condition}_{i:04d}",
            prompt=prompt,
            temperature=temperature,
        )
        for i in range(n_samples)
    ]

    batch = client.messages.batches.create(requests=requests)
    print(f"Submitted batch {batch.id} — {n_samples} requests for cell {experiment}_{condition}")
    return batch.id


def poll_batch(batch_id: str, poll_interval_s: int = POLL_INTERVAL_S):
    """Block until the batch is complete, printing status updates."""
    client = _get_client()

    while True:
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        counts = batch.request_counts
        print(
            f"  [{batch_id}] status={status} "
            f"processing={counts.processing} "
            f"succeeded={counts.succeeded} "
            f"errored={counts.errored}"
        )
        if status == "ended":
            return batch
        time.sleep(poll_interval_s)


def retrieve_results(batch_id: str, out_path: Path) -> int:
    """Stream batch results and write to a JSONL file.

    Each line is a JSON object with:
        custom_id, text, usage, error

    Returns:
        Number of successful results written.
    """
    client = _get_client()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_ok = 0
    with out_path.open("w") as fh:
        for result in client.messages.batches.results(batch_id):
            row: dict = {"custom_id": result.custom_id}

            if result.result.type == "succeeded":
                msg = result.result.message
                text = next((b.text for b in msg.content if b.type == "text"), "")
                row["text"] = text
                row["usage"] = {
                    "input_tokens": msg.usage.input_tokens,
                    "output_tokens": msg.usage.output_tokens,
                }
                row["error"] = None
                n_ok += 1
            else:
                row["text"] = None
                row["usage"] = None
                row["error"] = result.result.type

            fh.write(json.dumps(row) + "\n")

    return n_ok


def run_cell(
    experiment: str,
    condition: str,
    prompt: str,
    n_samples: int,
    temperature: float = TEMPERATURE,
) -> Path:
    """Submit, poll, and retrieve a full cell. Returns path to written JSONL."""
    batch_id = submit_batch(experiment, condition, prompt, n_samples, temperature)
    poll_batch(batch_id)
    out = raw_output_path(experiment, condition)
    n_ok = retrieve_results(batch_id, out)
    print(f"  Wrote {n_ok}/{n_samples} results to {out}")
    return out
