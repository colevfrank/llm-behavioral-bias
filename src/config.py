"""Constants and cell-ID helpers for the LLM behavioral bias study."""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
STIMULI_DIR = ROOT / "stimuli"
DATA_RAW_DIR = ROOT / "data" / "raw"
DATA_PROCESSED_DIR = ROOT / "data" / "processed"

# ── Model ──────────────────────────────────────────────────────────────────────
MODEL = "claude-opus-4-7"
TEMPERATURE = 0.5

# ── Study design ──────────────────────────────────────────────────────────────
EXPERIMENTS = ["Q1", "Q4", "Q5", "Q13"]
CONDITIONS = ["0", "A", "B", "C"]
EFFORT_LEVELS = ["low", "high"]

SAMPLES_PILOT = 5
SAMPLES_MAIN = 50

# ── Q13 canonical card values per condition ───────────────────────────────────
# Each entry: (canonical_vowel, canonical_odd, canonical_even)
# Condition 0 uses the classic E/K, 7/4 setup.
# Conditions A/B/C will vary — populate once stimuli are written.
Q13_CANONICAL: dict[str, tuple[str, str, str]] = {
    "0": ("E", "7", "4"),
    "A": ("TODO", "TODO", "TODO"),
    "B": ("TODO", "TODO", "TODO"),
    "C": ("TODO", "TODO", "TODO"),
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def cell_id(experiment: str, condition: str, effort: str) -> str:
    """Canonical identifier for one experimental cell, e.g. 'Q1_0_low'."""
    return f"{experiment}_{condition}_{effort}"


def stimulus_path(experiment: str, condition: str) -> Path:
    return STIMULI_DIR / f"{experiment}_{condition}.json"


def raw_output_path(experiment: str, condition: str, effort: str) -> Path:
    return DATA_RAW_DIR / f"{cell_id(experiment, condition, effort)}.jsonl"


def all_cells() -> list[tuple[str, str, str]]:
    """Return all (experiment, condition, effort) triples."""
    return [
        (exp, cond, effort)
        for exp in EXPERIMENTS
        for cond in CONDITIONS
        for effort in EFFORT_LEVELS
    ]
