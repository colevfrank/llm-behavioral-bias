"""Batch API submission and retrieval.

Supports two modes:
  - run_cell():      single cell (used by pilot)
  - run_all_cells(): single batch with all cells (used by main run)
"""

import json
import os
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from src.config import MODEL, TEMPERATURE, cell_id, raw_output_path

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
    """Build one request entry for the Messages Batch API."""
    return {
        "custom_id": custom_id,
        "params": {
            "model": MODEL,
            "max_tokens": 4096,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        },
    }


def submit_batch(requests: list[dict]) -> str:
    """Submit a list of request dicts to the Batch API. Returns batch_id."""
    client = _get_client()
    batch = client.messages.batches.create(requests=requests)
    print(f"Submitted batch {batch.id} — {len(requests)} requests")
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


def retrieve_and_demux(batch_id: str) -> dict[str, int]:
    """Stream batch results and write to per-cell JSONL files.

    Demuxes by parsing the custom_id prefix (e.g. "Q1_0_0042" → cell "Q1_0").
    Each JSONL line: {custom_id, text, usage, error}.

    Returns:
        dict mapping cell_id → number of successful results.
    """
    client = _get_client()
    file_handles: dict[str, object] = {}
    counts: dict[str, int] = {}

    try:
        for result in client.messages.batches.results(batch_id):
            cid = result.custom_id
            # custom_id format: {experiment}_{condition}_{sample_id}
            # cell = everything before the last underscore segment
            parts = cid.rsplit("_", 1)
            cell = parts[0]

            # Open file handle lazily
            if cell not in file_handles:
                # Parse experiment and condition from the cell id
                exp_parts = cell.split("_", 1)
                out_path = raw_output_path(exp_parts[0], exp_parts[1])
                out_path.parent.mkdir(parents=True, exist_ok=True)
                file_handles[cell] = out_path.open("w")
                counts[cell] = 0

            row: dict = {"custom_id": cid}
            if result.result.type == "succeeded":
                msg = result.result.message
                text = next((b.text for b in msg.content if b.type == "text"), "")
                row["text"] = text
                row["usage"] = {
                    "input_tokens": msg.usage.input_tokens,
                    "output_tokens": msg.usage.output_tokens,
                }
                row["error"] = None
                counts[cell] += 1
            else:
                row["text"] = None
                row["usage"] = None
                row["error"] = result.result.type

            file_handles[cell].write(json.dumps(row) + "\n")
    finally:
        for fh in file_handles.values():
            fh.close()

    return counts


def build_requests(
    cells: list[tuple[str, str, str]],
    n_samples: int,
    temperature: float = TEMPERATURE,
) -> list[dict]:
    """Build all request dicts for a list of (experiment, condition, prompt) triples."""
    requests = []
    for experiment, condition, prompt in cells:
        for i in range(n_samples):
            requests.append(
                _make_request(
                    custom_id=f"{experiment}_{condition}_{i:04d}",
                    prompt=prompt,
                    temperature=temperature,
                )
            )
    return requests


def run_all_cells(
    cells: list[tuple[str, str, str]],
    n_samples: int,
    temperature: float = TEMPERATURE,
) -> dict[str, int]:
    """Submit all cells as a single batch, poll, retrieve, and demux.

    Args:
        cells: list of (experiment, condition, prompt) triples.
        n_samples: samples per cell.

    Returns:
        dict mapping cell_id → number of successful results.
    """
    requests = build_requests(cells, n_samples, temperature)
    batch_id = submit_batch(requests)
    poll_batch(batch_id)
    counts = retrieve_and_demux(batch_id)

    for cid, n_ok in sorted(counts.items()):
        print(f"  {cid}: {n_ok}/{n_samples} succeeded")

    return counts


# ── Single-cell convenience (used by pilot) ───────────────────────────────────

def run_cell(
    experiment: str,
    condition: str,
    prompt: str,
    n_samples: int,
    temperature: float = TEMPERATURE,
) -> Path:
    """Submit, poll, and retrieve a single cell. Returns path to written JSONL."""
    requests = build_requests([(experiment, condition, prompt)], n_samples, temperature)
    batch_id = submit_batch(requests)
    poll_batch(batch_id)
    counts = retrieve_and_demux(batch_id)
    cid = cell_id(experiment, condition)
    n_ok = counts.get(cid, 0)
    out = raw_output_path(experiment, condition)
    print(f"  Wrote {n_ok}/{n_samples} results to {out}")
    return out
