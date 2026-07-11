# 2024–2026 Cross-Conference Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the public catalog to evidence-backed 2024–2026 coverage for all 11 declared venues, with visible coverage status and verified quantitative-finance or asset-management papers.

**Architecture:** Keep `data/papers.yaml` as the paper source of truth and add `data/coverage.yaml` as a 33-unit audit ledger. A focused coverage validator cross-checks both sources, while the renderer consumes both to build a coverage matrix and evidence-rich venue pages. Research is batched by year and uses official venue sources; unavailable 2026 programs remain explicitly pending.

**Tech Stack:** Python 3.11, PyYAML 6.0.3, JSON Schema documents, `unittest`, deterministic Markdown generation, GitHub Actions.

## Global Constraints

- Cover exactly the years 2024, 2025, and 2026 in this release.
- Cover exactly ICML, NeurIPS, ICLR, KDD, AAAI, IJCAI, WWW, WSDM, SIGIR, AISTATS, and ACM ICAIF.
- Admit main, workshop, position, and affinity papers only with explicit track labels and official acceptance evidence.
- Exclude banking, credit, fraud, payments, accounting QA, regulation, and generic financial AI without a direct investment, trading, portfolio, derivatives, or market-risk decision.
- Treat an arXiv URL as a paper link, never as sole proof of venue acceptance.
- Store original editorial summaries and links; do not store PDFs or copy abstracts.
- Keep CI network-free and deterministic.
- Preserve the existing 23 ICML 2026 records unless an official source proves a correction is needed.
- Use test-driven development for behavior changes and commit each independently testable task.

## File Map

- Create `scripts/coverage.py`: coverage constants, loading, record validation, and paper/coverage cross-checks.
- Create `schema/coverage.schema.json`: public contract for one coverage-ledger record.
- Create `data/coverage.yaml`: exactly 33 venue-year audit records.
- Create `tests/test_coverage.py`: coverage and cross-file regression tests.
- Modify `scripts/catalog.py`: ordered venue constant, reusable YAML-list loader, and optional `subvenue` support.
- Modify `schema/paper.schema.json`: optional `subvenue` contract.
- Modify `scripts/validate.py`: validate both data files and print combined counts.
- Modify `scripts/render.py`: consume coverage data, render matrix/status/source details, preserve deterministic cleanup.
- Modify `tests/test_validate.py`: paper `subvenue`, generic loader, and CLI regressions.
- Modify `tests/test_render.py`: two-source renderer, coverage matrix, venue ordering, and subvenue regressions.
- Modify `data/papers.yaml`: verified 2024–2026 records from all venue families.
- Modify `docs/metadata.md` and `CONTRIBUTING.md`: coverage-ledger and evidence instructions.
- Regenerate `README.md` and `papers/<year>/<venue>.md` from the two YAML sources.

## Spec Coverage Map

- Coverage contract and 33-unit ledger: Task 2.
- Optional subvenue metadata and stable paper contract: Task 1.
- Coverage matrix, ordered navigation, status evidence, and generated pages: Task 3.
- Official-source research and scope adjudication for 2024, 2025, and 2026: Tasks 4–6.
- Contributor workflow and metadata definitions: Task 7.
- Full acceptance criteria, review, public update, and CI verification: Task 8.

---

### Task 1: Extend the Paper Contract for Cross-Conference Records

**Files:**
- Modify: `scripts/catalog.py`
- Modify: `schema/paper.schema.json`
- Modify: `tests/test_validate.py`

**Interfaces:**
- Produces: `VENUE_ORDER: tuple[str, ...]`, `load_yaml_list(path: Path, root_name: str) -> list[dict]`, and optional paper field `subvenue: str`.
- Preserves: `VENUES`, `load_catalog(path)`, `validate_catalog(records)`, and all existing URL and duplicate checks.

- [ ] **Step 1: Write failing paper-contract tests**

Add these cases to `CatalogValidationTests`:

```python
def test_non_empty_subvenue_is_allowed(self) -> None:
    record = copy.deepcopy(VALID)
    record["track"] = "workshop"
    record["subvenue"] = "Workshop on Financial AI"
    self.assertEqual(validate_catalog([record]), [])

def test_empty_subvenue_is_rejected(self) -> None:
    record = copy.deepcopy(VALID)
    record["subvenue"] = "  "
    errors = validate_catalog([record])
    self.assertTrue(
        any(error.startswith(f"{VALID['id']}: subvenue:") for error in errors),
        errors,
    )

def test_schema_declares_optional_subvenue(self) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "schema" / "paper.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    self.assertEqual(schema["properties"]["subvenue"]["type"], "string")
    self.assertNotIn("subvenue", schema["required"])
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run:

```bash
python3 -m unittest \
  tests.test_validate.CatalogValidationTests.test_non_empty_subvenue_is_allowed \
  tests.test_validate.CatalogValidationTests.test_empty_subvenue_is_rejected \
  tests.test_validate.CatalogValidationTests.test_schema_declares_optional_subvenue -v
```

Expected: failure because `subvenue` is rejected and absent from the schema.

- [ ] **Step 3: Add the ordered venue constant and reusable loader**

Replace the unordered venue declaration with:

```python
VENUE_ORDER = (
    "ICML",
    "NeurIPS",
    "ICLR",
    "KDD",
    "AAAI",
    "IJCAI",
    "WWW",
    "WSDM",
    "SIGIR",
    "AISTATS",
    "ACM ICAIF",
)
VENUES = frozenset(VENUE_ORDER)
```

Extract the loader body into the public helper and retain the wrapper:

```python
def load_yaml_list(path: Path, root_name: str) -> list[dict]:
    with path.open("r", encoding="utf-8") as stream:
        records = yaml.load(stream, Loader=_CatalogLoader)
    if not isinstance(records, list):
        raise ValueError(f"{root_name} root must be a YAML list")
    return records


def load_catalog(path: Path) -> list[dict]:
    return load_yaml_list(path, "catalog")
```

Add `subvenue` to `OPTIONAL_STRING_FIELDS` so the existing non-empty-string check applies.

- [ ] **Step 4: Extend the JSON Schema**

Add this optional property to `schema/paper.schema.json` without adding it to `required`:

```json
"subvenue": {
  "type": "string",
  "minLength": 1,
  "pattern": "\\S"
}
```

- [ ] **Step 5: Run the focused and existing validation tests**

Run:

```bash
python3 -m unittest tests.test_validate -v
```

Expected: every validation test passes.

- [ ] **Step 6: Commit the paper-contract change**

```bash
git add scripts/catalog.py schema/paper.schema.json tests/test_validate.py
git commit -m "feat: support cross-conference subvenues"
```

---

### Task 2: Add the 33-Unit Coverage Ledger and Cross-File Validator

**Files:**
- Create: `scripts/coverage.py`
- Create: `schema/coverage.schema.json`
- Create: `data/coverage.yaml`
- Create: `tests/test_coverage.py`
- Modify: `scripts/validate.py`

**Interfaces:**
- Consumes: `VENUE_ORDER`, `VENUES`, `TRACKS`, `load_yaml_list`, and `HTTP_URL_PATTERN` from `scripts.catalog`.
- Produces: `COVERAGE_YEARS`, `COVERAGE_STATUSES`, `load_coverage(path)`, `validate_coverage(records, papers)`, and `validate_coverage_file(path, papers)`.
- CLI output: `Catalog valid: N papers across 33 venue-year coverage units`.

- [ ] **Step 1: Write the coverage-test fixture and failing tests**

Create `tests/test_coverage.py` with this reusable fixture:

```python
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.catalog import HTTP_URL_PATTERN, VENUE_ORDER
from scripts.coverage import COVERAGE_YEARS, validate_coverage
from tests.test_validate import VALID


def make_coverage() -> list[dict]:
    return [
        {
            "venue": venue,
            "year": year,
            "status": "pending",
            "checked_on": "2026-07-11",
            "tracks_checked": ["main"],
            "official_sources": [f"https://example.org/{year}/{venue.lower().replace(' ', '-')}"],
            "notes": "Official program availability reviewed for this coverage unit.",
        }
        for year in COVERAGE_YEARS
        for venue in VENUE_ORDER
    ]
```

Add these tests:

```python
class CoverageValidationTests(unittest.TestCase):
    def test_exact_33_pending_units_are_valid(self) -> None:
        self.assertEqual(validate_coverage(make_coverage(), []), [])

    def test_missing_unit_is_rejected(self) -> None:
        coverage = make_coverage()[:-1]
        errors = validate_coverage(coverage, [])
        self.assertTrue(any("missing coverage unit" in error for error in errors), errors)

    def test_duplicate_unit_is_rejected(self) -> None:
        coverage = make_coverage()
        coverage.append(copy.deepcopy(coverage[0]))
        errors = validate_coverage(coverage, [])
        self.assertTrue(any("duplicate coverage unit" in error for error in errors), errors)

    def test_complete_requires_a_matching_paper(self) -> None:
        coverage = make_coverage()
        unit = next(row for row in coverage if row["venue"] == "ICML" and row["year"] == 2026)
        unit["status"] = "complete"
        errors = validate_coverage(coverage, [])
        self.assertTrue(any("complete requires at least one paper" in error for error in errors), errors)

    def test_no_eligible_papers_rejects_a_matching_paper(self) -> None:
        coverage = make_coverage()
        unit = next(row for row in coverage if row["venue"] == "ICML" and row["year"] == 2026)
        unit["status"] = "no-eligible-papers"
        errors = validate_coverage(coverage, [copy.deepcopy(VALID)])
        self.assertTrue(any("no-eligible-papers requires zero papers" in error for error in errors), errors)

    def test_paper_outside_coverage_years_is_rejected(self) -> None:
        paper = copy.deepcopy(VALID)
        paper["year"] = 2023
        paper["id"] = "2023-icml-hwang-signature-informed-transformer"
        errors = validate_coverage(make_coverage(), [paper])
        self.assertTrue(any("has no coverage unit" in error for error in errors), errors)

    def test_schema_matches_runtime_constants(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "schema" / "coverage.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual(properties["venue"]["enum"], list(VENUE_ORDER))
        self.assertEqual(properties["year"]["enum"], list(COVERAGE_YEARS))
        self.assertEqual(schema["$defs"]["http_url"]["pattern"], HTTP_URL_PATTERN)
```

- [ ] **Step 2: Run the new tests and confirm import failure**

Run:

```bash
python3 -m unittest tests.test_coverage -v
```

Expected: import failure because `scripts.coverage` does not exist.

- [ ] **Step 3: Implement the coverage module**

Create `scripts/coverage.py` with this complete implementation:

```python
"""Validate the 2024–2026 venue coverage ledger."""

from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Sequence

import yaml

if __package__:
    from .catalog import (
        HTTP_URL_PATTERN,
        TRACKS,
        VENUE_ORDER,
        VENUES,
        load_yaml_list,
    )
else:
    from catalog import (
        HTTP_URL_PATTERN,
        TRACKS,
        VENUE_ORDER,
        VENUES,
        load_yaml_list,
    )


COVERAGE_YEARS = (2024, 2025, 2026)
COVERAGE_STATUSES = frozenset({"complete", "no-eligible-papers", "pending"})
COVERAGE_FIELDS = (
    "venue",
    "year",
    "status",
    "checked_on",
    "tracks_checked",
    "official_sources",
    "notes",
)
_HTTP_URL_RE = re.compile(HTTP_URL_PATTERN)
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def _label(record: object, index: int) -> str:
    if isinstance(record, dict):
        venue = record.get("venue")
        year = record.get("year")
        if isinstance(venue, str) and type(year) is int:
            return f"{year}-{venue}"
    return f"<coverage {index + 1}>"


def _non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _error(errors: list[str], label: str, field: str, message: str) -> None:
    errors.append(f"{label}: {field}: {message}")


def _string_list(
    value: object,
    *,
    label: str,
    field: str,
    errors: list[str],
) -> bool:
    if not isinstance(value, list) or not value:
        _error(errors, label, field, "must be a non-empty list")
        return False
    if any(not _non_empty(item) for item in value):
        _error(errors, label, field, "must contain only non-empty strings")
        return False
    if len(value) != len(set(value)):
        _error(errors, label, field, "must not contain duplicate values")
        return False
    return True


def load_coverage(path: Path) -> list[dict]:
    return load_yaml_list(path, "coverage")


def validate_coverage(records: list[dict], papers: Sequence[dict]) -> list[str]:
    """Validate record shape, exact matrix coverage, and paper-count consistency."""
    if not isinstance(records, list):
        return ["<coverage>: records: must be a list"]

    errors: list[str] = []
    expected = {
        (year, venue) for year in COVERAGE_YEARS for venue in VENUE_ORDER
    }
    seen: dict[tuple[int, str], str] = {}
    valid_rows: dict[tuple[int, str], dict] = {}

    for index, record in enumerate(records):
        label = _label(record, index)
        if not isinstance(record, dict):
            _error(errors, label, "record", "must be a mapping")
            continue
        for field in COVERAGE_FIELDS:
            if field not in record:
                _error(errors, label, field, "required field is missing")
        for field in sorted(set(record) - set(COVERAGE_FIELDS), key=str):
            _error(errors, label, str(field), "field is not allowed")

        venue = record.get("venue")
        year = record.get("year")
        status = record.get("status")
        if not isinstance(venue, str) or venue not in VENUES:
            _error(errors, label, "venue", f"{venue!r} is not allowed")
        if type(year) is not int or year not in COVERAGE_YEARS:
            _error(errors, label, "year", f"must be one of {COVERAGE_YEARS}")
        if not isinstance(status, str) or status not in COVERAGE_STATUSES:
            choices = ", ".join(sorted(COVERAGE_STATUSES))
            _error(errors, label, "status", f"choose one of: {choices}")

        checked_on = record.get("checked_on")
        if not _non_empty(checked_on):
            _error(errors, label, "checked_on", "must be a non-empty string")
        else:
            try:
                if not _DATE_RE.fullmatch(checked_on):
                    raise ValueError
                date.fromisoformat(checked_on)
            except ValueError:
                _error(errors, label, "checked_on", "must be a valid ISO date")

        if _string_list(
            record.get("tracks_checked"),
            label=label,
            field="tracks_checked",
            errors=errors,
        ):
            for track in record["tracks_checked"]:
                if track not in TRACKS:
                    _error(errors, label, "tracks_checked", f"unknown track {track!r}")

        if _string_list(
            record.get("official_sources"),
            label=label,
            field="official_sources",
            errors=errors,
        ):
            for source in record["official_sources"]:
                if _HTTP_URL_RE.fullmatch(source) is None:
                    _error(
                        errors,
                        label,
                        "official_sources",
                        f"invalid HTTP(S) URL {source!r}",
                    )

        if not _non_empty(record.get("notes")):
            _error(errors, label, "notes", "must be a non-empty string")

        if type(year) is int and isinstance(venue, str):
            key = (year, venue)
            first = seen.get(key)
            if first is not None:
                _error(errors, label, "unit", f"duplicate coverage unit; first is {first}")
            else:
                seen[key] = label
                if key in expected:
                    valid_rows[key] = record

    for year in COVERAGE_YEARS:
        for venue in VENUE_ORDER:
            if (year, venue) not in seen:
                _error(
                    errors,
                    "<coverage>",
                    "unit",
                    f"missing coverage unit: {venue} {year}",
                )

    counts: Counter[tuple[int, str]] = Counter()
    for paper in papers:
        if not isinstance(paper, dict):
            continue
        key = (paper.get("year"), paper.get("venue"))
        paper_id = paper.get("id", "<paper>")
        if key not in expected:
            _error(errors, str(paper_id), "coverage", "has no coverage unit")
            continue
        counts[key] += 1

    for key, record in valid_rows.items():
        status = record.get("status")
        count = counts[key]
        label = f"{key[0]}-{key[1]}"
        if status == "complete" and count == 0:
            _error(errors, label, "status", "complete requires at least one paper")
        if status == "no-eligible-papers" and count != 0:
            _error(
                errors,
                label,
                "status",
                "no-eligible-papers requires zero papers",
            )
    return errors


def validate_coverage_file(path: Path, papers: Sequence[dict]) -> list[str]:
    try:
        records = load_coverage(path)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        return [f"<coverage>: file: could not load {path}: {error}"]
    return validate_coverage(records, papers)
```

This implementation reuses the paper catalog's URL regex and duplicate-key
YAML loader, returns deterministic errors, and does not raise on malformed
record values.

- [ ] **Step 4: Add the coverage JSON Schema**

Create `schema/coverage.schema.json` with this structure. Copy the complete
`$defs.http_url` object byte-for-byte from `schema/paper.schema.json` into the
indicated `$defs` key so both schemas use the same URL contract.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/sjsj0101/good-quant-ai-papers/blob/main/schema/coverage.schema.json",
  "title": "Conference coverage record",
  "description": "Metadata contract for one venue-year audit in data/coverage.yaml.",
  "$defs": {
    "http_url": {
      "type": "string",
      "format": "uri",
      "pattern": "^(?!.*\\s)(?!.*[\\[\\]])(?!.*%(?![0-9A-Fa-f]{2}))[Hh][Tt][Tt][Pp][Ss]?://(?:[^/?#@\\s\\[\\]]+@)?(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\\.)*[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?::0*(?:[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]))?(?:[/?#][^\\s]*)?$"
    }
  },
  "type": "object",
  "additionalProperties": false,
  "required": [
    "venue",
    "year",
    "status",
    "checked_on",
    "tracks_checked",
    "official_sources",
    "notes"
  ],
  "properties": {
    "venue": {
      "enum": ["ICML", "NeurIPS", "ICLR", "KDD", "AAAI", "IJCAI", "WWW", "WSDM", "SIGIR", "AISTATS", "ACM ICAIF"]
    },
    "year": {
      "enum": [2024, 2025, 2026]
    },
    "status": {
      "enum": ["complete", "no-eligible-papers", "pending"]
    },
    "checked_on": {
      "type": "string",
      "format": "date"
    },
    "tracks_checked": {
      "type": "array",
      "minItems": 1,
      "uniqueItems": true,
      "items": {
        "enum": ["main", "workshop", "position", "affinity"]
      }
    },
    "official_sources": {
      "type": "array",
      "minItems": 1,
      "uniqueItems": true,
      "items": {
        "$ref": "#/$defs/http_url"
      }
    },
    "notes": {
      "type": "string",
      "minLength": 1,
      "pattern": "\\S"
    }
  }
}
```

- [ ] **Step 5: Seed all 33 units as pending**

Create `data/coverage.yaml` in year-descending, declared-venue order. Give every unit:

- its exact venue and year;
- `status: pending`;
- `checked_on: 2026-07-11`;
- only the track families actually checked during the initial availability pass;
- at least one official conference, proceedings, program, or official venue URL; and
- a factual note that states which official program material is or is not yet available.

Set ICML 2026 to `pending` at this infrastructure stage because verified papers exist but the broader cross-track audit has not yet been completed.

- [ ] **Step 6: Update the validation CLI**

Use these paths and control flow in `scripts/validate.py`:

```python
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
```

- [ ] **Step 7: Run focused and full validator tests**

Run:

```bash
python3 -m unittest tests.test_coverage tests.test_validate -v
python3 scripts/validate.py
```

Expected: tests pass and CLI reports 23 papers across 33 units.

- [ ] **Step 8: Commit the coverage contract**

```bash
git add scripts/coverage.py schema/coverage.schema.json data/coverage.yaml tests/test_coverage.py scripts/validate.py
git commit -m "feat: add conference coverage ledger"
```

---

### Task 3: Render Coverage Status, Ordered Venues, and Subvenues

**Files:**
- Modify: `scripts/render.py`
- Modify: `tests/test_render.py`
- Regenerate: `README.md`
- Regenerate: `papers/2026/icml.md`

**Interfaces:**
- Consumes: `papers: list[dict]` and `coverage: list[dict]`.
- Produces: `render_readme(papers, coverage)`, `render_venue_pages(papers, coverage)`, and `render_outputs(papers, coverage)`.
- Preserves: generated-file marker cleanup and network-free `--check` behavior.

- [ ] **Step 1: Load coverage in renderer tests**

Add:

```python
from scripts.coverage import load_coverage
from tests.test_coverage import make_coverage

COVERAGE = load_coverage(ROOT / "data" / "coverage.yaml")
```

Update existing calls to pass `COVERAGE` as the second argument. In each
temporary-root CLI test, copy the coverage source beside `papers.yaml`:

```python
(data / "coverage.yaml").write_text(
    (ROOT / "data" / "coverage.yaml").read_text(encoding="utf-8"),
    encoding="utf-8",
)
```

- [ ] **Step 2: Write failing coverage rendering tests**

Add assertions that the README contains:

```python
self.assertIn("## Coverage: 2024–2026", rendered)
self.assertIn("| Venue | 2026 | 2025 | 2024 |", rendered)
self.assertIn("| ICML |", rendered)
self.assertIn("| NeurIPS |", rendered)
self.assertIn("| ACM ICAIF |", rendered)
self.assertIn("[23 papers](papers/2026/icml.md) · Pending", rendered)
self.assertIn("Venues-11", rendered)
```

Replace the existing `self.assertIn("Venues-1", rendered)` assertion with the
`Venues-11` assertion above.

Import `make_coverage` from `tests.test_coverage` and add this focused case:

```python
def test_multi_venue_matrix_and_subvenue_metadata(self) -> None:
    main = copy.deepcopy(CATALOG[0])
    main.update(
        {
            "id": "2025-neurips-doe-portfolio-learning",
            "title": "Portfolio Learning",
            "authors": ["Jane Doe"],
            "venue": "NeurIPS",
            "year": 2025,
            "track": "main",
            "official_url": "https://neurips.cc/virtual/2025/poster/100",
            "paper_url": "https://example.org/portfolio-learning",
        }
    )
    workshop = copy.deepcopy(main)
    workshop.update(
        {
            "id": "2025-neurips-roe-market-simulation",
            "title": "Market Simulation",
            "authors": ["Richard Roe"],
            "track": "workshop",
            "subvenue": "Workshop on Financial AI",
            "official_url": "https://neurips.cc/virtual/2025/workshop/200",
            "paper_url": "https://example.org/market-simulation",
        }
    )
    coverage = make_coverage()

    readme = render_readme([workshop, main], coverage)
    venue = render_venue_pages([workshop, main], coverage)[
        Path("papers/2025/neurips.md")
    ]

    self.assertLess(readme.index("| ICML |"), readme.index("| NeurIPS |"))
    self.assertIn("Workshop on Financial AI", readme)
    self.assertIn("**Coverage status:** Pending", venue)
    self.assertIn("**Checked on:** 2026-07-11", venue)
    self.assertIn("**Official audit sources:**", venue)
    self.assertIn("**Subvenue:** Workshop on Financial AI", venue)
```

- [ ] **Step 3: Run renderer tests and confirm signature failures**

Run:

```bash
python3 -m unittest tests.test_render -v
```

Expected: failures because render functions accept only paper records and do not emit coverage metadata.

- [ ] **Step 4: Implement coverage helpers and deterministic ordering**

Extend the existing package/script conditional import block rather than using
an absolute package import:

```python
from collections import Counter, defaultdict

if __package__:
    from .catalog import VENUE_ORDER, load_catalog, validate_catalog
    from .coverage import COVERAGE_YEARS, load_coverage, validate_coverage
else:
    from catalog import VENUE_ORDER, load_catalog, validate_catalog
    from coverage import COVERAGE_YEARS, load_coverage, validate_coverage

COVERAGE_LABELS = {
    "complete": "Complete",
    "no-eligible-papers": "No eligible papers",
    "pending": "Pending",
}


def _coverage_by_key(coverage: Iterable[dict]) -> dict[tuple[int, str], dict]:
    return {(row["year"], row["venue"]): row for row in coverage}


def _venue_sort_key(venue: str) -> tuple[int, str]:
    try:
        return (VENUE_ORDER.index(venue), "")
    except ValueError:
        return (len(VENUE_ORDER), venue.casefold())
```

Change the venue portion of `_sorted_records` to
`_venue_sort_key(record["venue"])`. Change `_records_by_venue` to sort keys
with:

```python
key=lambda item: (-item[0], _venue_sort_key(item[1]))
```

Update the generated marker and README statistics to describe both inputs and
the declared venue universe:

```python
GENERATED_NOTICE = (
    "<!-- Generated from data/papers.yaml and data/coverage.yaml by "
    "scripts/render.py. Do not edit directly. -->"
)

venue_count = len(VENUE_ORDER)
last_verified = max(
    [record["verified_on"] for record in ordered]
    + [row["checked_on"] for row in coverage],
    default="Not available",
)
```

- [ ] **Step 5: Render the coverage matrix**

Add this helper and insert its output immediately after the Scope section:

```python
def _render_coverage_matrix(
    records: Iterable[dict], coverage: Iterable[dict]
) -> list[str]:
    counts = Counter((record["year"], record["venue"]) for record in records)
    by_key = _coverage_by_key(coverage)
    years = tuple(sorted(COVERAGE_YEARS, reverse=True))
    lines = [
        "## Coverage: 2024–2026",
        "",
        "| Venue | " + " | ".join(str(year) for year in years) + " |",
        "| --- | " + " | ".join("---:" for _ in years) + " |",
    ]
    for venue in VENUE_ORDER:
        cells: list[str] = []
        for year in years:
            count = counts[(year, venue)]
            noun = "paper" if count == 1 else "papers"
            count_text = f"{count} {noun}"
            if count:
                path = f"papers/{year}/{_venue_slug(venue)}.md"
                count_text = f"[{count_text}]({path})"
            status = COVERAGE_LABELS[by_key[(year, venue)]["status"]]
            cells.append(f"{count_text} · {status}")
        lines.append(
            f"| {_escape_markdown(venue)} | " + " | ".join(cells) + " |"
        )
    return lines
```

The section heading and header are exactly:

```markdown
## Coverage: 2024–2026

| Venue | 2026 | 2025 | 2024 |
| --- | ---: | ---: | ---: |
```

- [ ] **Step 6: Update venue pages and paper track display**

Replace `_track_cell` with:

```python
def _track_cell(record: dict) -> str:
    track = TRACK_LABELS.get(record["track"], _display_label(record["track"]))
    parts = [track, f"<sub>{_display_label(record['presentation'])}</sub>"]
    if record.get("subvenue"):
        parts.append(f"<sub>{_escape_markdown(record['subvenue'])}</sub>")
    return "<br>".join(parts)
```

In `_venue_record_block`, insert this after the track/presentation metadata:

```python
if record.get("subvenue"):
    lines.extend(["", _metadata_line("Subvenue", record["subvenue"])])
```

Change the declaration to `def _render_venue_page(year: int, venue: str,
records: list[dict], coverage_record: dict) -> str:`.

Build the source links and add this metadata below the title:

```python
source_links = " · ".join(
    _markdown_link(f"Source {index}", url)
    for index, url in enumerate(coverage_record["official_sources"], start=1)
)
coverage_lines = [
    _metadata_line(
        "Coverage status", COVERAGE_LABELS[coverage_record["status"]]
    ),
    "",
    _metadata_line("Checked on", coverage_record["checked_on"]),
    "",
    f"**Official audit sources:** {source_links}",
    "",
    _metadata_line("Coverage notes", coverage_record["notes"]),
]
```

The generated result begins with lines shaped as:

```markdown
**Coverage status:** Pending

**Checked on:** 2026-07-11

**Official audit sources:** [Source 1](<https://example.org/source>)
```

Keep the existing paper count, back link, track sections, and record blocks
after `coverage_lines`.

- [ ] **Step 7: Update CLI loading and function signatures**

Change the README declaration to
`def render_readme(records: list[dict], coverage: list[dict]) -> str:`. Remove
the existing `"## Browse by Topic"` pair from the initial `lines` literal and
insert this before computing the topic list:

```python
lines.extend(["", *_render_coverage_matrix(ordered, coverage), ""])
lines.extend(["## Browse by Topic", ""])
```

Replace the venue-page and output functions with:

```python
def render_venue_pages(
    records: list[dict], coverage: list[dict]
) -> dict[Path, str]:
    pages: dict[Path, str] = {}
    by_key = _coverage_by_key(coverage)
    for (year, venue), venue_records in _records_by_venue(records).items():
        path = Path("papers", str(year), f"{_venue_slug(venue)}.md")
        pages[path] = _render_venue_page(
            year, venue, venue_records, by_key[(year, venue)]
        )
    return pages


def render_outputs(
    records: list[dict], coverage: list[dict]
) -> dict[Path, str]:
    outputs = {Path("README.md"): render_readme(records, coverage)}
    outputs.update(render_venue_pages(records, coverage))
    return outputs
```

In `main`, add:

```python
coverage_path = repository_root / "data" / "coverage.yaml"
try:
    records = load_catalog(catalog_path)
    coverage = load_coverage(coverage_path)
except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Metadata error: {error}")
    return 1

errors = validate_catalog(records) + validate_coverage(coverage, records)
if errors:
    print("\n".join(errors))
    return 1
outputs = render_outputs(records, coverage)
```

Keep cleanup restricted to files whose first line is `GENERATED_NOTICE`.

- [ ] **Step 8: Run tests, regenerate, and verify freshness**

Run:

```bash
python3 -m unittest tests.test_render -v
python3 scripts/render.py
python3 scripts/render.py --check
git diff --check
```

Expected: all tests pass, renderer reports current generated files, and no whitespace errors appear.

- [ ] **Step 9: Commit the renderer expansion**

```bash
git add scripts/render.py tests/test_render.py README.md papers/2026/icml.md
git commit -m "feat: render conference coverage matrix"
```

---

### Task 4: Curate and Verify All 2024 Venue Units

**Files:**
- Modify: `data/papers.yaml`
- Modify: `data/coverage.yaml`
- Regenerate: `README.md`
- Create or regenerate: `papers/2024/*.md`

**Interfaces:**
- Consumes: official proceedings, OpenReview venues, conference programs, and official workshop programs.
- Produces: complete 2024 paper records plus final evidence-backed status for each of the 11 coverage units.

- [ ] **Step 1: Divide the official-source audit into independent venue families**

Use three parallel research assignments:

1. ICML, NeurIPS, ICLR, and AISTATS;
2. KDD, AAAI, and IJCAI; and
3. WWW, WSDM, SIGIR, and ACM ICAIF.

Each assignment must inspect main proceedings plus officially linked workshop, position, and affinity programs where those track families exist.

- [ ] **Step 2: Search each official source with the fixed discovery vocabulary**

Use these terms across title, program search, and proceedings metadata:

```text
portfolio, asset allocation, asset pricing, stock, equity, return, alpha,
factor, trading, trader, market, order book, execution, market impact,
derivative, option, volatility, tail risk, finance, financial, crypto
```

For each candidate, record title, ordered authors, venue, year, track, presentation, official acceptance URL, public paper URL, event name, and the passage or task demonstrating direct investment relevance. Reject candidates that only match an excluded FinTech category.

- [ ] **Step 3: Resolve evidence using official-source precedence**

Prefer proceedings over OpenReview, OpenReview over conference programs, and conference programs over organizer pages. Use arXiv only for paper access or missing optional identifiers. When title or author versions differ, use the official accepted version and document a material discrepancy in `notes`.

- [ ] **Step 4: Add every accepted 2024 record**

For every candidate that passes Step 3, add one complete YAML mapping with all required paper fields, at least one controlled topic, an original one-sentence `summary`, an original `why_it_matters`, and optional `subvenue`, identifiers, assets, frequency, tasks, methods, datasets, code, or project links only when verified.

Do not store abstracts. Do not create a record if official acceptance evidence is absent.

- [ ] **Step 5: Finalize all 2024 coverage records**

For each venue, list every official audit entry point in `official_sources`, list only reviewed track families in `tracks_checked`, set `checked_on` to the actual audit date, and write a precise boundary note. Use `complete` when at least one paper was included and `no-eligible-papers` when a full official review found none. A 2024 unit may remain `pending` only if an official source is demonstrably unavailable; the note must name that missing source.

- [ ] **Step 6: Validate, render, and inspect the 2024 matrix**

Run:

```bash
python3 scripts/validate.py
python3 scripts/render.py
python3 scripts/render.py --check
python3 -m unittest discover -s tests -v
rg -n "2024|Pending|No eligible papers" README.md papers/2024
```

Expected: validation and tests pass; every 2024 matrix cell is visible; every non-zero cell links to a generated page.

- [ ] **Step 7: Commit the 2024 research batch**

```bash
git add data/papers.yaml data/coverage.yaml README.md papers/2024
git commit -m "data: add verified 2024 conference coverage"
```

---

### Task 5: Curate and Verify All 2025 Venue Units

**Files:**
- Modify: `data/papers.yaml`
- Modify: `data/coverage.yaml`
- Regenerate: `README.md`
- Create or regenerate: `papers/2025/*.md`

**Interfaces:**
- Consumes: the same evidence hierarchy and scope rubric as Task 4, applied to 2025 official venues.
- Produces: complete 2025 paper records and final evidence-backed status for all 11 units.

- [ ] **Step 1: Run the same three venue-family audits for 2025**

Audit ICML/NeurIPS/ICLR/AISTATS, KDD/AAAI/IJCAI, and WWW/WSDM/SIGIR/ACM ICAIF in parallel. Review main proceedings and officially linked workshops, position tracks, and affinity events that publish accepted-paper metadata.

- [ ] **Step 2: Apply the fixed discovery vocabulary and direct-decision test**

Use the exact discovery terms from Task 4. Include a paper only if its method or evaluation directly supports portfolio, asset, trading, execution, derivatives, pricing, hedging, market simulation, or market-risk decisions. A finance dataset alone is insufficient.

- [ ] **Step 3: Add accepted records and adjudicate conflicts**

Transcribe official titles and ordered authors, assign stable IDs with the normalized venue slug, and add original summaries and relevance notes. Use `subvenue` for named non-main events. Resolve source conflicts by the evidence precedence in the global constraints.

- [ ] **Step 4: Finalize all 2025 coverage records**

Populate sources, tracks, date, note, and either `complete` or `no-eligible-papers` for every fully available venue. Use `pending` only when the official material required for a defensible audit cannot be obtained, and identify the missing material in the note.

- [ ] **Step 5: Validate, render, and inspect 2025 output**

Run:

```bash
python3 scripts/validate.py
python3 scripts/render.py
python3 scripts/render.py --check
python3 -m unittest discover -s tests -v
rg -n "2025|Pending|No eligible papers" README.md papers/2025
```

Expected: validation and tests pass; all 2025 cells appear; all included records have generated venue pages.

- [ ] **Step 6: Commit the 2025 research batch**

```bash
git add data/papers.yaml data/coverage.yaml README.md papers/2025
git commit -m "data: add verified 2025 conference coverage"
```

---

### Task 6: Curate Available 2026 Venues and Preserve Honest Pending States

**Files:**
- Modify: `data/papers.yaml`
- Modify: `data/coverage.yaml`
- Regenerate: `README.md`
- Create or regenerate: `papers/2026/*.md`

**Interfaces:**
- Consumes: official venue state available on the audit date.
- Produces: verified available 2026 records, preserved ICML seed, and explicit pending status for incomplete future programs.

- [ ] **Step 1: Re-audit the existing ICML 2026 seed**

Confirm that all 23 existing records retain official acceptance evidence, exact authors, and correct main/position/workshop labels. Add `subvenue` to non-main records when the official workshop or special-track name is available. Do not remove or rewrite a record without documenting the official evidence that requires the correction.

- [ ] **Step 2: Audit every other 2026 venue using currently available official material**

Use the same three venue families, discovery terms, evidence hierarchy, and direct-decision test as Tasks 4 and 5. Include papers whose acceptance is official even if the proceedings PDF is not yet public.

- [ ] **Step 3: Mark incomplete 2026 units pending**

For a conference whose final accepted-paper list, proceedings, or required affiliated-event material is not yet available, keep `status: pending`. Record the official pages checked and state exactly which result is unavailable. A pending unit may contain already verified papers; its count must remain visible in the README matrix.

- [ ] **Step 4: Finalize available units and add verified records**

Use `complete` or `no-eligible-papers` only after the available official program supports a full audit. Add all passing paper mappings with the same metadata standard used in prior years.

- [ ] **Step 5: Validate, render, and inspect 2026 output**

Run:

```bash
python3 scripts/validate.py
python3 scripts/render.py
python3 scripts/render.py --check
python3 -m unittest discover -s tests -v
rg -n "2026|Pending|No eligible papers" README.md papers/2026
```

Expected: all commands pass; the original ICML records remain present; unavailable conference results are visibly pending rather than silently empty.

- [ ] **Step 6: Commit the 2026 research batch**

```bash
git add data/papers.yaml data/coverage.yaml README.md papers/2026
git commit -m "data: expand verified 2026 conference coverage"
```

---

### Task 7: Document the Maintenance Workflow and Lock Down Generated Output

**Files:**
- Modify: `docs/metadata.md`
- Modify: `CONTRIBUTING.md`
- Modify: `tests/test_render.py`
- Regenerate: `README.md`
- Regenerate: `papers/2024/*.md`
- Regenerate: `papers/2025/*.md`
- Regenerate: `papers/2026/*.md`

**Interfaces:**
- Produces: contributor-facing definitions for coverage statuses, evidence, `subvenue`, and the two-file generation workflow.

- [ ] **Step 1: Add a failing documentation rendering assertion**

In `test_readme_is_polished_browsable_and_complete`, require links to both canonical data files:

```python
self.assertIn("data/papers.yaml", rendered)
self.assertIn("data/coverage.yaml", rendered)
```

Run the focused test and confirm the coverage link is absent.

- [ ] **Step 2: Update metadata documentation**

Document every coverage field, the three statuses, their count invariants, official-source precedence, allowed years and venues, `tracks_checked`, `subvenue`, and the rule that topics represent the paper's quantitative-finance fields.

- [ ] **Step 3: Update contribution instructions**

Require contributors to edit `data/papers.yaml` for papers and `data/coverage.yaml` only when they performed a systematic venue audit. Add this exact local command sequence:

```bash
python3 scripts/validate.py
python3 scripts/render.py
python3 scripts/render.py --check
python3 -m unittest discover -s tests -v
```

State that an arXiv page alone cannot prove acceptance and that a pending unit must not be changed to a final status without reviewing the official source set.

- [ ] **Step 4: Update generated contribution copy and regenerate**

Make the README contribution section link both YAML sources and explain their separate roles. Regenerate all pages and run the focused test.

- [ ] **Step 5: Run the full local verification gate**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
python3 scripts/render.py --check
git diff --check
git status --short
```

Expected: zero test failures, valid paper and coverage counts, current generated files, no whitespace errors, and only intended task files modified.

- [ ] **Step 6: Commit the maintenance documentation**

```bash
git add docs/metadata.md CONTRIBUTING.md tests/test_render.py scripts/render.py README.md papers/2024 papers/2025 papers/2026
git commit -m "docs: explain multi-conference catalog maintenance"
```

---

### Task 8: Audit Scope, Merge to Main, and Verify the Public Repository

**Files:**
- Review: all changes from `main...codex/expand-2024-2026`
- Publish: Git branch and GitHub repository state only after verification succeeds.

**Interfaces:**
- Produces: updated public `main`, matching local/remote SHA, and successful GitHub Actions validation.

- [ ] **Step 1: Run the final requirements checklist**

Confirm from deterministic output that:

- `data/coverage.yaml` contains exactly 33 unique units;
- README lists all 11 venues and all three years;
- each paper-bearing venue-year has a generated page;
- no paper falls outside 2024–2026;
- every `complete` unit has papers and every `no-eligible-papers` unit has none;
- each pending 2026 note names unavailable official material; and
- the 23 original ICML 2026 IDs are still present unless a committed correction explains the change.

- [ ] **Step 2: Run fresh completion verification**

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
python3 scripts/render.py --check
git diff --check
git status --short --branch
git log --oneline main..HEAD
```

Expected: every command succeeds and the worktree is clean.

- [ ] **Step 3: Obtain two-stage review**

Use a spec-compliance reviewer first and a code/data-quality reviewer second. Resolve every Critical or Important finding, rerun the full verification gate, and commit each evidence-backed correction.

- [ ] **Step 4: Fast-forward local main and push**

```bash
git switch main
git merge --ff-only codex/expand-2024-2026
git push origin main
```

Expected: `origin/main` advances to the verified expansion commit without a merge commit.

- [ ] **Step 5: Verify GitHub state and Actions**

```bash
gh repo view sjsj0101/good-quant-ai-papers \
  --json nameWithOwner,visibility,url,defaultBranchRef
gh api repos/sjsj0101/good-quant-ai-papers/commits/main --jq .sha
gh run list --repo sjsj0101/good-quant-ai-papers --limit 5 \
  --json databaseId,status,conclusion,workflowName,headSha,url
```

Expected: repository is `PUBLIC`, default branch is `main`, remote SHA equals local `git rev-parse HEAD`, and the `Validate` run for that SHA concludes `success`.

- [ ] **Step 6: Verify anonymous visibility**

Issue an unauthenticated HTTP request to the repository URL and require status 200. Inspect the public README to confirm that the coverage matrix and non-ICML venue pages are visible.
