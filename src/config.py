"""Constants and cell-ID helpers for the LLM behavioral bias study."""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
STIMULI_DIR = ROOT / "stimuli"
DATA_RAW_DIR = ROOT / "data" / "raw"
DATA_PROCESSED_DIR = ROOT / "data" / "processed"

# ── Model ──────────────────────────────────────────────────────────────────────
MODEL = "claude-opus-4-6"
TEMPERATURE = 0.5

# ── Study design ──────────────────────────────────────────────────────────────
EXPERIMENTS = ["Q1", "Q4", "Q5", "Q13"]
CONDITIONS = ["0", "A", "B", "C"]
SAMPLES_PILOT = 5
SAMPLES_MAIN = 50

# ── Q13 canonical card values per condition ───────────────────────────────────
# Each entry: (canonical_vowel, canonical_odd, canonical_even)
# Condition 0 uses the classic E/K, 7/4 setup.
# Conditions A/B/C will vary — populate once stimuli are written.
Q13_CANONICAL_CARDS = {
    "0": {"cards": {"E", "K", "4", "7"}, "correct": {"E", "7"}, "human_like_error": {"E", "4"}},
    "A": {"cards": {"U", "M", "6", "3"}, "correct": {"U", "3"}, "human_like_error": {"U", "6"}},
    "B": {"cards": {"I", "Q", "8", "83"}, "correct": {"I", "83"}, "human_like_error": {"I", "8"}},
    "C": {"cards": {"E", "K", "4", "7"}, "correct": {"E", "7"}, "human_like_error": {"E", "4"}},  # same as condition 0 — only the rule phrasing differs
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def cell_id(experiment: str, condition: str) -> str:
    """Canonical identifier for one experimental cell, e.g. 'Q1_0'."""
    return f"{experiment}_{condition}"


def stimulus_path(experiment: str, condition: str) -> Path:
    return STIMULI_DIR / f"{experiment}_{condition}.json"


def raw_output_path(experiment: str, condition: str) -> Path:
    return DATA_RAW_DIR / f"{cell_id(experiment, condition)}.jsonl"


def all_cells() -> list[tuple[str, str]]:
    """Return all (experiment, condition) pairs — 16 cells total."""
    return [
        (exp, cond)
        for exp in EXPERIMENTS
        for cond in CONDITIONS
    ]
