#!/usr/bin/env python3
"""Generate docs/modules/*.md from plugins/modules/*.py DOCUMENTATION blocks.

Ensures docs/modules/ is always in sync with module source code and never drifts.
Usage:
    python scripts/generate_docs.py         # Regenerates docs
    python scripts/generate_docs.py --check # Verifies docs are in sync, exits 1 on drift
"""

import argparse
import re
import sys
from pathlib import Path

import yaml


def clean_ansible_markup(text: str) -> str:
    """Convert Ansible doc markup like C(...) or B(...) to markdown."""
    text = re.sub(r"[CB]\(([^)]+)\)", r"`\1`", text)
    text = re.sub(r"[I]\(([^)]+)\)", r"*\1*", text)
    text = re.sub(r"[U]\(([^)]+)\)", r"<\1>", text)
    return text


def format_description(desc) -> str:
    if isinstance(desc, list):
        return " ".join(clean_ansible_markup(str(line).strip()) for line in desc)
    return clean_ansible_markup(str(desc).strip())


def generate_module_doc(py_path: Path) -> str:
    content = py_path.read_text(encoding="utf-8")

    doc_match = re.search(r"DOCUMENTATION\s*=\s*r?['\"]{3}(.*?)['\"]{3}", content, re.DOTALL)
    if not doc_match:
        return ""

    doc = yaml.safe_load(doc_match.group(1))
    module_name = doc.get("module", py_path.stem)
    short_desc = clean_ansible_markup(doc.get("short_description", "").strip())

    description_raw = doc.get("description", [])
    if isinstance(description_raw, list):
        desc_paragraphs = [clean_ansible_markup(line) for line in description_raw]
        description = "\n\n".join(desc_paragraphs)
    else:
        description = clean_ansible_markup(str(description_raw).strip())

    lines = [
        f"# hellqvio86.unifi.{module_name}",
        "",
        short_desc,
        "",
        "## Description",
        description,
        "",
        "## Parameters",
        "",
        "| Parameter | Type | Required | Default | Description |",
        "|-----------|------|----------|---------|-------------|",
    ]

    options = doc.get("options", {})
    if isinstance(options, dict):
        # List module parameters
        for opt_name, opt_meta in options.items():
            if not isinstance(opt_meta, dict):
                opt_meta = {}
            opt_type = opt_meta.get("type", "str")
            req = "Yes" if opt_meta.get("required") else "No"
            default = opt_meta.get("default")
            default_str = f"`{default}`" if default is not None else ""
            desc = format_description(opt_meta.get("description", ""))
            choices = opt_meta.get("choices")
            if choices:
                choices_str = ", ".join(f"`{c}`" for c in choices)
                desc += f" Choices: {choices_str}."
            # Escape pipes in markdown table
            desc = desc.replace("|", "\\|")
            lines.append(f"| `{opt_name}` | {opt_type} | {req} | {default_str} | {desc} |")

    # Check for EXAMPLES
    examples_match = re.search(r"EXAMPLES\s*=\s*r?['\"]{3}(.*?)['\"]{3}", content, re.DOTALL)
    if examples_match:
        ex_content = examples_match.group(1).strip()
        lines.extend(["", "## Examples", "", "```yaml", ex_content, "```"])

    # Check for RETURN
    return_match = re.search(r"RETURN\s*=\s*r?['\"]{3}(.*?)['\"]{3}", content, re.DOTALL)
    if return_match:
        try:
            ret_data = yaml.safe_load(return_match.group(1))
            if isinstance(ret_data, dict) and ret_data:
                lines.extend(
                    [
                        "",
                        "## Return Values",
                        "",
                        "| Return Value | Type | Returned | Description |",
                        "|--------------|------|----------|-------------|",
                    ]
                )
                for ret_name, ret_meta in ret_data.items():
                    if isinstance(ret_meta, dict):
                        r_type = ret_meta.get("type", "")
                        r_ret = ret_meta.get("returned", "always")
                        r_desc = format_description(ret_meta.get("description", "")).replace("|", "\\|")
                        lines.append(f"| `{ret_name}` | {r_type} | {r_ret} | {r_desc} |")
        except Exception:
            pass

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify module documentation")
    parser.add_argument("--check", action="store_true", help="Check if docs are up to date without modifying")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    modules_dir = repo_root / "plugins" / "modules"
    docs_dir = repo_root / "docs" / "modules"
    docs_dir.mkdir(parents=True, exist_ok=True)

    has_drift = False

    for py_file in sorted(modules_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        doc_content = generate_module_doc(py_file)
        if not doc_content:
            continue

        target_file = docs_dir / f"{py_file.stem}.md"

        if args.check:
            if not target_file.exists():
                print(f"Drift detected: {target_file} is missing.", file=sys.stderr)
                has_drift = True
            else:
                existing = target_file.read_text(encoding="utf-8")
                if existing != doc_content:
                    print(f"Drift detected: {target_file} differs from {py_file.name} DOCUMENTATION.", file=sys.stderr)
                    has_drift = True
        else:
            target_file.write_text(doc_content, encoding="utf-8")
            print(f"Generated {target_file.relative_to(repo_root)}")

    if args.check:
        if has_drift:
            print(
                "\nError: Documentation is out of sync. Run 'python scripts/generate_docs.py' to update.",
                file=sys.stderr,
            )
            return 1
        print("OK: All module documentation is in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
