# Project: LLM Behavioral Perturbations

Research codebase for a behavioral economics term paper. Replicates and extends 
a subset of experiments from Bini et al. (2025) "Behavioral Economics of AI," 
testing whether LLM "behavioral biases" are stable preferences or artifacts of 
autoregressive training dynamics (following McCoy et al. 2023, "Embers of 
Autoregression").

## Study design

- **Model:** Claude Opus 4.6 (`claude-opus-4-6`), via Anthropic API
- **Experiments (4):** Q1 (diminishing sensitivity), Q4 (narrow framing), 
  Q5 (hyperbolic discounting), Q13 (Wason selection task) — all from Bini et al.
- **Conditions per experiment (4):**
  - Condition 0: Verbatim Bini prompt (canonical replication baseline)
  - Condition A: Numerical perturbation (unround numbers)
  - Condition B: Non-numeric token perturbation (labels/objects/letters)
  - Condition C: Experiment-specific third perturbation
- **Reasoning effort:** low (held constant; Claude adaptive thinking, effort: "low")
- **Temperature:** 0.5 (matching Bini)
- **Samples per cell:** 50 (5 for pilot)
- **Total main run:** 800 calls, via batch API (50% discount)

## Outcome classification (from Bini et al.)

- **Q1:** `human_like = (scenario_a.choice == "B") and (scenario_b.choice == "A")`
- **Q4:** `human_like = (scenario_a.choice == "Yes") and (scenario_b.choice == "No")`
- **Q5:** `human_like = (scenario_a.choice == "A") and (scenario_b.choice == "B")`
- **Q13:** 
  - `correct = set(selected_cards) == {canonical_vowel, canonical_odd}` 
    ({E, 7} for condition 0; varies for A/B/C — parameterize)
  - `human_like_error = set(selected_cards) == {canonical_vowel, canonical_even}` 
    (confirmation bias pattern)

Bini's prompts instruct the model to return JSON with fields: Choice, Confidence, 
Explanation, Reasoning. Q1, Q4, Q5 have nested Scenario A/B structure; Q13 is 
flat. Parser must handle markdown code fence wrapping and normalize choice values 
(strip whitespace, uppercase letters, "Option A" → "A").

## Directory structure
llm-behavioral-bias/
├── .gitignore
├── .env.example
├── pyproject.toml
├── CLAUDE.md
├── README.md
├── stimuli/                # JSON per (experiment, condition), 16 files
├── src/
│   ├── api_client.py       # wraps Anthropic SDK
│   ├── batch_runner.py     # batch API submission & retrieval
│   ├── parser.py           # response parsing + classification
│   └── config.py           # model name, temperature, cell definitions
├── scripts/
│   ├── run_pilot.py
│   └── run_main.py
├── data/
│   ├── raw/                # JSONL, one file per cell
│   └── processed/
└── analysis/               # regression scripts (added later)
## Technical conventions

- Python 3.11+, managed with `uv`
- Dependencies: `anthropic`, `python-dotenv`, `tenacity`; dev: `pytest`, `ruff`
- Type hints throughout
- API key in `.env` (never commit); `.env.example` shows template
- Use `thinking: {"type": "adaptive", "effort": "low"}` for Opus 4.7
- Use `display: "summarized"` to capture reasoning traces (Opus 4.7 omits by default)
- Keep it simple: research code for a one-month project, not a library. 
  Avoid over-abstraction. Functions over classes where possible.

## API reference

For questions on Opus 4.7 extended thinking parameters, see:
https://platform.claude.com/docs/en/build-with-claude/extended-thinking

## Current status

Scope reduced before data collection: reasoning effort factor dropped for time constraints. See PREREGISTRATION.md Amendment 1.