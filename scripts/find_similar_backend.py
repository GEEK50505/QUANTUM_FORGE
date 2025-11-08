"""
Find near-duplicate Python files between backend/core and backend/simulation.
Usage: python3 scripts/find_similar_backend.py --threshold 0.8

This script computes a simple similarity score (difflib.SequenceMatcher)
between files and reports pairs with score >= threshold.
"""
from pathlib import Path
import difflib
import argparse


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding='utf-8')
    except Exception:
        return ''


def compute_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--threshold', type=float, default=0.8)
    parser.add_argument('--core', default='backend/core')
    parser.add_argument('--sim', default='backend/simulation')
    args = parser.parse_args()

    core_files = list(Path(args.core).rglob('*.py'))
    sim_files = list(Path(args.sim).rglob('*.py'))

    print(f'Found {len(core_files)} core files and {len(sim_files)} simulation files')

    results = []
    for cf in core_files:
        ca = read_text(cf)
        if not ca.strip():
            continue
        for sf in sim_files:
            sa = read_text(sf)
            if not sa.strip():
                continue
            score = compute_similarity(ca, sa)
            if score >= args.threshold and cf.resolve() != sf.resolve():
                results.append((score, str(cf), str(sf)))

    if not results:
        print('No similar files found above threshold')
        return

    results.sort(reverse=True)
    print('Similar file pairs:')
    for score, cf, sf in results:
        print(f'{score:.3f}  {cf}  <->  {sf}')

if __name__ == '__main__':
    main()
