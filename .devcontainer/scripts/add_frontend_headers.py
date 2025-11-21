#!/usr/bin/env python3
"""
Add standardized file headers to frontend source files.
Creates a `.autodoc.bak` backup for each file modified.

Usage:
  python3 scripts/add_frontend_headers.py --root frontend/src --extensions .ts .tsx [--dry-run]

Safe behavior:
- Idempotent: will not add header if one appears present in the first few lines.
- Preserves top-of-file pragmas like "use client" by inserting header after them.
- Creates a `.autodoc.bak` backup file (won't overwrite an existing .autodoc.bak).
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

HEADER_TEMPLATE = """/*
Purpose: 
Description: 
Exports: 
Notes: Auto-inserted by scripts/add_frontend_headers.py. Original content saved to: {backup}
*/

"""

DEFAULT_EXTS = [".ts", ".tsx", ".js", ".jsx"]
SKIP_DIRS = {"node_modules", "dist", "build", ".git", "public"}


def has_header(lines: list[str]) -> bool:
    # Check the first 8 non-empty lines for the 'Purpose:' marker or a header-like comment
    limit = min(12, len(lines))
    snippet = "\n".join(lines[:limit])
    if "Purpose:" in snippet or "Auto-inserted by scripts/add_frontend_headers.py" in snippet:
        return True
    # Also consider a leading block comment as a header (heuristic: starts with /* and contains Purpose or Exports)
    if snippet.strip().startswith("/*") and ("Exports:" in snippet or "Description:" in snippet):
        return True
    return False


def find_insertion_index(lines: list[str]) -> int:
    # Preserve leading shebang or "use client" or 'use client' pragmas
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == "":
            i += 1
            continue
        # shebang
        if i == 0 and stripped.startswith("#!"):
            i += 1
            continue
        # "use client" or similar pragma
        if stripped in ('"use client";', "'use client';", '"use server";', "'use server';"):
            i += 1
            continue
        break
    return i


def process_file(path: Path, dry_run: bool = False) -> tuple[bool, str]:
    """Return (was_modified, message)"""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"ERROR reading {path}: {e}"
    lines = text.splitlines(keepends=True)
    if has_header(lines):
        return False, f"SKIP (has header): {path}"
    insertion_index = find_insertion_index(lines)
    backup_path = path.with_suffix(path.suffix + ".autodoc.bak")
    header = HEADER_TEMPLATE.format(backup=str(backup_path.name))
    new_lines = []
    # preserve existing leading lines up to insertion_index
    new_lines.extend(lines[:insertion_index])
    # add header
    new_lines.append(header)
    # then the rest
    new_lines.extend(lines[insertion_index:])
    new_text = "".join(new_lines)
    if dry_run:
        return True, f"DRYRUN would modify: {path} (insert at line {insertion_index+1})"
    # create backup if not exists
    if not backup_path.exists():
        try:
            backup_path.write_text(text, encoding="utf-8")
        except Exception as e:
            return False, f"ERROR writing backup {backup_path}: {e}"
    else:
        # if backup exists, create a timestamped backup
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        alt_backup = path.with_suffix(path.suffix + f".autodoc.bak.{ts}")
        alt_backup.write_text(text, encoding="utf-8")
        backup_path = alt_backup
    # write new file
    try:
        path.write_text(new_text, encoding="utf-8")
    except Exception as e:
        return False, f"ERROR writing modified file {path}: {e}"
    return True, f"MODIFIED: {path} (backup: {backup_path.name})"


def walk_and_process(root: Path, exts: set[str], dry_run: bool = False) -> dict:
    results = {"modified": [], "skipped": [], "errors": []}
    for dirpath, dirnames, filenames in os.walk(root):
        # adjust dirnames in-place to skip large folders
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            path = Path(dirpath) / fname
            if path.suffix.lower() not in exts:
                continue
            ok, msg = process_file(path, dry_run=dry_run)
            if msg.startswith("ERROR"):
                results["errors"].append(msg)
            elif msg.startswith("MODIFIED") or msg.startswith("DRYRUN"):
                results["modified"].append(msg)
            else:
                results["skipped"].append(msg)
    return results


def main(argv: list[str]):
    parser = argparse.ArgumentParser(description="Bulk-insert standardized headers into frontend source files")
    parser.add_argument("--root", default="frontend/src", help="Root directory to scan")
    parser.add_argument("--extensions", nargs="*", default=[".ts", ".tsx"], help="File extensions to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing files")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.exists():
        print(f"ERROR: root does not exist: {root}")
        sys.exit(2)
    exts = set([e if e.startswith('.') else '.'+e for e in args.extensions])
    print(f"Scanning {root} for extensions={sorted(exts)} (dry_run={args.dry_run})...")
    results = walk_and_process(root, exts, dry_run=args.dry_run)
    print(f"Modified (or would modify): {len(results['modified'])}")
    for m in results['modified'][:200]:
        print(m)
    if len(results['modified']) > 200:
        print("... (truncated list) ...")
    print(f"Skipped: {len(results['skipped'])}")
    print(f"Errors: {len(results['errors'])}")
    for e in results['errors']:
        print(e)
    # exit code: 0 even if no changes; 3 if errors
    if results['errors']:
        sys.exit(3)

if __name__ == '__main__':
    main(sys.argv[1:])
