#!/usr/bin/env python3
"""
Add lightweight header templates to frontend TypeScript files.

This script is non-destructive: it creates a `.bak` backup of any file it
modifies so changes can be reviewed and reverted easily.

It will only add a short comment header to `.ts` and `.tsx` files under
`frontend/src` that do not already contain a 'Purpose:' marker in the
first 5 lines.
"""
import os
from pathlib import Path
import datetime

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / 'frontend' / 'src'
TODO_FILE = ROOT / 'frontend' / 'docs' / 'FRONTEND_DOCS_TODO.md'

HEADER = '''/*
Purpose: 
Description: 
Exports: 
Notes: Add a short usage example and expected props/return types.
*/

'''


def should_add_header(path: Path) -> bool:
    try:
        text = path.read_text(encoding='utf-8')
    except Exception:
        return False
    # Skip if already has a Purpose marker in the first 5 lines
    first_lines = '\n'.join(text.splitlines()[:5])
    if 'Purpose:' in first_lines or 'purpose:' in first_lines:
        return False
    # Skip if it's a declaration file
    if path.suffix == '.d.ts':
        return False
    return True


def add_header(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    bak = path.with_suffix(path.suffix + '.bak')
    # create a backup copy
    bak.write_text(text, encoding='utf-8')
    new_text = HEADER + text
    path.write_text(new_text, encoding='utf-8')
    return True


def main():
    if not FRONTEND_SRC.exists():
        print('frontend/src not found; aborting')
        return
    modified = []
    for root, dirs, files in os.walk(FRONTEND_SRC):
        for name in files:
            if name.endswith('.ts') or name.endswith('.tsx'):
                p = Path(root) / name
                if should_add_header(p):
                    try:
                        add_header(p)
                        modified.append(str(p.relative_to(ROOT)))
                    except Exception as e:
                        print(f'Failed to update {p}: {e}')
    # Write TODO file listing modified files
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TODO_FILE, 'w', encoding='utf-8') as f:
        f.write('# Frontend files updated with header templates\n')
        f.write(f'# Generated: {datetime.datetime.utcnow().isoformat()}Z\n\n')
        for m in modified:
            f.write(m + '\n')
    print(f'Headers added to {len(modified)} files; list written to {TODO_FILE}')


if __name__ == '__main__':
    main()
