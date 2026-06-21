#!/usr/bin/env python3
import os
import re
import subprocess
import sys


def run_cmd(args, cwd=None):
    res = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    return res.stdout.strip(), res.stderr.strip(), res.returncode

def get_current_version():
    if not os.path.exists("galaxy.yml"):
        return None
    with open("galaxy.yml") as f:
        for line in f:
            if line.startswith("version:"):
                return line.split(":")[1].strip()
    return None

def get_changelog_versions():
    versions = []
    if not os.path.exists("CHANGELOG.md"):
        return versions
    with open("CHANGELOG.md") as f:
        for line in f:
            m = re.match(r"^##\s+(\d+\.\d+\.\d+)", line)
            if m:
                versions.append(m.group(1))
    return versions

def get_start_commit(prev_version):
    # 1. Check if tag v{prev_version} exists
    _, _, rc = run_cmd(["git", "rev-parse", f"v{prev_version}"])
    if rc == 0:
        return f"v{prev_version}"

    # 2. Search git log for commit that set version to prev_version
    out, _, rc = run_cmd(["git", "log", "-S", f"version: {prev_version}", "--oneline"])
    if rc == 0 and out:
        first_line = out.splitlines()[0]
        commit_hash = first_line.split()[0]
        return commit_hash

    # 3. Get the latest tag
    out, _, rc = run_cmd(["git", "describe", "--tags", "--abbrev=0"])
    if rc == 0 and out:
        return out.strip()

    # 4. Fallback to first commit
    out, _, rc = run_cmd(["git", "rev-list", "--max-parents=0", "HEAD"])
    return out.strip() if out else "HEAD"

def parse_commits(start_commit):
    out, _, rc = run_cmd(["git", "log", f"{start_commit}..HEAD", "--oneline"])
    if rc != 0 or not out:
        return []
    commits = []
    for line in out.splitlines():
        if not line:
            continue
        commit_hash = line.split()[0]
        subj, _, _ = run_cmd(["git", "show", "-s", "--format=%s", commit_hash])
        commits.append(subj)
    return commits

def categorize_commits(commits):
    # Conventional commit regex: type(scope): description
    pattern = re.compile(r"^(\w+)(?:\(([^)]+)\))?:\s*(.*)$")
    
    categories = {
        "New Features": [],
        "Bug Fixes": [],
        "Improvements": [],
        "Dependencies": [],
        "Test Coverage": [],
        "CI/CD": [],
        "Other Changes": []
    }
    
    for commit in commits:
        commit = commit.strip()
        # Skip branch merges or release bumps
        if commit.startswith("Merge pull request") or commit.startswith("Merge branch") or "bump version" in commit.lower():
            continue
            
        m = pattern.match(commit)
        if m:
            ctype, scope, desc = m.groups()
            ctype = ctype.lower()
            
            desc = desc.strip()
            if desc:
                desc = desc[0].upper() + desc[1:]
                if not desc.endswith("."):
                    desc += "."
            
            if scope:
                formatted = f"- **`{scope}`**: {desc}"
            else:
                formatted = f"- {desc}"
                
            if ctype == "feat":
                categories["New Features"].append(formatted)
            elif ctype == "fix":
                categories["Bug Fixes"].append(formatted)
            elif ctype in ["refactor", "perf"]:
                categories["Improvements"].append(formatted)
            elif ctype == "test":
                categories["Test Coverage"].append(formatted)
            elif ctype == "ci":
                categories["CI/CD"].append(formatted)
            elif ctype == "chore" and scope == "deps":
                categories["Dependencies"].append(formatted)
            elif ctype == "chore":
                # Only append non-trivial chores
                if "dependabot" not in commit.lower() and "lint" not in commit.lower():
                    categories["Other Changes"].append(formatted)
        else:
            desc = commit
            if desc:
                desc = desc[0].upper() + desc[1:]
                if not desc.endswith("."):
                    desc += "."
            categories["Other Changes"].append(f"- {desc}")
            
    return categories

def generate_section(version, categories):
    lines = [f"## {version}", ""]
    has_content = False
    
    for cat, items in categories.items():
        if items:
            has_content = True
            lines.append(f"### {cat}")
            for item in items:
                lines.append(item)
            lines.append("")
            
    if not has_content:
        lines.append("- No changes recorded.")
        lines.append("")
        
    return "\n".join(lines)

def update_changelog():
    version = get_current_version()
    if not version:
        print("Error: Could not find version in galaxy.yml")
        sys.exit(1)
        
    versions_in_log = get_changelog_versions()
    
    # Determine previous version
    if versions_in_log:
        if versions_in_log[0] == version:
            prev_version = versions_in_log[1] if len(versions_in_log) > 1 else None
        else:
            prev_version = versions_in_log[0]
    else:
        prev_version = None
        
    if not prev_version:
        start_commit = None
    else:
        start_commit = get_start_commit(prev_version)
        
    print(f"Generating changelog for version {version} since {start_commit or 'first commit'}...")
    
    if start_commit:
        commits = parse_commits(start_commit)
    else:
        out, _, _ = run_cmd(["git", "log", "--oneline"])
        commits = []
        for line in out.splitlines():
            if line:
                commit_hash = line.split()[0]
                subj, _, _ = run_cmd(["git", "show", "-s", "--format=%s", commit_hash])
                commits.append(subj)
                
    categories = categorize_commits(commits)
    new_section = generate_section(version, categories)
    
    changelog_content = ""
    if os.path.exists("CHANGELOG.md"):
        with open("CHANGELOG.md") as f:
            changelog_content = f.read()
            
    if f"## {version}" in changelog_content:
        pattern = r"(##\s+" + re.escape(version) + r".*?)(?=\n##\s+|\Z)"
        updated_content = re.sub(pattern, new_section.strip(), changelog_content, flags=re.DOTALL)
    else:
        if "# Changelog" in changelog_content:
            parts = changelog_content.split("# Changelog", 1)
            updated_content = parts[0] + "# Changelog\n\n" + new_section + parts[1].lstrip()
        else:
            updated_content = "# Changelog\n\n" + new_section + changelog_content
            
    with open("CHANGELOG.md", "w") as f:
        f.write(updated_content)
        
    print("CHANGELOG.md updated successfully.")

if __name__ == "__main__":
    update_changelog()
