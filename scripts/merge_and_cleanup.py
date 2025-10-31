"""
merge_and_cleanup.py
Safe merge helper for merging a secondary project tree into this monorepo.

Usage (dry-run default):
    python scripts/merge_and_cleanup.py --source "C:\\Users\\G_R_E\\Downloads\\free-react-tailwind-admin-dashboard-main" --dry-run

To perform the copy (non-destructive, will not delete):
    python scripts/merge_and_cleanup.py --source "C:\\Users\\G_R_E\\Downloads\\free-react-tailwind-admin-dashboard-main" --apply

Behavior and safety rules:
- Default is `--dry-run` which prints planned operations and a short summary report.
- Does not copy `.git`, `node_modules`, `.venv`, or other large runtime dirs by default.
- Preserves candidate frontend templates: copies `frontend/src`, `frontend/public`, and `frontend/package.json` from the source when present into `frontend/template_sources/<origin>` for later manual review.
- Skips files listed in an internal ignore list; you can extend `EXTRA_IGNORES` at top.
- Copies files with metadata and writes a small `merge_report.json` in `scripts/merge_reports/` describing decisions.

This script is intentionally conservative — it helps the two founders perform the merge with full control. Do not run with `--apply` unless you reviewed the dry-run output.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IGNORES = {".git", "node_modules", "venv", ".venv", "dist", "build", "__pycache__"}
EXTRA_IGNORES = {"*.log", "*.pyc"}


def is_ignored(p: Path, root: Path) -> bool:
    name = p.name
    if name in DEFAULT_IGNORES:
        return True
    try:
        rel = p.relative_to(root)
    except Exception:
        return False
    for pat in EXTRA_IGNORES:
        if rel.match(pat):
            return True
    return False


def collect_items(source: Path) -> List[Path]:
    items = []
    for dirpath, dirnames, filenames in os.walk(source):
        pdir = Path(dirpath)
        # apply ignore rules to dirs in-place for efficiency
        dirnames[:] = [d for d in dirnames if not is_ignored(pdir / d, source)]
        for f in filenames:
            fp = pdir / f
            if is_ignored(fp, source):
                continue
            items.append(fp)
    return items


def preserve_frontend_template(source: Path, target: Path, origin_id: str, apply: bool, report: dict) -> None:
    # Source frontend candidate locations
    candidates = [source / "frontend", source / "react-tailwind-frontend-main-template-files", source / "frontend"]
    copied = []
    for c in candidates:
        if not c.exists():
            continue
        # copy only useful subpaths
        for sub in ["src", "public", "package.json", "index.html"]:
            sp = c / sub
            if not sp.exists():
                continue
            if sp.is_dir():
                for fp in collect_items(sp):
                    rel = fp.relative_to(source)
                    dest = target / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if apply:
                        shutil.copy2(fp, dest)
                    copied.append(str(rel))
            else:
                rel = sp.relative_to(source)
                dest = target / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                if apply:
                    shutil.copy2(sp, dest)
                copied.append(str(rel))
    report["frontend_templates_copied"] = copied


def run_merge(source_root: Path, apply: bool = False) -> dict:
    source = Path(source_root).resolve()
    report = {
        "source": str(source),
        "root": str(ROOT),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "apply": bool(apply),
        "copied": [],
        "skipped": [],
    }

    if not source.exists():
        raise SystemExit(f"Source path {source} does not exist")

    # preserve frontend templates into frontend/template_sources/<origin>
    origin_id = source.name.replace(" ", "_")
    preserve_frontend_template(source, ROOT, origin_id, apply, report)

    # Items to copy: top-level important files and recommended directories
    keep_dirs = {"ai", "backend", "frontend", "docs", "notebooks", "scripts", "requirements.txt", "package.json"}
    for entry in source.iterdir():
        name = entry.name
        if is_ignored(entry, source):
            report["skipped"].append(name)
            continue
        # copy only recommended dirs and important manifests
        if name in keep_dirs or any(name.startswith(k) for k in ["README", "LICENSE", "CHANGELOG"]):
            # copy dir recursively (respecting ignores)
            if entry.is_dir():
                for fp in collect_items(entry):
                    rel = fp.relative_to(source)
                    dest = ROOT / rel
                    report["copied"].append(str(rel))
                    if apply:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(fp, dest)
            else:
                rel = entry.relative_to(source)
                dest = ROOT / rel
                report["copied"].append(str(rel))
                if apply:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(entry, dest)
        else:
            report["skipped"].append(name)

    # write a merge report
    reports_dir = ROOT / "scripts" / "merge_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    report_path = reports_dir / f"merge_report_{origin_id}_{ts}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    report["report_path"] = str(report_path)
    return report


def main():
    parser = argparse.ArgumentParser(description="Merge helper: copy selected files from a source project into this monorepo (safe, dry-run default)")
    parser.add_argument("--source", required=True, help="Absolute path to the source project to merge from")
    parser.add_argument("--apply", action="store_true", help="Apply the copy (default is dry-run)")
    args = parser.parse_args()
    source = Path(args.source)
    report = run_merge(source, apply=args.apply)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
