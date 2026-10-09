#!/usr/bin/env python3
# Copyright 2026 UniFi Insights contributors
"""Check per-file test coverage against a threshold from Cobertura XML."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys
from typing import TypedDict
import xml.etree.ElementTree as ET


class FileCoverage(TypedDict):
    """Per-file coverage statistics."""

    file: str
    total: int
    hits: int
    missed: list[int]
    partial: list[int]
    pct: float


def load_coverage(path: Path | str) -> list[FileCoverage]:
    """Load per-file coverage from a Cobertura XML report.

    Computes coverage the way Codecov does:
    hits / (hits + misses + partials), where a line with an untaken branch
    counts as partial, not hit. Files with 0 measurable lines have 100.0% coverage.
    """
    rows: list[FileCoverage] = []
    tree = ET.parse(path)
    for cls in tree.getroot().iter("class"):
        hits = 0
        missed: list[int] = []
        partial: list[int] = []
        lines_elem = cls.find("lines")
        if lines_elem is not None:
            for line in lines_elem.iter("line"):
                number = int(line.get("number", "0"))
                cond = line.get("condition-coverage")
                line_hits = int(line.get("hits", "0"))
                if line_hits == 0:
                    missed.append(number)
                elif cond and not cond.startswith("100%"):
                    partial.append(number)
                else:
                    hits += 1
        total = hits + len(missed) + len(partial)
        filename = cls.get("filename", "")
        pct = (100.0 * hits / total) if total else 100.0
        rows.append(
            {
                "file": filename,
                "total": total,
                "hits": hits,
                "missed": missed,
                "partial": partial,
                "pct": pct,
            }
        )
    return rows


def check_coverage(
    coverage_file: Path | str,
    fail_under: float = 95.0,
) -> tuple[int, list[FileCoverage], list[FileCoverage]]:
    """Check coverage for all files against fail_under threshold.

    Returns (exit_code, failing_files, all_files).
    exit_code is 0 if all files meet threshold, 1 if any file is below,
    and 2 if no file rows are found.
    """
    rows = load_coverage(coverage_file)
    if not rows:
        return 2, [], []
    failing = [r for r in rows if r["pct"] < fail_under]
    failing.sort(key=lambda r: (r["pct"], r["file"]))
    exit_code = 1 if failing else 0
    return exit_code, failing, rows


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for per-file coverage verification."""
    parser = argparse.ArgumentParser(
        description=(
            "Verify per-file test coverage against a threshold from Cobertura XML."
        ),
    )
    parser.add_argument(
        "xml",
        nargs="?",
        default="coverage.xml",
        help="Path to Cobertura coverage.xml (default: coverage.xml)",
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        default=95.0,
        help="Minimum required coverage percentage per file (default: 95.0)",
    )
    args = parser.parse_args(argv)

    xml_path = Path(args.xml)
    if not xml_path.is_file():
        print(f"Error: coverage file '{args.xml}' not found.", file=sys.stderr)
        return 2

    try:
        exit_code, failing, all_rows = check_coverage(xml_path, args.fail_under)
    except ET.ParseError as err:
        print(f"Error: failed to parse '{args.xml}': {err}", file=sys.stderr)
        return 2

    if exit_code == 2:
        print(f"Error: no file rows found in '{args.xml}'.", file=sys.stderr)
        return 2

    threshold_str = (
        f"{int(args.fail_under)}%"
        if args.fail_under.is_integer()
        else f"{args.fail_under}%"
    )

    for r in failing:
        print(
            f"{r['file']:60} {r['pct']:7.2f}%  "
            f"miss={len(r['missed'])} partial={len(r['partial'])} "
            f"of {r['total']}"
        )

    if failing:
        print(f"{len(failing)} file(s) below {threshold_str} coverage threshold.")
        return 1

    print(
        f"All {len(all_rows)} file(s) meet or exceed "
        f"{threshold_str} coverage threshold."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
