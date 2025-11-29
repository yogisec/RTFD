"""Token counting utilities for response size tracking."""

from __future__ import annotations

import tiktoken
from typing import Any


# Use cl100k_base encoding (used by GPT-4, Claude, and most modern LLMs)
_encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """
    Count tokens in a string using tiktoken's cl100k_base encoding.

    Args:
        text: String to count tokens in

    Returns:
        Number of tokens
    """
    return len(_encoding.encode(text))


def calculate_token_stats(
    json_text: str, toon_text: str, active_format: str
) -> dict[str, Any]:
    """
    Calculate comprehensive token statistics comparing JSON and TOON formats.

    Args:
        json_text: Serialized data in JSON format
        toon_text: Serialized data in TOON format
        active_format: Which format is being returned ("json" or "toon")

    Returns:
        Dictionary with token statistics:
        {
            "tokens_json": int,
            "tokens_toon": int,
            "tokens_sent": int,  # actual tokens in response
            "format": str,  # "json" or "toon"
            "savings_tokens": int,  # how many tokens TOON saves
            "savings_percent": float,  # percentage saved
            "bytes_json": int,
            "bytes_toon": int
        }
    """
    json_tokens = count_tokens(json_text)
    toon_tokens = count_tokens(toon_text)

    savings_tokens = json_tokens - toon_tokens
    savings_percent = (
        (savings_tokens / json_tokens * 100) if json_tokens > 0 else 0.0
    )

    return {
        "tokens_json": json_tokens,
        "tokens_toon": toon_tokens,
        "tokens_sent": toon_tokens if active_format == "toon" else json_tokens,
        "format": active_format,
        "savings_tokens": savings_tokens,
        "savings_percent": round(savings_percent, 2),
        "bytes_json": len(json_text),
        "bytes_toon": len(toon_text),
    }
