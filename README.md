# llm-behavioral-bias

Do LLMs exhibit stable behavioral biases under scenario perturbation?

Replicates and extends Bini et al. (2025) "Behavioral Economics of AI," testing
whether LLM behavioral biases are stable preferences or artifacts of autoregressive
training dynamics (McCoy et al. 2023, "Embers of Autoregression").

## Setup

### 1. Install dependencies with uv

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv and install dependencies
uv sync

# Install dev dependencies too
uv sync --extra dev
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and paste your Anthropic API key
```

### 3. Populate stimulus files (manual step — see below)

The 16 files under `stimuli/` contain `"TODO"` placeholders. Each needs the
actual prompt text from Bini et al. (2025) before running experiments.

### 4. Verify auth with the smoke test

```bash
uv run python scripts/run_pilot.py
```

This makes one hardcoded call (`"What is 2+2?"`) and prints the response.
No stimulus files needed for this step.

### 5. Run pilot (5 samples per cell)

```bash
uv run python scripts/run_main.py --pilot
```

### 6. Run main experiment (50 samples per cell, ~1600 batch API calls)

```bash
uv run python scripts/run_main.py
```

Results land in `data/raw/<experiment>_<condition>_<effort>.jsonl`.

## Running tests

```bash
uv run pytest
# or run parser tests directly:
uv run python src/parser.py
```

## Project structure

```
stimuli/        JSON prompt files, one per (experiment × condition)
src/
  config.py     Constants, cell-ID helpers, canonical Q13 card values
  api_client.py Single-call wrapper with retry logic
  batch_runner.py Batch API submit / poll / retrieve
  parser.py     Response parsing + outcome classification (Q1, Q4, Q5, Q13)
scripts/
  run_pilot.py  Auth smoke test (one hardcoded call)
  run_main.py   Full experiment runner
data/raw/       JSONL output per cell (gitignored)
data/processed/ Analysis-ready CSVs (gitignored)
analysis/       Regression scripts (to be added)
```

## Manual steps before first real run

See checklist at the bottom of the first session notes.

1. Populate all 16 `stimuli/*.json` files with Bini et al. prompts
2. Update `Q13_CANONICAL` in `src/config.py` for conditions A, B, C
3. Run smoke test to confirm auth
4. Run `--pilot` pass and inspect `data/raw/` outputs manually
