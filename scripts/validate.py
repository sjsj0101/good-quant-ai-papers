#!/usr/bin/env python3
"""Validate the canonical paper catalog."""

from __future__ import annotations

from pathlib import Path

if __package__:
    from .catalog import load_catalog, validate_file
else:
    from catalog import load_catalog, validate_file


CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "papers.yaml"


def main() -> int:
    errors = validate_file(CATALOG_PATH)
    if errors:
        print("\n".join(errors))
        return 1

    records = load_catalog(CATALOG_PATH)
    print(f"Catalog valid: {len(records)} papers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
