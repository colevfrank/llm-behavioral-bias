"""Smoke test: one hardcoded API call to verify auth and response handling.

Run with:
    uv run python scripts/run_pilot.py
"""

import json
import sys
from pathlib import Path

# Allow imports from src/ without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api_client import call_model

SMOKE_PROMPT = "What is 2+2? Reply in JSON with field 'answer'."


def main():
    print("=== Smoke test ===")
    print(f"Prompt: {SMOKE_PROMPT!r}")
    print("Calling model ...")

    result = call_model(prompt=SMOKE_PROMPT)

    print(f"\nLatency: {result['latency_ms']} ms")
    print(f"Usage:   {result['usage']}")
    print(f"Thinking (summarized): {result['thinking']!r}")
    print(f"\nRaw text:\n{result['text']}")

    # Basic sanity check
    text = result["text"]
    try:
        data = json.loads(text.strip().strip("```json").strip("```").strip())
        answer = data.get("answer")
        print(f"\nParsed answer: {answer!r}")
        if str(answer) == "4":
            print("Auth and response handling: OK")
        else:
            print(f"Unexpected answer value: {answer!r} (not '4') — check manually")
    except Exception as e:
        print(f"Could not parse response as JSON: {e}")
        print("(The API call itself succeeded — check the raw text above)")


if __name__ == "__main__":
    main()
