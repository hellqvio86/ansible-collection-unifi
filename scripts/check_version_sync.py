#!/usr/bin/env python3
"""Validate that the version in galaxy.yml matches the installation example in README.md."""

import re
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent

    galaxy_path = repo_root / "galaxy.yml"
    readme_path = repo_root / "README.md"

    if not galaxy_path.exists():
        print(f"Error: {galaxy_path} not found.", file=sys.stderr)
        return 1

    if not readme_path.exists():
        print(f"Error: {readme_path} not found.", file=sys.stderr)
        return 1

    galaxy_content = galaxy_path.read_text(encoding="utf-8")
    readme_content = readme_path.read_text(encoding="utf-8")

    galaxy_match = re.search(
        r"^version:\s*['\"]?([0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?['\"]?)",
        galaxy_content,
        re.MULTILINE,
    )
    if not galaxy_match:
        print("Error: Could not find 'version:' in galaxy.yml", file=sys.stderr)
        return 1

    galaxy_version = galaxy_match.group(1).strip("'\"")

    readme_match = re.search(
        r"name:\s*hellqvio86\.unifi\s*\n\s*version:\s*['\"]?([0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?['\"]?)",
        readme_content,
    )
    if not readme_match:
        print(
            "Error: Could not find 'hellqvio86.unifi' version in README.md requirements.yml example",
            file=sys.stderr,
        )
        return 1

    readme_version = readme_match.group(1).strip("'\"")

    if galaxy_version != readme_version:
        print(
            f"Error: Version mismatch! galaxy.yml has '{galaxy_version}' "
            f"but README.md specifies '{readme_version}' in requirements.yml example.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: galaxy.yml and README.md versions match ({galaxy_version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
