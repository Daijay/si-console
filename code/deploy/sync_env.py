#!/usr/bin/env python3
"""Bring an existing code/.env up to date with code/.env.example.

Keeps every value you already filled in, lays the file out like the
current template, applies the known migrations, and backs up the old
file. Standard library only, so it runs before any venv exists.
Never prints a secret: names ending in _KEY or _TOKEN are shown as
"set" or "empty", never their value.

    python code/deploy/sync_env.py              # update code/.env
    python code/deploy/sync_env.py --dry-run    # show what would change
    python code/deploy/sync_env.py --env /path/.env

Migrations (from the repo's history):
- DEEPSEEK_MODEL_PRO is removed: not in the accepted roster (T1 is Qwen4 Max).
- A value in OPENROUTER_API_KEY that is not an OpenRouter key (those
  start with "sk-or-") moves to TYPESAFE_API_KEY: Jev now goes direct to
  TypeSafe by default.
- JEV_MODEL in OpenRouter form ("typesafe/jev-1.14") becomes "jev-1.14.0"
  when the TypeSafe route is used.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import time
from pathlib import Path

LINE = re.compile(r"^\s*(#\s*)?([A-Z][A-Z0-9_]*)\s*=(.*)$")
REMOVED = {"DEEPSEEK_MODEL_PRO": "not in the accepted roster (T1 is Qwen4 Max)"}
OPENROUTER_PREFIX = "sk-or-"


def is_secret(name: str) -> bool:
    return name.endswith("_KEY") or name.endswith("_TOKEN")


def parse_env(text: str) -> dict:
    """Active KEY=VALUE lines only (commented lines are ignored)."""
    values: dict[str, str] = {}
    for raw in text.lstrip("﻿").splitlines():
        match = LINE.match(raw)
        if not match or match.group(1):
            continue
        value = match.group(3).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[match.group(2)] = value
    return values


def migrate(values: dict) -> tuple[dict, list[str]]:
    values = dict(values)
    notes: list[str] = []
    for name, why in REMOVED.items():
        if name in values:
            values.pop(name)
            notes.append(f"removed {name}: {why}")
    old = values.get("OPENROUTER_API_KEY", "")
    if old and not old.startswith(OPENROUTER_PREFIX) and not values.get("TYPESAFE_API_KEY"):
        values["TYPESAFE_API_KEY"] = old
        values.pop("OPENROUTER_API_KEY")
        notes.append("moved the key in OPENROUTER_API_KEY to TYPESAFE_API_KEY "
                     "(it is not an OpenRouter key; Jev goes direct to TypeSafe)")
    typesafe_route = bool(values.get("TYPESAFE_API_KEY")) or not values.get("OPENROUTER_API_KEY")
    jev = values.get("JEV_MODEL", "")
    if typesafe_route and (jev.startswith("typesafe/") or not jev):
        values["JEV_MODEL"] = "jev-1.14.0"
        notes.append(f"JEV_MODEL {jev or '(empty)'} -> jev-1.14.0 (TypeSafe direct id)")
    if "dashscope-intl" in values.get("DASHSCOPE_BASE_URL", ""):
        notes.append("WARNING: DASHSCOPE_BASE_URL is the Singapore endpoint; a Hong Kong "
                     "key needs https://cn-hongkong.dashscope.aliyuncs.com/compatible-mode/v1 "
                     "(or delete the line to use that default)")
    return values, notes


def render(template: str, values: dict) -> tuple[str, list[str]]:
    """The template with your values filled in. Commented template lines
    become active when you have a value for them. Unknown keys from your
    old file are kept at the end."""
    out: list[str] = []
    used: set[str] = set()
    for raw in template.lstrip("﻿").splitlines():
        match = LINE.match(raw)
        if not match:
            out.append(raw)
            continue
        commented, name, default = match.group(1), match.group(2), match.group(3)
        if name in values:
            out.append(f"{name}={values[name]}")
            used.add(name)
        elif commented:
            out.append(raw)
        else:
            out.append(f"{name}={default.strip()}")
    extra = [n for n in values if n not in used]
    if extra:
        out += ["", "# --- Kept from your old .env (not in the template) ---"]
        out += [f"{n}={values[n]}" for n in extra]
    return "\n".join(out) + "\n", extra


def show(name: str, value: str) -> str:
    if is_secret(name):
        return f"{name}: {'set' if value else 'EMPTY'}"
    return f"{name}: {value or 'EMPTY'}"


def main(argv=None) -> int:
    here = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--env", default=str(here / ".env"))
    parser.add_argument("--template", default=str(here / ".env.example"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    env_path, template_path = Path(args.env), Path(args.template)
    if not template_path.is_file():
        print(f"template not found: {template_path}", file=sys.stderr)
        return 2
    template = template_path.read_text(encoding="utf-8")
    old_text = env_path.read_text(encoding="utf-8") if env_path.is_file() else ""
    values, notes = migrate(parse_env(old_text))
    new_text, extra = render(template, values)

    print(f".env: {env_path}")
    for note in notes:
        print(f"  - {note}")
    for name in extra:
        print(f"  - kept {name} (not in the template)")
    print("Values after sync:")
    for name, value in parse_env(new_text).items():
        print(f"  {show(name, value)}")

    if args.dry_run:
        print("Dry run: nothing written.")
        return 0
    if old_text == new_text:
        print("Already up to date.")
        return 0
    if env_path.is_file():
        backup = env_path.with_name(f".env.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(env_path, backup)
        os.chmod(backup, 0o600)
        print(f"Backup: {backup} (git-ignored; delete it once the new file works)")
    env_path.write_text(new_text, encoding="utf-8", newline="\n")
    os.chmod(env_path, 0o600)
    print("Written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
