#!/usr/bin/env python3
"""Estimate token cost of reading files. Usage: python estimate_token_cost.py <path> [--verbose]"""

import os
import sys

# Approximate: 1 token ≈ 4 characters for code
CHARS_PER_TOKEN = 4.0

# Overhead per file read
OVERHEAD_TOKENS = 50

# Budgets
MAX_FILES = 10
MAX_LINES = 5000
MAX_BYTES = 50 * 1024  # 50 KB


def estimate(path):
    try:
        size = os.path.getsize(path)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
        return None, str(e)

    line_count = len(lines)
    char_count = sum(len(l) for l in lines)
    token_estimate = int(char_count / CHARS_PER_TOKEN) + OVERHEAD_TOKENS

    return {
        "path": path,
        "size_bytes": size,
        "lines": line_count,
        "chars": char_count,
        "estimated_tokens": token_estimate,
        "under_budget": {
            "files": True,
            "lines": line_count <= MAX_LINES,
            "bytes": size <= MAX_BYTES,
        },
    }, None


def main():
    verbose = "--verbose" in sys.argv
    targets = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not targets:
        print("Usage: python estimate_token_cost.py <path1> [path2 ...] [--verbose]")
        sys.exit(1)

    total_tokens = 0
    file_count = 0
    for target in targets:
        if os.path.isfile(target):
            result, error = estimate(target)
            if error:
                print(f"[SKIP] {target}: {error}")
                continue
            file_count += 1
            total_tokens += result["estimated_tokens"]
            if verbose:
                print(f"[COST] {target}")
                print(f"       Lines: {result['lines']}, Size: {result['size_bytes']} bytes")
                print(f"       Est tokens: {result['estimated_tokens']}")
                under = result["under_budget"]
                if not all(under.values()):
                    reasons = [k for k, v in under.items() if not v]
                    print(f"       WARNING: Over budget on: {', '.join(reasons)}")
                print()
        elif os.path.isdir(target):
            for root, dirs, files in os.walk(target):
                for f in files:
                    fpath = os.path.join(root, f)
                    result, error = estimate(fpath)
                    if error:
                        continue
                    file_count += 1
                    total_tokens += result["estimated_tokens"]
                    if verbose:
                        print(f"[COST] {fpath} → {result['estimated_tokens']} tok")
        else:
            print(f"[SKIP] Not found: {target}")

    print(f"\n[COST:SUMMARY] Files: {file_count}, Est total tokens: {total_tokens}")
    print(f"[BUDGET] files={file_count}/{MAX_FILES}")
    over_files = file_count > MAX_FILES
    over_lines = False  # We don't aggregate this here
    if over_files:
        print(f"[BUDGET_OVERRIDE] Files exceed {MAX_FILES}. Justify before reading.")


if __name__ == "__main__":
    main()
