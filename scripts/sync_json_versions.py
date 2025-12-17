#!/usr/bin/env python3
"""Sync version from pyproject.toml to JSON files."""

import json
import re
import sys
from pathlib import Path


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")

    content = pyproject_path.read_text()
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)


def update_json_file(path: Path, version: str):
    """Update version field in a JSON file."""
    if not path.exists():
        print(f"Warning: {path} not found, skipping")
        return

    content = json.loads(path.read_text())

    if "version" in content:
        content["version"] = version

    # specialized logic for marketplace.json which has nested plugins
    if "plugins" in content:
        for plugin in content["plugins"]:
            if "version" in plugin:
                plugin["version"] = version

    path.write_text(json.dumps(content, indent=2) + "\n")
    print(f"Updated {path} to version {version}")


def main():
    try:
        version = get_current_version()
        print(f"Syncing version {version} from pyproject.toml...")

        update_json_file(Path(".claude-plugin/plugin.json"), version)
        update_json_file(Path(".claude-plugin/marketplace.json"), version)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
