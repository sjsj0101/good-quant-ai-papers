# good-quant-ai-papers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, publish, and verify a polished public GitHub catalog of top-conference quantitative-finance and asset-management papers at `sjsj0101/good-quant-ai-papers`.

**Architecture:** A single YAML catalog is the source of truth. Small Python programs validate records and deterministically render a polished README plus year/venue pages; tests and GitHub Actions keep data and generated views synchronized. The first release contains 23 verified ICML 2026 records and no PDFs or copied abstracts.

**Tech Stack:** Python 3.11+, PyYAML 6.0.3, `unittest`, YAML, JSON Schema documentation, Markdown, GitHub Actions, GitHub CLI or authenticated GitHub web UI.

## Global Constraints

- The remote repository must be public and named exactly `sjsj0101/good-quant-ai-papers`.
- Scope is quantitative finance and asset management only.
- Initial venues are ICML, NeurIPS, ICLR, KDD, AAAI, IJCAI, WWW, WSDM, SIGIR, AISTATS, and ACM ICAIF.
- Store metadata, original summaries, and links; never store PDFs or copied full abstracts.
- `data/papers.yaml` is the only paper-data source of truth.
- The initial seed is exactly the 23 ICML 2026 records listed in the approved design.
- Workshop, position, and main-track records must remain visibly distinct.
- Validation and rendering must work without network access.
- Curated content is licensed CC BY 4.0.

---

## File Map

- `requirements-dev.txt`: one pinned parser dependency.
- `data/papers.yaml`: canonical paper catalog.
- `schema/paper.schema.json`: public metadata contract.
- `scripts/catalog.py`: YAML loading, normalization, and validation library.
- `scripts/validate.py`: command-line validation entry point.
- `scripts/render.py`: deterministic README and venue-page renderer.
- `tests/test_validate.py`: catalog validation and duplicate tests.
- `tests/test_render.py`: formatting, grouping, and stale-output tests.
- `README.md`: generated landing page with badges, navigation, and recent-paper table.
- `papers/2026/icml.md`: generated detailed ICML 2026 list.
- `docs/metadata.md`: field and taxonomy reference.
- `CONTRIBUTING.md`: inclusion and contribution rules.
- `LICENSE`: CC BY 4.0 text.
- `.github/workflows/validate.yml`: offline CI validation and render check.

### Task 1: Catalog Validation Core

**Files:**
- Create: `requirements-dev.txt`
- Create: `schema/paper.schema.json`
- Create: `scripts/__init__.py`
- Create: `scripts/catalog.py`
- Create: `scripts/validate.py`
- Create: `tests/test_validate.py`

**Interfaces:**
- Produces: `load_catalog(path: Path) -> list[dict]`
- Produces: `validate_catalog(records: list[dict]) -> list[str]`
- Produces: `validate_file(path: Path) -> list[str]`

- [ ] **Step 1: Add failing validator tests**

Create tests covering one valid record, a missing required field, an invalid enum, malformed URL, and normalized-title duplication. The shared valid fixture is:

```python
VALID = {
    "id": "2026-icml-hwang-signature-informed-transformer",
    "title": "Signature-Informed Transformer for Asset Allocation",
    "authors": ["Yoontae Hwang", "Stefan Zohren"],
    "venue": "ICML",
    "year": 2026,
    "track": "main",
    "presentation": "poster",
    "official_url": "https://icml.cc/virtual/2026/poster/62694",
    "paper_url": "https://openreview.net/forum?id=eBM5ALLJNx",
    "topics": ["asset-allocation", "portfolio-optimization"],
    "summary": "End-to-end asset allocation with path signatures and a risk-aware objective.",
    "why_it_matters": "Aligns training with downstream portfolio risk.",
    "status": "accepted",
    "verified_on": "2026-07-11",
}
```

- [ ] **Step 2: Verify tests fail**

Run: `python3 -m unittest tests.test_validate -v`

Expected: import failure for `scripts.catalog` or missing functions.

- [ ] **Step 3: Implement loading and validation**

`scripts/catalog.py` must define exact required fields and controlled sets from the design. `validate_catalog` returns readable errors formatted as `<record-id>: <field>: <message>`. It validates non-empty author/topic lists, integer year, ISO date, HTTP(S) URLs, enums, stable ID shape, and duplicates across ID, normalized title, official URL, and paper URL.

`scripts/validate.py` loads `data/papers.yaml`, prints `Catalog valid: N papers` on success, otherwise prints every error and exits 1.

- [ ] **Step 4: Add the public schema**

Create a Draft 2020-12 JSON Schema with `additionalProperties: false`, the same required fields, URL formats, controlled enum fields, and optional arrays/URLs defined in the design.

- [ ] **Step 5: Run validator tests**

Run: `python3 -m unittest tests.test_validate -v`

Expected: all tests pass.

- [ ] **Step 6: Commit validation core**

```bash
git add requirements-dev.txt schema scripts tests/test_validate.py
git commit -m "feat: add paper catalog validation"
```

### Task 2: Verified ICML 2026 Seed

**Files:**
- Create: `data/papers.yaml`

**Interfaces:**
- Consumes: metadata contract and `validate_file` from Task 1.
- Produces: exactly 23 validated records.

- [ ] **Step 1: Add the 23 approved records**

Use the exact title set in `docs/superpowers/specs/2026-07-11-good-quant-ai-papers-design.md`. Use official ICML poster pages for main/position records and these workshop paper pages:

| Paper | Paper page | Presentation |
|---|---|---|
| Forecast-to-Trade | `https://openreview.net/forum?id=pTiRAPtDzK` | spotlight |
| One Token per Trade | `https://openreview.net/forum?id=ZMEIc25o0a` | poster |
| TradeFM | `https://openreview.net/forum?id=anK6dppdfa` | poster |
| DELPHYNE | `https://openreview.net/forum?id=DPrS5jDoR3` | poster |
| Leakage-Aware Benchmarking | `https://openreview.net/forum?id=mi8QiWomm3` | poster |
| Reflexivity as Prompt | `https://openreview.net/forum?id=cqnuY2xFQl` | poster |
| Mechanism-Inspired Aggregation | `https://openreview.net/forum?id=mbstEcHW0R` | poster |
| Learning to Trade Like an Expert | `https://openreview.net/forum?id=01bO7bdq4e` | poster |
| Behavioral Proxy Conditioning | `https://openreview.net/forum?id=xrwkOUb8kp` | poster |

Every record must include original `summary` and `why_it_matters` text, accurate authors in accepted-record order, at least one topic, and `verified_on: 2026-07-11`. Workshop names and non-archival status go in `notes` where applicable.

- [ ] **Step 2: Validate the seed**

Run: `python3 scripts/validate.py`

Expected: `Catalog valid: 23 papers`.

- [ ] **Step 3: Deterministically verify count and uniqueness**

Run: `python3 -c "from pathlib import Path; from scripts.catalog import load_catalog, validate_catalog; p=load_catalog(Path('data/papers.yaml')); assert len(p)==23; assert not validate_catalog(p); print('23 unique verified records')"`

Expected: `23 unique verified records`.

- [ ] **Step 4: Commit the seed**

```bash
git add data/papers.yaml
git commit -m "data: seed verified ICML 2026 papers"
```

### Task 3: Deterministic Markdown Renderer

**Files:**
- Create: `scripts/render.py`
- Create: `tests/test_render.py`
- Create: `README.md`
- Create: `papers/2026/icml.md`

**Interfaces:**
- Consumes: `load_catalog` and `validate_catalog` from `scripts.catalog`.
- Produces: `render_readme(records: list[dict]) -> str`
- Produces: `render_venue_pages(records: list[dict]) -> dict[Path, str]`
- Produces: CLI `python3 scripts/render.py [--check]`.

- [ ] **Step 1: Add failing renderer tests**

Tests must assert that:

- README contains the centered project title, scope statement, badges, topic navigation, and a 23-paper count;
- paper rows link titles and distinguish Main, Workshop, and Position;
- `papers/2026/icml.md` contains all records in deterministic title order within track sections;
- Markdown table pipes in text are escaped;
- `--check` detects a stale output file.

- [ ] **Step 2: Verify renderer tests fail**

Run: `python3 -m unittest tests.test_render -v`

Expected: import failure or missing renderer functions.

- [ ] **Step 3: Implement the renderer**

The README layout is:

```markdown
<div align="center">

# Good Quant AI Papers

Curated top-conference research for quantitative finance and asset management.

[paper-count badge] [venue-count badge] [last-verified badge] [CC BY 4.0 badge]

</div>

## Scope
## Browse by Topic
## ICML 2026
## Browse by Year and Venue
## Contributing
## License
```

Use compact tables with columns `Paper`, `Track`, `Focus`, `Assets / Frequency`, and `Why it matters`. Use original summaries, never abstracts. Venue pages include source links, code links when present, and factual notes.

- [ ] **Step 4: Generate outputs**

Run: `python3 scripts/render.py`

Expected: writes `README.md` and `papers/2026/icml.md` and reports `Rendered 2 files`.

- [ ] **Step 5: Run tests and freshness check**

Run: `python3 -m unittest tests.test_render -v`

Expected: all tests pass.

Run: `python3 scripts/render.py --check`

Expected: `Generated files are current`.

- [ ] **Step 6: Commit rendered views**

```bash
git add scripts/render.py tests/test_render.py README.md papers/2026/icml.md
git commit -m "feat: render polished paper indexes"
```

### Task 4: Documentation and Contribution Policy

**Files:**
- Create: `docs/metadata.md`
- Create: `CONTRIBUTING.md`
- Create: `LICENSE`

**Interfaces:**
- Consumes: field names and taxonomies from `scripts.catalog` and the schema.
- Produces: contributor-facing rules with no conflicting source of truth.

- [ ] **Step 1: Document every field and controlled value**

`docs/metadata.md` must explain required and optional fields, stable-ID construction, topic definitions, asset/frequency enums, official-source priority, and one complete valid YAML example.

- [ ] **Step 2: Write contribution rules**

`CONTRIBUTING.md` must include the inclusion test, explicit exclusions, no-PDF/no-copied-abstract policy, YAML-only edit workflow, commands to install/validate/render/test, and separate labeling for main/workshop/position tracks.

- [ ] **Step 3: Add CC BY 4.0 license**

Use the official Creative Commons Attribution 4.0 International legal text and identify the licensed material as repository-authored metadata curation, summaries, and documentation.

- [ ] **Step 4: Verify docs match implementation**

Run: `rg -n "data/papers.yaml|scripts/validate.py|scripts/render.py|main|workshop|position|PDF" CONTRIBUTING.md docs/metadata.md`

Expected: every workflow and boundary appears in the documentation.

- [ ] **Step 5: Commit docs**

```bash
git add CONTRIBUTING.md LICENSE docs/metadata.md
git commit -m "docs: add metadata and contribution guides"
```

### Task 5: Offline GitHub Actions Quality Gate

**Files:**
- Create: `.github/workflows/validate.yml`

**Interfaces:**
- Runs on: pushes and pull requests.
- Produces: a single `validate` job on Ubuntu with Python 3.11.

- [ ] **Step 1: Create the workflow**

The job checks out the repository, sets up Python 3.11, installs `requirements-dev.txt`, then runs:

```bash
python3 scripts/validate.py
python3 scripts/render.py --check
python3 -m unittest discover -s tests -v
```

- [ ] **Step 2: Validate workflow syntax and local equivalents**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/validate.yml')); print('workflow yaml valid')"`

Expected: `workflow yaml valid`.

Run all three workflow commands locally and expect success.

- [ ] **Step 3: Commit CI**

```bash
git add .github/workflows/validate.yml
git commit -m "ci: validate catalog and generated indexes"
```

### Task 6: Completion Verification

**Files:**
- Modify only files that fail verification.

**Interfaces:**
- Produces: a clean, reproducible local `main` branch ready to publish.

- [ ] **Step 1: Run the complete test matrix**

```bash
python3 scripts/validate.py
python3 scripts/render.py --check
python3 -m unittest discover -s tests -v
git diff --check
```

Expected: 23 valid papers, current generated files, all tests passing, and no whitespace errors.

- [ ] **Step 2: Audit scope and prohibited files**

Run: `find . -type f -not -path './.git/*' -print | sort`

Expected: only planned repository files; no `.pdf`, credentials, caches, or private artifacts.

Run: `git status --short --branch`

Expected: clean `main` branch.

- [ ] **Step 3: Review rendered README**

Confirm that the landing page visibly shows the repository purpose, 23-paper count, venue/track separation, topic navigation, contribution instructions, and CC BY 4.0 license.

### Task 7: Create, Push, and Verify the Public GitHub Repository

**Files:**
- Configure: Git remote `origin`.

**Interfaces:**
- Produces: public URL `https://github.com/sjsj0101/good-quant-ai-papers`.

- [ ] **Step 1: Confirm GitHub identity and repository absence**

Run: `gh auth status`

Expected: authenticated as `sjsj0101`. If the stored CLI token is invalid, authenticate through the existing signed-in GitHub browser session or run `gh auth login -h github.com -w` and complete the GitHub device authorization.

Run: `gh repo view sjsj0101/good-quant-ai-papers`

Expected before creation: repository not found.

- [ ] **Step 2: Create and push the public repository**

Run:

```bash
gh repo create sjsj0101/good-quant-ai-papers --public --source=. --remote=origin --push --description "Curated top-conference papers for quantitative finance and asset management"
```

Expected: repository URL and successful push of `main`.

- [ ] **Step 3: Verify visibility and default branch**

Run:

```bash
gh repo view sjsj0101/good-quant-ai-papers --json nameWithOwner,visibility,url,defaultBranchRef
```

Expected: `visibility` is `PUBLIC`, URL is `https://github.com/sjsj0101/good-quant-ai-papers`, and default branch is `main`.

- [ ] **Step 4: Verify anonymous visibility and workflow state**

Open `https://github.com/sjsj0101/good-quant-ai-papers` without relying on private connector state and confirm HTTP success and rendered README. Then run `gh run list --repo sjsj0101/good-quant-ai-papers --limit 5` and inspect the validation workflow until it completes successfully.

- [ ] **Step 5: Final remote/local consistency check**

Run: `git status --short --branch`

Expected: clean `main` tracking `origin/main`.

Run: `git rev-parse HEAD` and compare it with the remote default branch SHA returned by GitHub. They must match.
