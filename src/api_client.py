"""Thin wrapper around the Anthropic SDK for single synchronous calls."""

import os
import time

import anthropic
from dotenv import load_dotenv
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.config import MODEL, TEMPERATURE

load_dotenv()


def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set. Copy .env.example to .env and fill it in.")
    return anthropic.Anthropic(api_key=api_key)


@retry(
    retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APITimeoutError)),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def call_model(
    prompt: str,
    reasoning_effort: str,
    temperature: float = TEMPERATURE,
) -> dict:
    """Make a single synchronous call to the model.

    Args:
        prompt: User message text.
        reasoning_effort: "low" or "high" — passed to adaptive thinking.
        temperature: Sampling temperature (default 0.5 per Bini et al.).

    Returns:
        dict with keys:
            raw_response: the full SDK response object
            text:         assistant text content (str)
            thinking:     summarized thinking trace (str | None)
            usage:        token usage dict
            latency_ms:   wall-clock milliseconds for the API call
    """
    client = _get_client()

    t0 = time.monotonic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        temperature=temperature,
        thinking={
            "type": "adaptive",
            "effort": reasoning_effort,
            "display": "summarized",
        },
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = int((time.monotonic() - t0) * 1000)

    text = ""
    thinking = None
    for block in response.content:
        if block.type == "thinking":
            thinking = getattr(block, "summary", None) or getattr(block, "thinking", None)
        elif block.type == "text":
            text = block.text

    return {
        "raw_response": response,
        "text": text,
        "thinking": thinking,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
            "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
        },
        "latency_ms": latency_ms,
    }
