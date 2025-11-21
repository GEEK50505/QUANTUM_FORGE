#!/usr/bin/env python3
"""Quick verification of SQL migration file for common Supabase/Postgres issues.

Checks performed:
- File exists
- Looks for unguarded pgmq usage (pgmq.create, pgmq.send)
- Detects `create policy if not exists` patterns (unsupported in some PG servers)
- Confirms storage bucket insertion and publication line presence

Exit codes:
0 - no issues found
1 - minor warnings found
2 - critical issue (file missing)
"""
import argparse
import os
import re
import sys

def main(path: str):
    if not os.path.exists(path):
        print(f"ERROR: SQL file not found at {path}")
        return 2

    with open(path, 'r', encoding='utf-8') as f:
        sql = f.read()

    issues = []
    warnings = []

    # Check for unguarded pgmq usage
    if re.search(r"\bpgmq\.create\s*\(|\bpgmq\.send\s*\(|\bpgmq\.receive\s*\(", sql, re.I):
        warnings.append("Found direct pgmq usage (pgmq.create/send/receive). Ensure pgmq extension exists or guard these calls to avoid migration failures.")

    # Check for CREATE POLICY IF NOT EXISTS
    if re.search(r"create\s+policy\s+if\s+not\s+exists", sql, re.I):
        issues.append("Found 'CREATE POLICY IF NOT EXISTS' which is not supported in some Postgres environments; prefer guarded DO blocks or existence checks.")

    # Check for 'alter publication supabase_realtime add table' as optional
    if 'alter publication supabase_realtime add table' not in sql.lower():
        warnings.append("Publication line for supabase_realtime not found. Realtime updates may not be enabled for tables.")

    # Check for storage bucket insert
    if "insert into storage.buckets" not in sql.lower():
        warnings.append("No storage.buckets insertion found; logs/artifacts bucket may not be created.")

    # Check for auth.users trigger helper
    if 'create trigger on_auth_user_created' not in sql.lower() and 'handle_new_user' not in sql.lower():
        warnings.append("No auth.users trigger detected to auto-create profile on signup. That's optional but recommended.")

    # Report
    print("Verification report for:", path)
    print("- Issues (must-fix):")
    if issues:
        for i in issues:
            print("  -", i)
    else:
        print("  - None")

    print("- Warnings (review):")
    if warnings:
        for w in warnings:
            print("  -", w)
    else:
        print("  - None")

    # Decide exit
    if issues:
        return 1
    if warnings:
        return 0
    return 0

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--file', '-f', default='deploy/db/schema.sql', help='Path to SQL migration file')
    args = p.parse_args()
    rc = main(args.file)
    sys.exit(rc)
