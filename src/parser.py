"""Response parsing and outcome classification for Q1, Q4, Q5, Q13.

All parse_* functions:
  - Accept a `condition` parameter ("0", "A", "B", "C") that controls which
    choice labels and classification logic to apply.
  - Never raise on malformed input.
  - Return a dict always containing `parsed_ok` (bool) and `parse_error` (str|None).
"""

import json
import re
import sys
from pathlib import Path

# Allow `python src/parser.py` as well as `uv run pytest`
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Q13_CANONICAL_CARDS


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _strip_fence(text: str) -> str:
    """Remove markdown code fences (```json ... ``` or ``` ... ```)."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def _extract_json(text: str) -> dict | None:
    """Try to extract a JSON object from arbitrary text.

    Tries in order:
      1. Direct parse after fence stripping
      2. First {...} block found in the text
    Returns None on failure.
    """
    cleaned = _strip_fence(text)
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def _get_scenario(data: dict, key_variants: list[str]) -> dict | None:
    """Case-insensitive lookup for a scenario sub-dict."""
    upper_variants = [v.upper() for v in key_variants]
    for k, v in data.items():
        if k.strip().upper() in upper_variants and isinstance(v, dict):
            return v
    return None


def _get_choice_upper(scenario: dict) -> str | None:
    """Return the Choice field stripped, uppercased, with 'OPTION X' → 'X'."""
    for k, v in scenario.items():
        if k.strip().upper() == "CHOICE":
            s = str(v).strip().upper()
            s = re.sub(r"^OPTION\s+", "", s)
            return s
    return None


def _get_choice_lower(scenario: dict) -> str | None:
    """Return the Choice field stripped and lowercased (preserves label tokens)."""
    for k, v in scenario.items():
        if k.strip().upper() == "CHOICE":
            return str(v).strip().lower()
    return None


def _norm_apostrophe(s: str) -> str:
    """Normalise curly/smart apostrophes to straight apostrophe."""
    return s.replace("\u2019", "'").replace("\u2018", "'")


# ── Q13 card extraction ────────────────────────────────────────────────────────

def _extract_q13_cards(choice_text: str, condition: str) -> set[str]:
    """Extract the set of valid cards from a Choice value string.

    Sorts valid cards by length descending so multi-char tokens like "83"
    are matched before single-char prefixes like "8".
    """
    valid_cards: set[str] = Q13_CANONICAL_CARDS[condition]["cards"]
    sorted_cards = sorted(valid_cards, key=len, reverse=True)
    pattern = r"\b(" + "|".join(re.escape(c) for c in sorted_cards) + r")\b"
    matches = re.findall(pattern, choice_text.upper())
    return set(matches) & valid_cards


# ── Per-experiment parsers ─────────────────────────────────────────────────────

def parse_q1(text: str, condition: str = "0") -> dict:
    """Parse Q1 (diminishing sensitivity).

    Conditions 0/A/B — Choice ∈ {"A", "B"}:
        human_like = (scenario_a == "B") AND (scenario_b == "A")

    Condition C — Choice ∈ {"the gamble", "the certain amount"}:
        human_like = (scenario_a == "the certain amount") AND (scenario_b == "the gamble")
    """
    result: dict = {
        "parsed_ok": False,
        "parse_error": None,
        "scenario_a_choice": None,
        "scenario_b_choice": None,
        "human_like": None,
        "raw_json": None,
    }

    data = _extract_json(text)
    if data is None:
        result["parse_error"] = "no JSON found"
        return result
    result["raw_json"] = data

    sa = _get_scenario(data, ["Scenario A", "scenario_a", "A"])
    sb = _get_scenario(data, ["Scenario B", "scenario_b", "B"])
    if sa is None:
        result["parse_error"] = "missing Scenario A"
        return result
    if sb is None:
        result["parse_error"] = "missing Scenario B"
        return result

    if condition in ("0", "A", "B"):
        ca = _get_choice_upper(sa)
        cb = _get_choice_upper(sb)
        if ca is None:
            result["parse_error"] = "missing Choice in Scenario A"
            return result
        if cb is None:
            result["parse_error"] = "missing Choice in Scenario B"
            return result
        result["scenario_a_choice"] = ca
        result["scenario_b_choice"] = cb
        result["human_like"] = (ca == "B") and (cb == "A")
    else:  # condition C
        ca = _get_choice_lower(sa)
        cb = _get_choice_lower(sb)
        if ca is None:
            result["parse_error"] = "missing Choice in Scenario A"
            return result
        if cb is None:
            result["parse_error"] = "missing Choice in Scenario B"
            return result
        result["scenario_a_choice"] = ca
        result["scenario_b_choice"] = cb
        result["human_like"] = (ca == "the certain amount") and (cb == "the gamble")

    result["parsed_ok"] = True
    return result


def parse_q4(text: str, condition: str = "0") -> dict:
    """Parse Q4 (narrow framing).

    Conditions 0/A/B — Choice ∈ {"Yes", "No"}:
        human_like = (scenario_a == "YES") AND (scenario_b == "NO")

    Condition C — Choice ∈ {"make the trip", "don't make the trip"}:
        human_like = (scenario_a == "make the trip") AND (scenario_b == "don't make the trip")
        Handles both straight (') and curly (\u2019) apostrophes.
    """
    result: dict = {
        "parsed_ok": False,
        "parse_error": None,
        "scenario_a_choice": None,
        "scenario_b_choice": None,
        "human_like": None,
        "raw_json": None,
    }

    data = _extract_json(text)
    if data is None:
        result["parse_error"] = "no JSON found"
        return result
    result["raw_json"] = data

    sa = _get_scenario(data, ["Scenario A", "scenario_a", "A"])
    sb = _get_scenario(data, ["Scenario B", "scenario_b", "B"])
    if sa is None:
        result["parse_error"] = "missing Scenario A"
        return result
    if sb is None:
        result["parse_error"] = "missing Scenario B"
        return result

    if condition in ("0", "A", "B"):
        ca = _get_choice_upper(sa)
        cb = _get_choice_upper(sb)
        if ca is None:
            result["parse_error"] = "missing Choice in Scenario A"
            return result
        if cb is None:
            result["parse_error"] = "missing Choice in Scenario B"
            return result
        result["scenario_a_choice"] = ca
        result["scenario_b_choice"] = cb
        result["human_like"] = (ca == "YES") and (cb == "NO")
    else:  # condition C
        ca_raw = _get_choice_lower(sa)
        cb_raw = _get_choice_lower(sb)
        if ca_raw is None:
            result["parse_error"] = "missing Choice in Scenario A"
            return result
        if cb_raw is None:
            result["parse_error"] = "missing Choice in Scenario B"
            return result
        ca = _norm_apostrophe(ca_raw)
        cb = _norm_apostrophe(cb_raw)
        result["scenario_a_choice"] = ca
        result["scenario_b_choice"] = cb
        result["human_like"] = (ca == "make the trip") and (cb == "don't make the trip")

    result["parsed_ok"] = True
    return result


def parse_q5(text: str, condition: str = "0") -> dict:
    """Parse Q5 (hyperbolic discounting).

    Conditions 0/A — Choice ∈ {"A", "B"}:
        human_like = (scenario_a == "A") AND (scenario_b == "B")

    Conditions B/C — Choice ∈ {"the sooner payment", "the later payment"}:
        human_like = (scenario_a == "the sooner payment") AND (scenario_b == "the later payment")
    """
    result: dict = {
        "parsed_ok": False,
        "parse_error": None,
        "scenario_a_choice": None,
        "scenario_b_choice": None,
        "human_like": None,
        "raw_json": None,
    }

    data = _extract_json(text)
    if data is None:
        result["parse_error"] = "no JSON found"
        return result
    result["raw_json"] = data

    sa = _get_scenario(data, ["Scenario A", "scenario_a", "A"])
    sb = _get_scenario(data, ["Scenario B", "scenario_b", "B"])
    if sa is None:
        result["parse_error"] = "missing Scenario A"
        return result
    if sb is None:
        result["parse_error"] = "missing Scenario B"
        return result

    if condition in ("0", "A"):
        ca = _get_choice_upper(sa)
        cb = _get_choice_upper(sb)
        if ca is None:
            result["parse_error"] = "missing Choice in Scenario A"
            return result
        if cb is None:
            result["parse_error"] = "missing Choice in Scenario B"
            return result
        result["scenario_a_choice"] = ca
        result["scenario_b_choice"] = cb
        result["human_like"] = (ca == "A") and (cb == "B")
    else:  # conditions B, C
        ca = _get_choice_lower(sa)
        cb = _get_choice_lower(sb)
        if ca is None:
            result["parse_error"] = "missing Choice in Scenario A"
            return result
        if cb is None:
            result["parse_error"] = "missing Choice in Scenario B"
            return result
        result["scenario_a_choice"] = ca
        result["scenario_b_choice"] = cb
        result["human_like"] = (ca == "the sooner payment") and (cb == "the later payment")

    result["parsed_ok"] = True
    return result


def parse_q13(text: str, condition: str = "0") -> dict:
    """Parse Q13 (Wason selection task).

    Extracts card selections from the Choice field of a flat JSON response.
    Choice may be a list, a comma/space-separated string, or natural prose —
    valid card tokens are extracted via regex regardless of surrounding text.

    Uses Q13_CANONICAL_CARDS[condition] from config for classification.

    Returns:
        parsed_ok:       bool
        parse_error:     str | None
        cards_selected:  sorted list of matched card tokens (uppercase)
        correct:         bool — matches canonical correct set
        human_like_error: bool — matches canonical human-like-error set
        other_error:     bool — parsed_ok but neither correct nor human_like_error
        raw_json:        the raw parsed dict
    """
    result: dict = {
        "parsed_ok": False,
        "parse_error": None,
        "cards_selected": None,
        "correct": None,
        "human_like_error": None,
        "other_error": None,
        "raw_json": None,
    }

    data = _extract_json(text)
    if data is None:
        result["parse_error"] = "no JSON found"
        return result
    result["raw_json"] = data

    choice_val = None
    for k, v in data.items():
        if k.strip().upper() == "CHOICE":
            choice_val = v
            break

    if choice_val is None:
        result["parse_error"] = "missing Choice field"
        return result

    # Normalise to a single string for regex extraction
    if isinstance(choice_val, list):
        choice_str = " ".join(str(c) for c in choice_val)
    else:
        choice_str = str(choice_val)

    card_set = _extract_q13_cards(choice_str, condition)

    if not card_set:
        result["parse_error"] = f"no valid card tokens found in Choice: {choice_str!r}"
        return result

    canonical = Q13_CANONICAL_CARDS[condition]
    correct = card_set == canonical["correct"]
    human_like_error = card_set == canonical["human_like_error"]

    result["cards_selected"] = sorted(card_set)
    result["correct"] = correct
    result["human_like_error"] = human_like_error
    result["other_error"] = not correct and not human_like_error
    result["parsed_ok"] = True
    return result


# ── Dispatch ───────────────────────────────────────────────────────────────────

def parse_response(experiment: str, condition: str, text: str) -> dict:
    """Dispatch to the right parser for a given experiment and condition."""
    if experiment == "Q1":
        return parse_q1(text, condition)
    if experiment == "Q4":
        return parse_q4(text, condition)
    if experiment == "Q5":
        return parse_q5(text, condition)
    if experiment == "Q13":
        return parse_q13(text, condition)
    raise ValueError(f"Unknown experiment: {experiment!r}")


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_q1_conditions_0ab():
    # Human-like: A→B, B→A
    r = parse_q1('{"Scenario A": {"Choice": "B"}, "Scenario B": {"Choice": "A"}}', "0")
    assert r["parsed_ok"] and r["human_like"] is True

    # Non-human-like
    r = parse_q1('{"Scenario A": {"Choice": "A"}, "Scenario B": {"Choice": "A"}}', "A")
    assert r["parsed_ok"] and r["human_like"] is False

    # Fenced JSON
    r = parse_q1('```json\n{"Scenario A": {"Choice": "B"}, "Scenario B": {"Choice": "A"}}\n```', "B")
    assert r["parsed_ok"] and r["human_like"] is True

    # Preamble text
    r = parse_q1('Sure: {"Scenario A": {"Choice": "B"}, "Scenario B": {"Choice": "A"}}', "0")
    assert r["parsed_ok"] and r["human_like"] is True

    # "Option B" / "Option A" variant
    r = parse_q1('{"Scenario A": {"Choice": "Option B"}, "Scenario B": {"Choice": "Option A"}}', "0")
    assert r["parsed_ok"] and r["human_like"] is True

    # Lowercase keys and values
    r = parse_q1('{"scenario a": {"choice": "b"}, "scenario b": {"choice": "a"}}', "0")
    assert r["parsed_ok"] and r["human_like"] is True

    # Missing Choice field
    r = parse_q1('{"Scenario A": {"Confidence": 80}, "Scenario B": {"Choice": "A"}}', "0")
    assert not r["parsed_ok"] and "Choice" in r["parse_error"]

    # No JSON
    r = parse_q1("no json here", "0")
    assert not r["parsed_ok"] and r["parse_error"] == "no JSON found"


def test_q1_condition_c():
    # Human-like: A→certain amount, B→gamble
    r = parse_q1(
        '{"Scenario A": {"Choice": "the certain amount"}, "Scenario B": {"Choice": "the gamble"}}',
        "C",
    )
    assert r["parsed_ok"] and r["human_like"] is True
    assert r["scenario_a_choice"] == "the certain amount"
    assert r["scenario_b_choice"] == "the gamble"

    # Non-human-like (reversed)
    r = parse_q1(
        '{"Scenario A": {"Choice": "the gamble"}, "Scenario B": {"Choice": "the certain amount"}}',
        "C",
    )
    assert r["parsed_ok"] and r["human_like"] is False

    # Case-insensitive
    r = parse_q1(
        '{"Scenario A": {"Choice": "The Certain Amount"}, "Scenario B": {"Choice": "THE GAMBLE"}}',
        "C",
    )
    assert r["parsed_ok"] and r["human_like"] is True

    # Missing field still errors
    r = parse_q1('{"Scenario A": {}, "Scenario B": {"Choice": "the gamble"}}', "C")
    assert not r["parsed_ok"]


def test_q4_conditions_0ab():
    r = parse_q4('{"Scenario A": {"Choice": "Yes"}, "Scenario B": {"Choice": "No"}}', "0")
    assert r["parsed_ok"] and r["human_like"] is True

    r = parse_q4('{"Scenario A": {"Choice": "yes"}, "Scenario B": {"Choice": "no"}}', "A")
    assert r["parsed_ok"] and r["human_like"] is True

    r = parse_q4('{"Scenario A": {"Choice": "No"}, "Scenario B": {"Choice": "Yes"}}', "B")
    assert r["parsed_ok"] and r["human_like"] is False

    r = parse_q4("no json", "0")
    assert not r["parsed_ok"]


def test_q4_condition_c():
    # Human-like: A→make the trip, B→don't make the trip (straight apostrophe)
    r = parse_q4(
        '{"Scenario A": {"Choice": "make the trip"}, "Scenario B": {"Choice": "don\'t make the trip"}}',
        "C",
    )
    assert r["parsed_ok"] and r["human_like"] is True

    # Curly apostrophe (\u2019)
    r = parse_q4(
        '{"Scenario A": {"Choice": "make the trip"}, "Scenario B": {"Choice": "don\u2019t make the trip"}}',
        "C",
    )
    assert r["parsed_ok"] and r["human_like"] is True
    assert r["scenario_b_choice"] == "don't make the trip"  # normalised to straight

    # Non-human-like (reversed)
    r = parse_q4(
        '{"Scenario A": {"Choice": "don\'t make the trip"}, "Scenario B": {"Choice": "make the trip"}}',
        "C",
    )
    assert r["parsed_ok"] and r["human_like"] is False

    # Case-insensitive
    r = parse_q4(
        '{"Scenario A": {"Choice": "Make The Trip"}, "Scenario B": {"Choice": "Don\'t Make The Trip"}}',
        "C",
    )
    assert r["parsed_ok"] and r["human_like"] is True


def test_q5_conditions_0a():
    r = parse_q5('{"Scenario A": {"Choice": "A"}, "Scenario B": {"Choice": "B"}}', "0")
    assert r["parsed_ok"] and r["human_like"] is True

    r = parse_q5('{"Scenario A": {"Choice": "B"}, "Scenario B": {"Choice": "B"}}', "A")
    assert r["parsed_ok"] and r["human_like"] is False

    r = parse_q5('```json\n{"Scenario A": {"Choice": "A"}, "Scenario B": {"Choice": "B"}}\n```', "0")
    assert r["parsed_ok"] and r["human_like"] is True


def test_q5_conditions_bc():
    # Human-like: A→sooner, B→later
    r = parse_q5(
        '{"Scenario A": {"Choice": "the sooner payment"}, "Scenario B": {"Choice": "the later payment"}}',
        "B",
    )
    assert r["parsed_ok"] and r["human_like"] is True

    r = parse_q5(
        '{"Scenario A": {"Choice": "the sooner payment"}, "Scenario B": {"Choice": "the later payment"}}',
        "C",
    )
    assert r["parsed_ok"] and r["human_like"] is True

    # Case-insensitive
    r = parse_q5(
        '{"Scenario A": {"Choice": "The Sooner Payment"}, "Scenario B": {"Choice": "The Later Payment"}}',
        "B",
    )
    assert r["parsed_ok"] and r["human_like"] is True

    # Non-human-like
    r = parse_q5(
        '{"Scenario A": {"Choice": "the later payment"}, "Scenario B": {"Choice": "the sooner payment"}}',
        "C",
    )
    assert r["parsed_ok"] and r["human_like"] is False


def test_q13_condition_0():
    # Correct: E and 7
    r = parse_q13('{"Choice": ["E", "7"], "Confidence": 90}', "0")
    assert r["parsed_ok"] and r["correct"] is True and r["human_like_error"] is False

    # Human-like error: E and 4
    r = parse_q13('{"Choice": ["E", "4"]}', "0")
    assert r["parsed_ok"] and r["correct"] is False and r["human_like_error"] is True and r["other_error"] is False

    # Other wrong answer
    r = parse_q13('{"Choice": ["K", "7"]}', "0")
    assert r["parsed_ok"] and r["correct"] is False and r["human_like_error"] is False and r["other_error"] is True

    # Comma-separated string
    r = parse_q13('{"Choice": "E, 7"}', "0")
    assert r["parsed_ok"] and r["correct"] is True

    # Natural prose in Choice value
    r = parse_q13('{"Choice": "the E card and the 7 card"}', "0")
    assert r["parsed_ok"] and r["correct"] is True

    # Lowercase
    r = parse_q13('{"choice": ["e", "7"]}', "0")
    assert r["parsed_ok"] and r["correct"] is True

    # Fenced JSON
    r = parse_q13('```json\n{"Choice": ["E", "7"]}\n```', "0")
    assert r["parsed_ok"] and r["correct"] is True

    # Missing Choice field
    r = parse_q13('{"Confidence": 50}', "0")
    assert not r["parsed_ok"] and r["parse_error"] == "missing Choice field"

    # No JSON at all
    r = parse_q13("I would choose E and 7.", "0")
    assert not r["parsed_ok"] and r["parse_error"] == "no JSON found"


def test_q13_condition_a():
    # cards={"U","M","6","3"}, correct={"U","3"}, human_like_error={"U","6"}
    r = parse_q13('{"Choice": ["U", "3"]}', "A")
    assert r["parsed_ok"] and r["correct"] is True

    r = parse_q13('{"Choice": "U and 3"}', "A")
    assert r["parsed_ok"] and r["correct"] is True

    r = parse_q13('{"Choice": ["U", "6"]}', "A")
    assert r["parsed_ok"] and r["human_like_error"] is True

    r = parse_q13('{"Choice": "u, 3"}', "A")
    assert r["parsed_ok"] and r["correct"] is True


def test_q13_condition_b_two_char_token():
    """Condition B has card "83" — must not be split into "8" and "3"."""
    # cards={"I","Q","8","83"}, correct={"I","83"}, human_like_error={"I","8"}

    # List format
    r = parse_q13('{"Choice": ["I", "83"]}', "B")
    assert r["parsed_ok"] and r["correct"] is True
    assert set(r["cards_selected"]) == {"I", "83"}

    # "I, 83"
    r = parse_q13('{"Choice": "I, 83"}', "B")
    assert r["parsed_ok"] and r["correct"] is True

    # "I and 83"
    r = parse_q13('{"Choice": "I and 83"}', "B")
    assert r["parsed_ok"] and r["correct"] is True

    # Natural prose
    r = parse_q13('{"Choice": "Cards I and 83 must be turned over"}', "B")
    assert r["parsed_ok"] and r["correct"] is True

    # "83" alone — neither correct nor human_like_error
    r = parse_q13('{"Choice": "83"}', "B")
    assert r["parsed_ok"] and r["other_error"] is True
    assert set(r["cards_selected"]) == {"83"}

    # Over-inclusion: I, 8, 83 → {I, 8, 83}
    r = parse_q13('{"Choice": "I, 8, 83"}', "B")
    assert r["parsed_ok"] and r["other_error"] is True
    assert set(r["cards_selected"]) == {"I", "8", "83"}

    # Human-like error: I and 8 (not 83)
    r = parse_q13('{"Choice": ["I", "8"]}', "B")
    assert r["parsed_ok"] and r["human_like_error"] is True

    # Lowercase
    r = parse_q13('{"Choice": "i, 83"}', "B")
    assert r["parsed_ok"] and r["correct"] is True

    # Mixed case
    r = parse_q13('{"Choice": "i and 83"}', "B")
    assert r["parsed_ok"] and r["correct"] is True


def test_q13_condition_c():
    # Condition C uses same cards as 0: {"E","K","4","7"}
    r = parse_q13('{"Choice": ["E", "7"]}', "C")
    assert r["parsed_ok"] and r["correct"] is True

    r = parse_q13('{"Choice": ["E", "4"]}', "C")
    assert r["parsed_ok"] and r["human_like_error"] is True


def test_q13_unparseable():
    r = parse_q13("The model refuses to answer.", "0")
    assert not r["parsed_ok"]

    r = parse_q13('{"Choice": []}', "0")
    assert not r["parsed_ok"] and "no valid card tokens" in r["parse_error"]

    r = parse_q13('{"Choice": "no cards here at all"}', "0")
    assert not r["parsed_ok"] and "no valid card tokens" in r["parse_error"]


def test_dispatch():
    r = parse_response("Q1", "0", '{"Scenario A": {"Choice": "B"}, "Scenario B": {"Choice": "A"}}')
    assert r["parsed_ok"] and r["human_like"] is True

    r = parse_response("Q13", "B", '{"Choice": ["I", "83"]}')
    assert r["parsed_ok"] and r["correct"] is True


if __name__ == "__main__":
    test_q1_conditions_0ab()
    test_q1_condition_c()
    test_q4_conditions_0ab()
    test_q4_condition_c()
    test_q5_conditions_0a()
    test_q5_conditions_bc()
    test_q13_condition_0()
    test_q13_condition_a()
    test_q13_condition_b_two_char_token()
    test_q13_condition_c()
    test_q13_unparseable()
    test_dispatch()
    print("All parser tests passed.")
