"""Configuration generator for defer_loading client settings.

This module provides utilities to generate MCP client configurations with
defer_loading recommendations based on tool tier classifications.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Any

from .server import get_all_tool_tiers


def get_tools_by_tier() -> dict[int, list[str]]:
    """
    Get all tools organized by their tier.

    Returns:
        Dictionary mapping tier number to list of tool names.
    """
    all_tiers = get_all_tool_tiers()
    tools_by_tier: dict[int, list[str]] = {}

    for tool_name, tier_info in all_tiers.items():
        if tier_info.tier not in tools_by_tier:
            tools_by_tier[tier_info.tier] = []
        tools_by_tier[tier_info.tier].append(tool_name)

    # Sort tools within each tier
    for tools in tools_by_tier.values():
        tools.sort()

    return tools_by_tier


def get_all_tools_with_tiers() -> dict[str, dict[str, Any]]:
    """
    Get all tools with their tier information.

    Returns:
        Dictionary mapping tool names to their tier info as dicts.
    """
    all_tiers = get_all_tool_tiers()
    return {name: asdict(info) for name, info in all_tiers.items()}


def generate_claude_desktop_config(
    defer_tiers: list[int] | None = None,
    command: str = "uvx",
    args: list[str] | None = None,
) -> dict[str, Any]:
    """
    Generate Claude Desktop configuration with defer_loading settings.

    Args:
        defer_tiers: List of tiers to defer (default: [2, 3, 4, 5, 6])
        command: Command to run rtfd (default: "uvx")
        args: Arguments for the command (default: ["rtfd-mcp"])

    Returns:
        Claude Desktop MCP server configuration dict.
    """
    if defer_tiers is None:
        defer_tiers = [2, 3, 4, 5, 6]
    if args is None:
        args = ["rtfd-mcp"]

    all_tiers = get_all_tool_tiers()

    # Build per-tool config overrides
    tool_configs = {}
    for tool_name, tier_info in all_tiers.items():
        # Only include tools that should NOT be deferred (tier not in defer_tiers)
        if tier_info.tier not in defer_tiers:
            tool_configs[tool_name] = {"defer_loading": False}

    config = {
        "mcpServers": {
            "rtfd": {
                "command": command,
                "args": args,
                "type": "mcp_toolset",
                "default_config": {"defer_loading": True},
                "configs": tool_configs,
            }
        }
    }

    return config


def generate_api_config(defer_tiers: list[int] | None = None) -> dict[str, Any]:
    """
    Generate Anthropic API configuration with defer_loading settings.

    Args:
        defer_tiers: List of tiers to defer (default: [2, 3, 4, 5, 6])

    Returns:
        API-style configuration dict for tool configs.
    """
    if defer_tiers is None:
        defer_tiers = [2, 3, 4, 5, 6]

    all_tiers = get_all_tool_tiers()

    # Build tool configurations
    tool_configs = {}
    for tool_name, tier_info in all_tiers.items():
        tool_configs[tool_name] = {
            "defer_loading": tier_info.tier in defer_tiers,
            "tier": tier_info.tier,
            "category": tier_info.category,
        }

    return {
        "description": "rtfd MCP tool configurations for Anthropic API",
        "defer_loading_note": (
            "Set defer_loading=true in your MCP server config for tools you want to defer. "
            "Tools with defer_loading=false are recommended to always be loaded."
        ),
        "tools": tool_configs,
    }


def generate_tier_summary() -> dict[str, Any]:
    """
    Generate a summary of all tool tiers.

    Returns:
        Summary dict with tier descriptions and tool lists.
    """
    tier_descriptions = {
        1: "Core - Always loaded, essential for basic functionality",
        2: "Frequent - Commonly used tools",
        3: "Regular - Standard tools for common workflows",
        4: "Situational - Tools for specific use cases",
        5: "Niche - Specialized tools for rare needs",
        6: "Admin - Cache and admin utilities",
    }

    tools_by_tier = get_tools_by_tier()

    summary = {
        "description": "rtfd tool tier classification for defer_loading optimization",
        "recommendation": "Defer tiers 2-6 for ~93% token reduction (2 tools always loaded)",
        "tiers": {},
    }

    for tier in sorted(tools_by_tier.keys()):
        summary["tiers"][tier] = {
            "description": tier_descriptions.get(tier, f"Tier {tier}"),
            "defer_recommended": tier > 1,
            "tool_count": len(tools_by_tier[tier]),
            "tools": tools_by_tier[tier],
        }

    return summary


def cli() -> None:
    """Command-line interface for config generator."""
    parser = argparse.ArgumentParser(
        description="Generate rtfd MCP configuration for defer_loading optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rtfd-config --format claude-desktop > claude_desktop_config.json
  rtfd-config --format api --defer-tiers 3,4,5,6
  rtfd-config --format summary
  rtfd-config --format tiers

Formats:
  claude-desktop  Generate Claude Desktop MCP server configuration
  api             Generate Anthropic API tool configurations
  summary         Generate tier summary with tool lists
  tiers           Same as summary (alias)
  tools           List all tools with their tier info
        """,
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["claude-desktop", "api", "summary", "tiers", "tools"],
        default="summary",
        help="Output format (default: summary)",
    )

    parser.add_argument(
        "--defer-tiers",
        "-d",
        type=str,
        default="2,3,4,5,6",
        help="Comma-separated list of tiers to defer (default: 2,3,4,5,6)",
    )

    parser.add_argument(
        "--command",
        "-c",
        type=str,
        default="uvx",
        help="Command to run rtfd (default: uvx)",
    )

    parser.add_argument(
        "--args",
        "-a",
        type=str,
        default="rtfd-mcp",
        help="Arguments for command (default: rtfd-mcp)",
    )

    parser.add_argument(
        "--pretty",
        "-p",
        action="store_true",
        default=True,
        help="Pretty print JSON output (default: True)",
    )

    parser.add_argument(
        "--compact",
        action="store_true",
        help="Compact JSON output (no pretty printing)",
    )

    args = parser.parse_args()

    # Parse defer tiers
    defer_tiers = [int(t.strip()) for t in args.defer_tiers.split(",")]

    # Parse command args
    command_args = args.args.split() if args.args else ["rtfd-mcp"]

    # Generate output based on format
    if args.format == "claude-desktop":
        output = generate_claude_desktop_config(
            defer_tiers=defer_tiers,
            command=args.command,
            args=command_args,
        )
    elif args.format == "api":
        output = generate_api_config(defer_tiers=defer_tiers)
    elif args.format in ("summary", "tiers"):
        output = generate_tier_summary()
    elif args.format == "tools":
        output = get_all_tools_with_tiers()
    else:
        parser.error(f"Unknown format: {args.format}")
        return

    # Output JSON
    indent = None if args.compact else 2
    print(json.dumps(output, indent=indent))


if __name__ == "__main__":
    cli()
