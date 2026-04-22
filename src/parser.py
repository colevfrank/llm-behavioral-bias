"""Response parsing and outcome classification for Q1, Q4, Q5, Q13.

All parse_* functions:
  - Never raise on malformed input
  - Return a dict always containing `parsed_ok` (bool) and `parse_error` (str|None)
  - Normalise choice values: strip whitespace, uppercase, "OPTION A" → "A"
"""

import json
import re


# ── Normalisation ──────────────────────────────────────────────────────────────

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
    # 1. After fence stripping
    cleaned = _strip_fence(text)
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. Scan for first {...} block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def _norm_choice(value: object) -> str:
    """Normalise a choice value to a clean uppercase string.

    Examples:
        "  option A "  →  "A"
        "option b"     →  "B"
        "yes"          →  "YES"
        "no"           →  "NO"
        "A"            →  "A"
        1              →  "1"
    """
    s = str(value).strip().upper()
    # "OPTION X" → "X"
    s = re.sub(r"^OPTION\s+", "", s)
    return s


def _get_scenario(data: dict, key_variants: list[str]) -> dict | None:
    """Case-insensitive dict lookup for a scenario sub-dict."""
    for k in data:
        if k.strip().upper() in [v.upper() for v in key_variants]:
            v = data[k]
            if isinstance(v, dict):
                return v
    return None


def _get_choice(scenario: dict) -> str | None:
    """Extract the Choice field from a scenario dict, normalised."""
    for k in scenario:
        if k.strip().upper() == "CHOICE":
            return _norm_choice(scenario[k])
    return None


# ── Per-experiment parsers ─────────────────────────────────────────────────────

def parse_q1(text: str) -> dict:
    """Parse Q1 (diminishing sensitivity).

    Expected JSON structure:
        {"Scenario A": {"Choice": "A"|"B", ...}, "Scenario B": {"Choice": "A"|"B", ...}}

    human_like: scenario_a_choice == "B" AND scenario_b_choice == "A"
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

    ca = _get_choice(sa)
    cb = _get_choice(sb)

    if ca is None:
        result["parse_error"] = "missing Choice in Scenario A"
        return result
    if cb is None:
        result["parse_error"] = "missing Choice in Scenario B"
        return result

    result["scenario_a_choice"] = ca
    result["scenario_b_choice"] = cb
    result["human_like"] = (ca == "B") and (cb == "A")
    result["parsed_ok"] = True
    return result


def parse_q4(text: str) -> dict:
    """Parse Q4 (narrow framing).

    Expected JSON structure:
        {"Scenario A": {"Choice": "Yes"|"No", ...}, "Scenario B": {"Choice": "Yes"|"No", ...}}

    human_like: scenario_a_choice == "YES" AND scenario_b_choice == "NO"
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

    ca = _get_choice(sa)
    cb = _get_choice(sb)

    if ca is None:
        result["parse_error"] = "missing Choice in Scenario A"
        return result
    if cb is None:
        result["parse_error"] = "missing Choice in Scenario B"
        return result

    result["scenario_a_choice"] = ca
    result["scenario_b_choice"] = cb
    result["human_like"] = (ca == "YES") and (cb == "NO")
    result["parsed_ok"] = True
    return result


def parse_q5(text: str) -> dict:
    """Parse Q5 (hyperbolic discounting).

    Expected JSON structure:
        {"Scenario A": {"Choice": "A"|"B", ...}, "Scenario B": {"Choice": "A"|"B", ...}}

    human_like: scenario_a_choice == "A" AND scenario_b_choice == "B"
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

    ca = _get_choice(sa)
    cb = _get_choice(sb)

    if ca is None:
        result["parse_error"] = "missing Choice in Scenario A"
        return result
    if cb is None:
        result["parse_error"] = "missing Choice in Scenario B"
        return result

    result["scenario_a_choice"] = ca
    result["scenario_b_choice"] = cb
    result["human_like"] = (ca == "A") and (cb == "B")
    result["parsed_ok"] = True
    return result


def parse_q13(text: str, canonical_vowel: str, canonical_odd: str, canonical_even: str) -> dict:
    """Parse Q13 (Wason selection task).

    Expected JSON structure (flat):
        {"Choice": ["E", "4"], "Confidence": ..., "Explanation": ..., "Reasoning": ...}

    Args:
        canonical_vowel: The "vowel" card for this condition (e.g. "E")
        canonical_odd:   The "odd" card for this condition (e.g. "7")
        canonical_even:  The "even" card for this condition (e.g. "4")

    Returns:
        parsed_ok, selected_cards (list[str]), correct (bool), human_like_error (bool)
    """
    result: dict = {
        "parsed_ok": False,
        "parse_error": None,
        "selected_cards": None,
        "correct": None,
        "human_like_error": None,
        "raw_json": None,
    }

    data = _extract_json(text)
    if data is None:
        result["parse_error"] = "no JSON found"
        return result
    result["raw_json"] = data

    # Find "Choice" key (case-insensitive)
    choice_val = None
    for k in data:
        if k.strip().upper() == "CHOICE":
            choice_val = data[k]
            break

    if choice_val is None:
        result["parse_error"] = "missing Choice field"
        return result

    # Choice may be a list or a comma-separated string
    if isinstance(choice_val, list):
        cards = [_norm_choice(c) for c in choice_val]
    elif isinstance(choice_val, str):
        # Try splitting on commas or spaces
        parts = re.split(r"[,\s]+", choice_val.strip())
        cards = [_norm_choice(p) for p in parts if p]
    else:
        result["parse_error"] = f"unexpected Choice type: {type(choice_val)}"
        return result

    if not cards:
        result["parse_error"] = "empty Choice list"
        return result

    cv = canonical_vowel.strip().upper()
    co = canonical_odd.strip().upper()
    ce = canonical_even.strip().upper()

    card_set = set(cards)
    result["selected_cards"] = cards
    result["correct"] = card_set == {cv, co}
    result["human_like_error"] = card_set == {cv, ce}
    result["parsed_ok"] = True
    return result


# ── Dispatch ───────────────────────────────────────────────────────────────────

PARSERS = {
    "Q1": parse_q1,
    "Q4": parse_q4,
    "Q5": parse_q5,
}


def parse_response(experiment: str, text: str, q13_canonical: tuple[str, str, str] | None = None) -> dict:
    """Dispatch to the right parser.

    For Q13, q13_canonical must be (vowel, odd, even).
    """
    if experiment == "Q13":
        if q13_canonical is None:
            raise ValueError("q13_canonical required for Q13")
        return parse_q13(text, *q13_canonical)
    if experiment not in PARSERS:
        raise ValueError(f"Unknown experiment: {experiment}")
    return PARSERS[experiment](text)


# ── Tests ──────────────────────────────────────────────────────────────────────

def _test_q1():
    # Clean JSON
    r = parse_q1('{"Scenario A": {"Choice": "B", "Confidence": 80}, "Scenario B": {"Choice": "A", "Confidence": 70}}')
    assert r["parsed_ok"], r
    assert r["human_like"] is True
    assert r["scenario_a_choice"] == "B"
    assert r["scenario_b_choice"] == "A"

    # Non-human-like
    r = parse_q1('{"Scenario A": {"Choice": "A"}, "Scenario B": {"Choice": "A"}}')
    assert r["parsed_ok"]
    assert r["human_like"] is False

    # Fenced JSON
    r = parse_q1('Here is my answer:\n```json\n{"Scenario A": {"Choice": "B"}, "Scenario B": {"Choice": "A"}}\n```')
    assert r["parsed_ok"]
    assert r["human_like"] is True

    # Preamble text before JSON
    r = parse_q1('After careful thought: {"Scenario A": {"Choice": "B"}, "Scenario B": {"Choice": "A"}}')
    assert r["parsed_ok"]
    assert r["human_like"] is True

    # Option A / Option B variant
    r = parse_q1('{"Scenario A": {"Choice": "Option B"}, "Scenario B": {"Choice": "Option A"}}')
    assert r["parsed_ok"]
    assert r["human_like"] is True

    # Missing field
    r = parse_q1('{"Scenario A": {"Confidence": 80}, "Scenario B": {"Choice": "A"}}')
    assert not r["parsed_ok"]
    assert "Choice" in r["parse_error"]

    # Malformed input
    r = parse_q1("This is just some text with no JSON at all.")
    assert not r["parsed_ok"]
    assert r["parse_error"] == "no JSON found"

    # Lowercase keys
    r = parse_q1('{"scenario a": {"choice": "b"}, "scenario b": {"choice": "a"}}')
    assert r["parsed_ok"]
    assert r["human_like"] is True

    print("Q1 tests passed")


def _test_q4():
    r = parse_q4('{"Scenario A": {"Choice": "Yes"}, "Scenario B": {"Choice": "No"}}')
    assert r["parsed_ok"]
    assert r["human_like"] is True

    r = parse_q4('{"Scenario A": {"Choice": "yes"}, "Scenario B": {"Choice": "no"}}')
    assert r["parsed_ok"]
    assert r["human_like"] is True

    r = parse_q4('{"Scenario A": {"Choice": "No"}, "Scenario B": {"Choice": "Yes"}}')
    assert r["parsed_ok"]
    assert r["human_like"] is False

    r = parse_q4("no json here")
    assert not r["parsed_ok"]

    print("Q4 tests passed")


def _test_q5():
    r = parse_q5('{"Scenario A": {"Choice": "A"}, "Scenario B": {"Choice": "B"}}')
    assert r["parsed_ok"]
    assert r["human_like"] is True

    r = parse_q5('{"Scenario A": {"Choice": "B"}, "Scenario B": {"Choice": "B"}}')
    assert r["parsed_ok"]
    assert r["human_like"] is False

    r = parse_q5('```json\n{"Scenario A": {"Choice": "A"}, "Scenario B": {"Choice": "B"}}\n```')
    assert r["parsed_ok"]
    assert r["human_like"] is True

    print("Q5 tests passed")


def _test_q13():
    cv, co, ce = "E", "7", "4"

    # Correct answer (E and 7)
    r = parse_q13('{"Choice": ["E", "7"], "Confidence": 90}', cv, co, ce)
    assert r["parsed_ok"]
    assert r["correct"] is True
    assert r["human_like_error"] is False

    # Human-like error (E and 4)
    r = parse_q13('{"Choice": ["E", "4"]}', cv, co, ce)
    assert r["parsed_ok"]
    assert r["correct"] is False
    assert r["human_like_error"] is True

    # Other wrong answer
    r = parse_q13('{"Choice": ["K", "7"]}', cv, co, ce)
    assert r["parsed_ok"]
    assert r["correct"] is False
    assert r["human_like_error"] is False

    # Comma-separated string
    r = parse_q13('{"Choice": "E, 7"}', cv, co, ce)
    assert r["parsed_ok"]
    assert r["correct"] is True

    # Lowercase
    r = parse_q13('{"choice": ["e", "7"]}', cv, co, ce)
    assert r["parsed_ok"]
    assert r["correct"] is True

    # Fenced
    r = parse_q13('```json\n{"Choice": ["E", "7"]}\n```', cv, co, ce)
    assert r["parsed_ok"]
    assert r["correct"] is True

    # Missing field
    r = parse_q13('{"Confidence": 50}', cv, co, ce)
    assert not r["parsed_ok"]

    # No JSON
    r = parse_q13("I would choose E and 7.", cv, co, ce)
    assert not r["parsed_ok"]

    print("Q13 tests passed")


if __name__ == "__main__":
    _test_q1()
    _test_q4()
    _test_q5()
    _test_q13()
    print("All parser tests passed.")
