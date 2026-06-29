#!/usr/bin/env python3
"""Validate a skill directory in this repo."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}

    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_name = skill_dir.name

    if not NAME_PATTERN.match(skill_name):
        errors.append(
            f"Directory name '{skill_name}' must be lowercase letters, numbers, and hyphens only."
        )

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append("Missing required file: SKILL.md")
        return errors

    content = skill_md.read_text(encoding="utf-8")
    frontmatter = _parse_frontmatter(content)

    if not frontmatter:
        errors.append("SKILL.md must start with YAML frontmatter (--- ... ---).")
        return errors

    if frontmatter.get("name") != skill_name:
        errors.append(
            f"Frontmatter name '{frontmatter.get('name')}' must match directory '{skill_name}'."
        )

    description = frontmatter.get("description", "")
    if not description:
        errors.append("Frontmatter must include a non-empty description.")
    elif len(description) > 1024:
        errors.append("description must be 1024 characters or fewer.")

    line_count = len(content.splitlines())
    if line_count > 500:
        errors.append(f"SKILL.md is {line_count} lines; keep it under 500 (use references/).")

    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.iterdir():
            if script.is_file() and not script.stat().st_mode & 0o111 and script.suffix == ".py":
                errors.append(f"Make script executable: chmod +x {script.relative_to(skill_dir)}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a repo skill directory.")
    parser.add_argument(
        "skill_dir",
        type=Path,
        help="Path to skills/<skill-name>/",
    )
    args = parser.parse_args(argv)

    errors = validate_skill(args.skill_dir.resolve())
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.skill_dir.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
