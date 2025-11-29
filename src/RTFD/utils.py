"""Shared utilities for providers and server."""

from __future__ import annotations

from typing import Any

import httpx
import json
import os
from toon import encode
from mcp.types import CallToolResult, TextContent
from .token_counter import calculate_token_stats

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/118.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 15.0


def is_fetch_enabled() -> bool:
    """
    Check if documentation content fetching is enabled.

    Controlled by RTFD_FETCH environment variable (default: true).
    Set to 'false', '0', or 'no' to disable.
    """
    fetch_enabled = os.getenv("RTFD_FETCH", "true").lower()
    return fetch_enabled not in ("false", "0", "no")


async def create_http_client() -> httpx.AsyncClient:
    """
    Create a configured HTTP client for provider use.

    Centralizes timeout, user-agent, and redirect configuration.
    """
    return httpx.AsyncClient(
        timeout=DEFAULT_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )


def serialize_response(data: Any) -> str:
    """
    Convert data to string format.

    Uses JSON by default. Falls back to TOON if USE_TOON environment variable is set to 'true'.
    """
    use_toon = os.getenv("USE_TOON", "false").lower() == "true"

    if use_toon:
        return encode(data)
    return json.dumps(data)


def serialize_response_with_meta(data: Any) -> CallToolResult:
    """
    Convert data to CallToolResult with optional token statistics in _meta.

    When RTFD_TRACK_TOKENS=true (default), serializes to both JSON and TOON
    to calculate comparative stats. When false, only serializes to active format.

    Returns format specified by USE_TOON environment variable.

    Token statistics are included in _meta field, which is visible in
    Claude Code but NOT sent to the LLM (costs 0 tokens).

    Args:
        data: Python object to serialize (dict, list, etc.)

    Returns:
        CallToolResult with:
          - content: Serialized data in active format
          - _meta: Token statistics comparing JSON vs TOON (if tracking enabled)
    """
    use_toon = os.getenv("USE_TOON", "false").lower() == "true"
    track_tokens = os.getenv("RTFD_TRACK_TOKENS", "true").lower() == "true"

    active_format = "toon" if use_toon else "json"

    # If token tracking is disabled, just serialize to active format
    if not track_tokens:
        response_text = encode(data) if use_toon else json.dumps(data)
        return CallToolResult(
            content=[TextContent(type="text", text=response_text)]
        )

    # Token tracking enabled: serialize to both formats for comparison
    try:
        json_text = json.dumps(data)
        toon_text = encode(data)
        response_text = toon_text if use_toon else json_text

        # Calculate token statistics
        token_stats = calculate_token_stats(json_text, toon_text, active_format)

        # Return CallToolResult with content and metadata
        return CallToolResult(
            content=[TextContent(type="text", text=response_text)],
            _meta={"token_stats": token_stats}
        )
    except Exception as e:
        # Fallback: still return response, but with error in metadata
        response_text = encode(data) if use_toon else json.dumps(data)
        return CallToolResult(
            content=[TextContent(type="text", text=response_text)],
            _meta={"token_stats": {"error": f"Token counting failed: {str(e)}"}}
        )
