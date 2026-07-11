#!/usr/bin/env python3
"""Validate the canonical paper catalog."""

from __future__ import annotations

from pathlib import Path

if __package__:
    from .catalog import load_catalog, validate_file
    from .coverage import load_coverage, validate_coverage_file
else:
    from catalog import load_catalog, validate_file
    from coverage import load_coverage, validate_coverage_file


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "papers.yaml"
COVERAGE_PATH = ROOT / "data" / "coverage.yaml"


def main() -> int:
    paper_errors = validate_file(CATALOG_PATH)
    if paper_errors:
        print("\n".join(paper_errors))
        return 1
    papers = load_catalog(CATALOG_PATH)
    coverage_errors = validate_coverage_file(COVERAGE_PATH, papers)
    if coverage_errors:
        print("\n".join(coverage_errors))
        return 1
    coverage = load_coverage(COVERAGE_PATH)
    print(
        f"Catalog valid: {len(papers)} papers across "
        f"{len(coverage)} venue-year coverage units"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
