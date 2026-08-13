# Link-Only Paper Contribution MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a GitHub visitor submit one paper URL, automate reliable base-metadata extraction and duplicate checks, and let an authorized maintainer create a partial-record draft PR for manual completion.

**Architecture:** A read-only Issue workflow runs a small Python metadata pipeline and synchronizes one managed comment plus one machine-state label. A separate maintainer-gated workflow re-runs the same pipeline, appends a syntactically valid partial YAML record, and uses GitHub CLI to create or update one draft PR. Existing catalog validation remains unchanged and intentionally blocks merge until a maintainer completes the extended metadata and rendered files.

**Tech Stack:** Python 3.11, Python standard library, PyYAML 6.0.3, `unittest`, GitHub Issue Forms, GitHub Actions, GitHub REST API, GitHub CLI.

## Global Constraints

- Work from the approved MVP design in `docs/superpowers/specs/2026-08-13-link-contribution-ingestion-design.md`.
- Preserve `data/papers.yaml` as the only canonical paper catalog and never hand-edit generated Markdown.
- Never change `data/coverage.yaml` for an individual suggestion.
- Accept exactly one HTTPS URL and fetch only recognized public source hosts.
- Extract bibliographic facts only; do not infer conference acceptance or topical eligibility.
- Do not add AI/model dependencies, AI configuration, automatic summaries, classifications, or scope advice.
- Base metadata is title, at least one author, controlled venue, year 2024--2026, and a canonical paper URL.
- Exact duplicates block PR creation; possible title matches remain a maintainer decision and must be visible in the Issue report and PR body.
- Only a repository actor with `write`, `maintain`, or `admin` permission may trigger repository writes through the `approved` label.
- The approval workflow opens a draft PR containing a partial record; it never writes directly to `main`, never merges, and never weakens existing CI.
- Do not persist HTML, PDFs, copied abstracts, credentials, raw upstream bodies, or third-party prose.
- Keep URL controls minimal and local: HTTPS, allowlisted host, public IP, bounded redirects/timeouts/body size.
- Final offline gates remain `python3 scripts/validate.py`, `python3 scripts/render.py --check`, `python3 -m unittest discover -s tests -v`, and `git diff --check`.

## File Map

- `scripts/contributions/models.py`: immutable base-metadata and pipeline-result contracts with strict JSON serialization.
- `scripts/contributions/issue_form.py`: strict parser for the stable Issue Form headings.
- `scripts/contributions/http.py`: bounded HTTPS fetcher for recognized public hosts.
- `scripts/contributions/sources.py`: OpenReview, arXiv, Crossref/DOI, and official-page base-metadata adapters.
- `scripts/contributions/check.py`: metadata-readiness and catalog duplicate checks; no scope or acceptance policy.
- `scripts/contributions/report.py`: managed Issue comment and five-label state derivation.
- `scripts/contributions/github.py`: minimal GitHub REST operations for the managed comment, labels, and actor permission.
- `scripts/contributions/materialize.py`: partial-record YAML append and stable branch/record slug generation.
- `scripts/contributions/cli.py`: workflow-facing `inspect-event`, `sync-issue`, `authorize-event`, and `materialize` commands.
- `.github/ISSUE_TEMPLATE/paper-suggestion.yml`: one-link visitor form with fixed Issue-title prefix.
- `.github/workflows/inspect-paper-suggestion.yml`: read-only metadata workflow.
- `.github/workflows/materialize-paper-suggestion.yml`: maintainer-gated draft-PR workflow.
- `scripts/render.py`, `README.md`, and `CONTRIBUTING.md`: generated entry point and maintainer instructions.
- `tests/contributions/`: offline fixtures, units, integrations, and static workflow contracts.

---

### Task 1: Issue Form and Strict Data Contracts

**Files:**
- Create: `scripts/contributions/__init__.py`
- Create: `scripts/contributions/models.py`
- Create: `scripts/contributions/issue_form.py`
- Create: `tests/contributions/__init__.py`
- Create: `tests/contributions/test_issue_form.py`

**Interfaces:**
- Produces: `Submission(paper_url: str)`.
- Produces: `BaseMetadata`, `DuplicateResult`, and `InspectionResult` frozen dataclasses.
- Produces: `InspectionResult.to_dict() -> dict[str, object]` and `InspectionResult.from_dict(value: object) -> InspectionResult` with `RESULT_VERSION = 1` and strict type checks.
- Produces: `parse_issue_form(body: str) -> Submission`, raising `SubmissionError(code: str)`.
- Consumes headings `### Paper URL` and `### Scope acknowledgement`.

- [ ] **Step 1: Write failing form and serialization tests**

```python
class IssueFormTests(unittest.TestCase):
    def test_parses_one_https_url_and_checked_acknowledgement(self):
        body = """### Paper URL

https://openreview.net/forum?id=abc123

### Scope acknowledgement

- [x] I understand maintainers decide scope and venue eligibility.
"""
        self.assertEqual(
            parse_issue_form(body),
            Submission("https://openreview.net/forum?id=abc123"),
        )

    def test_rejects_http_multiple_urls_duplicate_headings_and_unchecked_scope(self):
        invalid_bodies = (
            VALID_BODY.replace("https://", "http://"),
            VALID_BODY.replace("\n\n### Scope", " https://arxiv.org/abs/2401.1\n\n### Scope"),
            VALID_BODY + "\n### Paper URL\n\nhttps://doi.org/10.1/x\n",
            VALID_BODY.replace("- [x]", "- [ ]"),
        )
        for body in invalid_bodies:
            with self.subTest(body=body), self.assertRaises(SubmissionError):
                parse_issue_form(body)

    def test_result_round_trip_rejects_bool_version_and_string_authors(self):
        payload = READY_RESULT.to_dict()
        self.assertEqual(InspectionResult.from_dict(payload), READY_RESULT)
        for version in (True, 1.0, "1"):
            malformed = {**payload, "version": version}
            with self.assertRaises(ResultError):
                InspectionResult.from_dict(malformed)
        malformed = {**payload, "metadata": {**payload["metadata"], "authors": "Ada"}}
        with self.assertRaises(ResultError):
            InspectionResult.from_dict(malformed)
```

- [ ] **Step 2: Run the focused test and observe the missing module**

Run: `python3 -m unittest tests.contributions.test_issue_form -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.contributions'`.

- [ ] **Step 3: Implement only the contracts and strict form parser**

```python
@dataclass(frozen=True)
class Submission:
    paper_url: str


@dataclass(frozen=True)
class BaseMetadata:
    submitted_url: str
    canonical_url: str | None
    title: str | None
    authors: tuple[str, ...]
    venue: str | None
    year: int | None
    paper_url: str | None
    official_url: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    openreview_id: str | None = None
    track: str | None = None
    subvenue: str | None = None
    presentation: str | None = None
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class DuplicateResult:
    status: str
    matching_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class InspectionResult:
    version: int
    submission: Submission
    metadata: BaseMetadata
    missing_fields: tuple[str, ...]
    duplicate: DuplicateResult
    metadata_ready: bool
```

`parse_issue_form()` must require exactly one occurrence of each required
heading, exactly one URL token, `https` scheme, no credentials, a non-empty
hostname, and at least one checked box in the acknowledgement section. Omit all
abstract, contributor-note, scope, acceptance, enrichment, and record fields
from these contracts.

- [ ] **Step 4: Run focused and existing tests**

Run: `python3 -m unittest tests.contributions.test_issue_form tests.test_validate tests.test_render -v`

Expected: PASS.

- [ ] **Step 5: Commit the contracts**

```bash
git add scripts/contributions/__init__.py scripts/contributions/models.py scripts/contributions/issue_form.py tests/contributions
git commit -m "feat: parse paper suggestion issues"
```

---

### Task 2: Bounded Base-Metadata Sources

**Files:**
- Create: `scripts/contributions/http.py`
- Create: `scripts/contributions/sources.py`
- Create: `tests/contributions/fixtures/openreview-note.json`
- Create: `tests/contributions/fixtures/arxiv-entry.xml`
- Create: `tests/contributions/fixtures/crossref-work.json`
- Create: `tests/contributions/fixtures/official-paper.html`
- Create: `tests/contributions/test_http.py`
- Create: `tests/contributions/test_sources.py`

**Interfaces:**
- Consumes: `BaseMetadata` from Task 1.
- Produces: `SafeFetcher.get(url: str, *, accepted_hosts: frozenset[str]) -> HttpResponse`.
- Produces: `extract_metadata(url: str, fetcher: SafeFetcher) -> BaseMetadata`.
- Produces: `SourceError(code: str)` with stable non-secret codes.

- [ ] **Step 1: Write failing fetch-policy and adapter tests**

```python
class SourceTests(unittest.TestCase):
    def test_extracts_openreview_base_metadata_without_acceptance_decision(self):
        result = extract_metadata(OPENREVIEW_URL, fixture_fetcher("openreview-note.json"))
        self.assertEqual(result.title, "Portfolio Learning")
        self.assertEqual(result.authors, ("Ada A.", "Bo B."))
        self.assertEqual(result.venue, "ICML")
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.openreview_id, "abc123")
        self.assertFalse(hasattr(result, "venue_verified"))

    def test_rejects_unknown_host_private_ip_http_redirect_and_oversized_body(self):
        for fetcher, url in SAFETY_CASES:
            with self.subTest(url=url), self.assertRaises(SourceError):
                extract_metadata(url, fetcher)
```

Add fixture-backed cases for arXiv, DOI/Crossref, a controlled-conference HTML
page, missing authors, and missing venue. Assert that returned/serialized
objects contain no abstract or raw response body.

- [ ] **Step 2: Run source tests and observe missing modules**

Run: `python3 -m unittest tests.contributions.test_http tests.contributions.test_sources -v`

Expected: FAIL because `http.py` and `sources.py` do not exist.

- [ ] **Step 3: Implement the minimal safe fetcher**

```python
MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 2_000_000
CONNECT_TIMEOUT_SECONDS = 5
READ_TIMEOUT_SECONDS = 15

ALLOWED_SOURCE_HOSTS = frozenset({
    "openreview.net", "api.openreview.net", "api2.openreview.net",
    "arxiv.org", "export.arxiv.org", "doi.org", "api.crossref.org",
    "icml.cc", "neurips.cc", "iclr.cc", "kdd.org", "aaai.org",
    "ijcai.org", "thewebconf.org", "wsdm-conference.org",
    "sigir.org", "aistats.org", "icaif.org",
})
```

Require HTTPS at the original and every redirect hop, resolve the hostname
before connecting, reject every non-global address, keep the hostname as TLS
SNI/Host, and stop after the declared redirect/body/time bounds. Follow a
trusted source subdomain only when its hostname is exactly trusted or ends in a
dot plus the trusted hostname; never accept suffix lookalikes.

- [ ] **Step 4: Implement source-specific bibliographic extraction**

OpenReview reads public note content; arXiv reads the Atom entry; DOI reads
Crossref; official HTML reads citation meta tags (`citation_title`,
`citation_author`, `citation_conference_title`, `citation_publication_date`,
`citation_pdf_url`, `citation_doi`). Normalize controlled venue aliases through
one explicit map imported from `scripts.catalog.VENUES`. Do not derive an
acceptance boolean, scope field, summary, taxonomy, or status.

```python
def extract_metadata(url: str, fetcher: SafeFetcher) -> BaseMetadata:
    parsed = validated_https_url(url)
    if parsed.hostname == "openreview.net":
        return _from_openreview(url, fetcher)
    if parsed.hostname == "arxiv.org":
        return _from_arxiv(url, fetcher)
    if parsed.hostname == "doi.org":
        return _from_crossref(url, fetcher)
    if _is_controlled_conference_host(parsed.hostname):
        return _from_citation_meta(url, fetcher)
    raise SourceError("unsupported-source")
```

- [ ] **Step 5: Run focused tests and compile checks**

Run: `python3 -m unittest tests.contributions.test_http tests.contributions.test_sources -v`

Run: `python3 -m py_compile scripts/contributions/http.py scripts/contributions/sources.py`

Expected: both commands PASS.

- [ ] **Step 6: Commit source extraction**

```bash
git add scripts/contributions/http.py scripts/contributions/sources.py tests/contributions
git commit -m "feat: extract paper base metadata"
```

---

### Task 3: Readiness and Duplicate Inspection

**Files:**
- Create: `scripts/contributions/check.py`
- Create: `tests/contributions/test_check.py`

**Interfaces:**
- Consumes: `Submission`, `BaseMetadata`, `DuplicateResult`, and `InspectionResult`.
- Consumes: `load_catalog(path: Path) -> list[dict]` from `scripts.catalog`.
- Produces: `normalize_title(value: str) -> str`.
- Produces: `check_duplicates(metadata: BaseMetadata, records: list[dict]) -> DuplicateResult`.
- Produces: `inspect_submission(submission: Submission, metadata: BaseMetadata, records: list[dict]) -> InspectionResult`.

- [ ] **Step 1: Write failing readiness and duplicate tests**

```python
class InspectionTests(unittest.TestCase):
    def test_base_fields_are_the_only_readiness_gate(self):
        result = inspect_submission(SUBMISSION, COMPLETE_METADATA, [])
        self.assertEqual(result.missing_fields, ())
        self.assertTrue(result.metadata_ready)
        self.assertFalse(hasattr(result, "scope_assessment"))
        self.assertFalse(hasattr(result, "venue_verified"))

    def test_exact_identifier_url_and_normalized_title_matches_block(self):
        for metadata in (SAME_DOI, SAME_OPENREVIEW, SAME_ARXIV, SAME_URL, SAME_TITLE):
            with self.subTest(metadata=metadata):
                duplicate = check_duplicates(metadata, EXISTING_RECORDS)
                self.assertEqual(duplicate.status, "duplicate")

    def test_conservative_similar_title_is_possible_not_duplicate(self):
        duplicate = check_duplicates(SIMILAR_TITLE, EXISTING_RECORDS)
        self.assertEqual(duplicate.status, "possible")
```

Also cover missing title/authors/venue/year/paper URL, invalid controlled venue,
out-of-range year, URL normalization preserving path/query case, and generated
ID collision detection at materialization recheck time.

- [ ] **Step 2: Run the focused test and observe the missing module**

Run: `python3 -m unittest tests.contributions.test_check -v`

Expected: FAIL with `ModuleNotFoundError` for `scripts.contributions.check`.

- [ ] **Step 3: Implement deterministic inspection only**

```python
BASE_FIELDS = ("title", "authors", "venue", "year", "paper_url")
EXACT_FIELDS = ("doi", "openreview_id", "arxiv_id")

def inspect_submission(submission, metadata, records):
    missing = missing_base_fields(metadata)
    duplicate = check_duplicates(metadata, records)
    ready = not missing and duplicate.status != "duplicate"
    return InspectionResult(
        version=RESULT_VERSION,
        submission=submission,
        metadata=metadata,
        missing_fields=missing,
        duplicate=duplicate,
        metadata_ready=ready,
    )
```

Use NFKC/casefold/alphanumeric title normalization. Exact normalized-title
equality is `duplicate`; only a conservative `SequenceMatcher` threshold of
`>= 0.96` with at least six normalized tokens is `possible`. Compare
identifiers case-insensitively and URLs after lowercasing scheme/host, removing
the default HTTPS port and fragment, and preserving path/query bytes and case.

- [ ] **Step 4: Run check, catalog, and validation tests**

Run: `python3 -m unittest tests.contributions.test_check tests.test_validate tests.test_coverage -v`

Expected: PASS.

- [ ] **Step 5: Commit deterministic inspection**

```bash
git add scripts/contributions/check.py tests/contributions/test_check.py
git commit -m "feat: check paper metadata and duplicates"
```

---

### Task 4: Managed Issue Report, Labels, and Workflow CLI

**Files:**
- Create: `scripts/contributions/report.py`
- Create: `scripts/contributions/github.py`
- Create: `scripts/contributions/cli.py`
- Create: `tests/contributions/test_report.py`
- Create: `tests/contributions/test_github.py`
- Create: `tests/contributions/test_cli.py`

**Interfaces:**
- Consumes: source extraction and inspection from Tasks 1--3.
- Produces: `render_report(result: InspectionResult) -> str` with exactly one `<!-- paper-suggestion-report:v1 -->` marker.
- Produces: `render_problem_report(code: str) -> str` for allowlisted form/source failures.
- Produces: `state_label(result: InspectionResult) -> str`, returning exactly one of `metadata-ready`, `needs-metadata`, or `duplicate`.
- Produces: `GitHubClient.sync_issue(issue_number: int, report: str, state: str) -> None`.
- Produces: `GitHubClient.actor_can_write(actor: str) -> bool` accepting base permission `write`, `maintain`, or `admin`.
- Produces CLI commands `inspect-event`, `sync-issue`, and `authorize-event`.

- [ ] **Step 1: Write failing report, REST, and CLI tests**

```python
class ReportTests(unittest.TestCase):
    def test_report_contains_only_base_facts_duplicates_missing_fields_and_next_action(self):
        report = render_report(READY_RESULT)
        self.assertEqual(report.count(REPORT_MARKER), 1)
        self.assertIn("Portfolio Learning", report)
        self.assertIn("ICML", report)
        self.assertNotIn("scope assessment", report.casefold())
        self.assertNotIn("acceptance verified", report.casefold())
        self.assertNotIn("summary suggestion", report.casefold())

    def test_untrusted_metadata_cannot_create_mentions_or_bare_links(self):
        report = render_report(adversarial_result("@owner https://evil.test ~x~"))
        self.assertNotIn("@owner", report)
        self.assertNotIn("https://evil.test", report)
```

GitHub client tests must model real REST semantics: paginate comments and
labels, update the single marker comment, delete only the three old
automation-owned state labels, add the desired label, preserve `approved` and
other human labels, validate exactly one report marker before an API call, and
reject pagination links outside `https://api.github.com/repos/<owner>/<repo>/`.
CLI tests use fixture transports and temporary files; they assert strict event
field types, stable category-only errors, no raw body/response/token in
formatted tracebacks, and no live network. A malformed form must still write a
managed problem report plus `needs-metadata`, must not write a result JSON, and
must not raise a workflow-internal error.

- [ ] **Step 2: Run focused tests and observe missing modules**

Run: `python3 -m unittest tests.contributions.test_report tests.contributions.test_github tests.contributions.test_cli -v`

Expected: FAIL because the report, GitHub, and CLI modules are missing.

- [ ] **Step 3: Implement the minimal report and label state**

Render one fact table for title, authors, venue, year, URLs, and identifiers;
one duplicate section; one missing-fields section; and one maintainer-next-step
section. Escape HTML/Markdown, insert zero-width breaks into untrusted `@`,
`http://`, `https://`, and `~`, and construct trusted submitted/canonical links
only through a dedicated link helper.

```python
REPORT_MARKER = "<!-- paper-suggestion-report:v1 -->"
MACHINE_STATES = frozenset({"metadata-ready", "needs-metadata", "duplicate"})

def state_label(result: InspectionResult) -> str:
    if result.duplicate.status == "duplicate":
        return "duplicate"
    return "metadata-ready" if result.metadata_ready else "needs-metadata"

def render_report(result: InspectionResult) -> str:
    return "\n".join((
        REPORT_MARKER,
        "## Paper metadata check",
        _fact_table(result.metadata),
        _duplicate_section(result.duplicate),
        _missing_section(result.missing_fields),
        _next_action(result),
        "",
    ))
```

- [ ] **Step 4: Implement the small GitHub client**

Use `urllib.request` with `Authorization: Bearer`,
`Accept: application/vnd.github+json`, and `X-GitHub-Api-Version: 2022-11-28`.
Paginate the three relevant collections. Synchronization must validate the
report marker and state label locally before any request, update/create the
managed comment, remove only obsolete machine-state labels, and add the one
desired state. Authorization reads
`GET /repos/{owner}/{repo}/collaborators/{actor}/permission`.

```python
class GitHubClient:
    def sync_issue(self, issue_number: int, report: str, state: str) -> None:
        _validate_managed_report(report)
        _validate_state(state)
        self._upsert_marker_comment(issue_number, report)
        current = self._issue_labels(issue_number)
        for label in sorted((current & MACHINE_STATES) - {state}):
            self._delete_issue_label(issue_number, label)
        if state not in current:
            self._add_issue_label(issue_number, state)

    def actor_can_write(self, actor: str) -> bool:
        return self._collaborator_permission(actor) in {"write", "maintain", "admin"}
```

- [ ] **Step 5: Implement strict JSON-file CLI boundaries**

`inspect-event --event PATH --catalog PATH --result PATH --report PATH --labels PATH`
must parse the Issue body, extract metadata, inspect it, and write a strict
result plus the report/single-label artifacts. A recognized form with a source
failure writes an unresolved `InspectionResult`; a malformed form writes only
an allowlisted problem report and `needs-metadata`. `sync-issue` reads the
report/label artifacts and updates GitHub. `authorize-event` prints only
`authorized=true` or `authorized=false` to `$GITHUB_OUTPUT`. Unexpected CLI
errors print a stable category to stderr and exit non-zero with suppressed
causes.

```python
def _inspect_event(args: argparse.Namespace) -> int:
    event = _load_issue_event(args.event)
    try:
        submission = parse_issue_form(event.body)
    except SubmissionError as error:
        _write_report_and_label(
            args.report, args.labels,
            render_problem_report(error.code), "needs-metadata",
        )
        return 0
    try:
        metadata = extract_metadata(submission.paper_url, SafeFetcher())
    except SourceError as error:
        metadata = unresolved_metadata(submission.paper_url, error.code)
    result = inspect_submission(submission, metadata, load_catalog(args.catalog))
    _write_result(args.result, result)
    _write_report_and_label(
        args.report, args.labels, render_report(result), state_label(result)
    )
    return 0
```

- [ ] **Step 6: Run focused and full offline tests**

Run: `python3 -m unittest tests.contributions.test_report tests.contributions.test_github tests.contributions.test_cli -v`

Run: `python3 -m unittest discover -s tests -v`

Expected: both commands PASS.

- [ ] **Step 7: Commit Issue orchestration**

```bash
git add scripts/contributions/report.py scripts/contributions/github.py scripts/contributions/cli.py tests/contributions
git commit -m "feat: report paper metadata suggestions"
```

---

### Task 5: Partial Catalog Record and Draft-PR Inputs

**Files:**
- Create: `scripts/contributions/materialize.py`
- Modify: `scripts/contributions/cli.py`
- Create: `tests/contributions/test_materialize.py`

**Interfaces:**
- Consumes: a strict version-1 `InspectionResult` JSON.
- Produces: `partial_record(result: InspectionResult) -> dict[str, object]`.
- Produces: `append_partial_record(path: Path, result: InspectionResult) -> str`, returning the record ID.
- Produces: `branch_name(issue_number: int, record_id: str) -> str`.
- Extends CLI with `materialize --result PATH --catalog PATH --issue-number INT --pr-body PATH --github-output PATH`.

- [ ] **Step 1: Write failing partial-record tests**

```python
class MaterializeTests(unittest.TestCase):
    def test_appends_only_reliable_base_metadata_and_keeps_valid_yaml(self):
        catalog = copy_catalog()
        before_coverage = COVERAGE.read_bytes()
        record_id = append_partial_record(catalog, READY_RESULT)
        records = load_catalog(catalog)
        added = records[-1]
        self.assertEqual(added["id"], record_id)
        self.assertEqual(added["title"], "Portfolio Learning")
        self.assertEqual(added["authors"], ["Ada A.", "Bo B."])
        self.assertNotIn("summary", added)
        self.assertNotIn("topics", added)
        self.assertEqual(COVERAGE.read_bytes(), before_coverage)

    def test_not_ready_and_exact_duplicate_leave_catalog_byte_identical(self):
        for result in (NOT_READY_RESULT, DUPLICATE_RESULT):
            catalog = copy_catalog()
            before = catalog.read_bytes()
            with self.assertRaises(MaterializeError):
                append_partial_record(catalog, result)
            self.assertEqual(catalog.read_bytes(), before)
```

Also assert: current catalog is reloaded and rechecked before append; an ID
collision blocks; the appended YAML parses as a list; the partial record omits
unknown extended fields rather than inventing placeholders; branch/record IDs
contain only `[a-z0-9/-]`; and the PR body lists every missing schema field plus
the exact existing validation/render commands.

- [ ] **Step 2: Run materialization tests and observe the missing module**

Run: `python3 -m unittest tests.contributions.test_materialize -v`

Expected: FAIL because `materialize.py` does not exist.

- [ ] **Step 3: Implement partial-record generation and safe append**

```python
PARTIAL_FIELD_ORDER = (
    "id", "title", "authors", "venue", "year", "track", "subvenue",
    "presentation", "official_url", "paper_url", "arxiv_id",
    "openreview_id", "doi",
)
```

Generate the stable ID as `<year>-<venue-slug>-<first-author-slug>-<title-slug>`.
Re-run `check_duplicates()` against the current file, reject a current exact
duplicate or ID collision, render one YAML list-item snippet with
`yaml.safe_dump`, validate that the combined candidate parses as a YAML list,
and replace the catalog from a same-directory temporary file. Do not call
`validate_catalog()` because a partial draft record is intentionally incomplete.

- [ ] **Step 4: Wire the materialize CLI and PR checklist**

The command must reject non-ready/exact-duplicate results before writing, append
one record, write a Markdown PR body that links the Issue and possible matches,
and append only validated `record_id=...` and `branch=...` lines to the supplied
GitHub output file. Never print arbitrary result data to shell output.

```python
def _materialize(args: argparse.Namespace) -> int:
    result = _load_result(args.result)
    record_id = append_partial_record(args.catalog, result)
    branch = branch_name(args.issue_number, record_id)
    args.pr_body.write_text(render_pr_body(args.issue_number, result), encoding="utf-8")
    _append_github_output(args.github_output, {"record_id": record_id, "branch": branch})
    return 0
```

- [ ] **Step 5: Run materialize and CLI tests**

Run: `python3 -m unittest tests.contributions.test_materialize tests.contributions.test_cli -v`

Expected: PASS, including byte-identical refusal cases.

- [ ] **Step 6: Commit partial materialization**

```bash
git add scripts/contributions/materialize.py scripts/contributions/cli.py tests/contributions
git commit -m "feat: prepare partial paper records"
```

---

### Task 6: Visitor Entry Point and Maintainer Documentation

**Files:**
- Create: `.github/ISSUE_TEMPLATE/paper-suggestion.yml`
- Modify: `scripts/render.py`
- Modify: `tests/test_render.py`
- Modify: `README.md` through `python3 scripts/render.py`
- Modify: `CONTRIBUTING.md`
- Create: `tests/contributions/test_issue_template.py`

**Interfaces:**
- Consumes: fixed Issue headings from Task 1 and title prefix `[Paper suggestion]`.
- Produces: generated README links to the Issue Form URL.
- Produces: Issue Form with one URL field and one required acknowledgement.

- [ ] **Step 1: Write failing README and Issue Form tests**

```python
def test_readme_links_to_paper_suggestion_form(self):
    rendered = render_readme(CATALOG, COVERAGE)
    self.assertIn("Suggest a Paper", rendered)
    self.assertIn("/issues/new?template=paper-suggestion.yml", rendered)


def test_issue_form_has_stable_prefix_and_parser_headings(self):
    form = yaml.safe_load(FORM_PATH.read_text(encoding="utf-8"))
    self.assertEqual(form["title"], "[Paper suggestion] ")
    self.assertEqual([item["attributes"]["label"] for item in form["body"]], [
        "Paper URL", "Scope acknowledgement",
    ])
```

Assert the URL uses an input with `validations.required: true`, the
acknowledgement uses required checkboxes, the form does not require an automatic
routing label, and README keeps the contribution link above the paper index.

- [ ] **Step 2: Run the focused tests and observe failure**

Run: `python3 -m unittest tests.test_render tests.contributions.test_issue_template -v`

Expected: FAIL because the form and generated README entry do not exist.

- [ ] **Step 3: Add the form and generated README CTA**

Use exactly the two parser headings, the fixed title prefix, and no AI/scope
questions. Add the CTA to `render_readme()` near the centered header and repeat
it under Contributing. Run `python3 scripts/render.py` to update generated files;
never patch `README.md` directly.

```yaml
name: Suggest a paper
description: Submit one paper link for maintainer review
title: "[Paper suggestion] "
body:
  - type: input
    id: paper-url
    attributes:
      label: Paper URL
      placeholder: https://openreview.net/forum?id=...
    validations:
      required: true
  - type: checkboxes
    id: scope-acknowledgement
    attributes:
      label: Scope acknowledgement
      options:
        - label: I understand maintainers decide scope and venue eligibility.
          required: true
    validations:
      required: true
```

In `render_readme()`, construct the repository-owned form URL once and insert
`[Suggest a Paper](<URL>)` in the centered header and Contributing section.

- [ ] **Step 4: Document the human-review and partial-PR flow**

Add a short `Suggesting a paper by link` section to `CONTRIBUTING.md`: automation
extracts only base facts, maintainers decide scope and acceptance, `approved`
opens a draft partial-record PR, and the existing full checklist/CI must be
completed before merge.

```markdown
## Suggesting a paper by link

Use **Suggest a Paper** to submit one HTTPS paper URL. Automation extracts only
base bibliographic facts and checks duplicates. Maintainers decide topical fit,
venue eligibility, track, and acceptance before applying `approved`. The
resulting draft PR is intentionally partial; complete the normal metadata and
verification checklist below before merging it.
```

- [ ] **Step 5: Run renderer and form tests**

Run: `python3 -m unittest tests.test_render tests.contributions.test_issue_template -v`

Run: `python3 scripts/render.py --check`

Expected: both commands PASS.

- [ ] **Step 6: Commit the visitor entry point**

```bash
git add .github/ISSUE_TEMPLATE/paper-suggestion.yml scripts/render.py tests/test_render.py tests/contributions/test_issue_template.py README.md CONTRIBUTING.md
git commit -m "feat: add paper suggestion entry point"
```

---

### Task 7: GitHub Workflows and End-to-End Contracts

**Files:**
- Create: `.github/workflows/inspect-paper-suggestion.yml`
- Create: `.github/workflows/materialize-paper-suggestion.yml`
- Create: `tests/contributions/test_workflows.py`
- Modify: `tests/contributions/test_cli.py`

**Interfaces:**
- Consumes: CLI commands from Tasks 4--5 and Issue title prefix from Task 6.
- Produces: read workflow for Issue metadata and write workflow for authorized draft PR creation.

- [ ] **Step 1: Write failing static workflow and end-to-end CLI tests**

```python
class WorkflowContractTests(unittest.TestCase):
    def test_inspect_workflow_has_read_contents_and_issue_write_only(self):
        workflow = load_workflow("inspect-paper-suggestion.yml")
        self.assertEqual(workflow["permissions"], {"contents": "read", "issues": "write"})
        self.assertEqual(set(workflow["on"]["issues"]["types"]), {"opened", "edited", "reopened"})

    def test_materialize_workflow_checks_actor_before_checkout_write_or_gh_pr(self):
        text = workflow_text("materialize-paper-suggestion.yml")
        self.assertLess(text.index("authorize-event"), text.index("materialize --result"))
        self.assertIn("github.event.label.name == 'approved'", text)
        self.assertIn("gh pr create --draft", text)
        self.assertNotIn("OPENAI", text)
        self.assertNotIn("merge", text.casefold())
```

Add an end-to-end offline test from a fixture Issue event through
`inspect-event`, strict JSON reload, report/label generation, `authorize-event`
with a fake GitHub client, and `materialize` into a temporary catalog. Assert
that no scope, acceptance, summary, or taxonomy field is introduced.

- [ ] **Step 2: Run workflow tests and observe missing files**

Run: `python3 -m unittest tests.contributions.test_workflows tests.contributions.test_cli -v`

Expected: FAIL because the workflows do not exist.

- [ ] **Step 3: Implement the read workflow**

Trigger on Issue `opened`, `edited`, and `reopened`; guard jobs with
`startsWith(github.event.issue.title, '[Paper suggestion]')`; set
`contents: read` and `issues: write`; install `requirements-dev.txt`; run
`inspect-event`; then run `sync-issue` under `if: always()` only when artifacts
exist. Use `concurrency: paper-suggestion-${{ github.event.issue.number }}` with
`cancel-in-progress: true`. Do not define any AI secret or model variable.

```yaml
name: Inspect paper suggestion
"on":
  issues:
    types: [opened, edited, reopened]
permissions:
  contents: read
  issues: write
concurrency:
  group: paper-suggestion-${{ github.event.issue.number }}
  cancel-in-progress: true
jobs:
  inspect:
    if: startsWith(github.event.issue.title, '[Paper suggestion]')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
      - run: python3 -m pip install -r requirements-dev.txt
      - id: inspect
        run: python3 -m scripts.contributions.cli inspect-event --event "${{ github.event_path }}" --catalog data/papers.yaml --result "$RUNNER_TEMP/result.json" --report "$RUNNER_TEMP/report.md" --labels "$RUNNER_TEMP/label.txt"
      - if: always() && steps.inspect.outcome == 'success'
        env:
          GH_TOKEN: ${{ github.token }}
        run: python3 -m scripts.contributions.cli sync-issue --event "${{ github.event_path }}" --report "$RUNNER_TEMP/report.md" --labels "$RUNNER_TEMP/label.txt"
```

- [ ] **Step 4: Implement the approval workflow**

Trigger on Issue `labeled`; guard on the title prefix and label `approved`.
Use `contents: write`, `issues: write`, and `pull-requests: write`. The first
mutating-capable logical gate is `authorize-event`; every later step has
`if: steps.auth.outputs.authorized == 'true'`. Re-run `inspect-event` from the
Issue body and current `main` catalog, call `materialize`, create/switch the
validated branch, commit only `data/papers.yaml`, push the Issue branch, and
create or update one draft PR with `gh pr create --draft`/`gh pr edit`. Add
`pr-created` only after a PR URL exists. Never run merge, render, or validation
as a prerequisite to opening the intentionally incomplete draft.

```yaml
name: Materialize approved paper suggestion
"on":
  issues:
    types: [labeled]
permissions:
  contents: write
  issues: write
  pull-requests: write
concurrency:
  group: paper-suggestion-${{ github.event.issue.number }}
  cancel-in-progress: false
jobs:
  materialize:
    if: startsWith(github.event.issue.title, '[Paper suggestion]') && github.event.label.name == 'approved'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
      - run: python3 -m pip install -r requirements-dev.txt
      - id: auth
        env:
          GH_TOKEN: ${{ github.token }}
        run: python3 -m scripts.contributions.cli authorize-event --event "${{ github.event_path }}" --github-output "$GITHUB_OUTPUT"
      - if: steps.auth.outputs.authorized == 'true'
        run: python3 -m scripts.contributions.cli inspect-event --event "${{ github.event_path }}" --catalog data/papers.yaml --result "$RUNNER_TEMP/result.json" --report "$RUNNER_TEMP/report.md" --labels "$RUNNER_TEMP/label.txt"
      - id: materialize
        if: steps.auth.outputs.authorized == 'true'
        run: python3 -m scripts.contributions.cli materialize --result "$RUNNER_TEMP/result.json" --catalog data/papers.yaml --issue-number "${{ github.event.issue.number }}" --pr-body "$RUNNER_TEMP/pr.md" --github-output "$GITHUB_OUTPUT"
      - if: steps.auth.outputs.authorized == 'true'
        env:
          BRANCH: ${{ steps.materialize.outputs.branch }}
        run: |
          git fetch origin "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH" || true
          git switch -C "$BRANCH" "$GITHUB_SHA"
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data/papers.yaml
          git commit -m "data: stage paper suggestion #${{ github.event.issue.number }}"
          git push --force-with-lease origin "$BRANCH"
      - id: pr
        if: steps.auth.outputs.authorized == 'true'
        env:
          GH_TOKEN: ${{ github.token }}
          BRANCH: ${{ steps.materialize.outputs.branch }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
        run: |
          existing="$(gh pr list --head "$BRANCH" --state open --json number --jq '.[0].number // empty')"
          if [ -n "$existing" ]; then
            gh pr edit "$existing" --body-file "$RUNNER_TEMP/pr.md"
            gh pr view "$existing" --json url --jq '.url'
          else
            gh pr create --draft --head "$BRANCH" --base main --title "Paper suggestion #$ISSUE_NUMBER" --body-file "$RUNNER_TEMP/pr.md"
          fi
      - if: steps.auth.outputs.authorized == 'true' && steps.pr.outcome == 'success'
        env:
          GH_TOKEN: ${{ github.token }}
        run: gh issue edit "${{ github.event.issue.number }}" --add-label pr-created
```

- [ ] **Step 5: Run focused, full, and repository gates**

Run: `python3 -m unittest tests.contributions.test_workflows tests.contributions.test_cli -v`

Run: `python3 -m unittest discover -s tests -v`

Run: `python3 scripts/validate.py`

Run: `python3 scripts/render.py --check`

Run: `git diff --check`

Expected: all commands PASS on the implementation branch before any live Issue
is materialized. The catalog remains unchanged during tests.

- [ ] **Step 6: Commit the workflows**

```bash
git add .github/workflows/inspect-paper-suggestion.yml .github/workflows/materialize-paper-suggestion.yml tests/contributions
git commit -m "feat: automate paper suggestion draft PRs"
```

---

## Final Verification and Deployment

- [ ] Review the complete branch diff against the MVP design and confirm there
  is no AI/enrichment module, automatic scope decision, acceptance inference,
  coverage mutation, direct `main` write, merge command, or CI bypass.
- [ ] Run `python3 scripts/validate.py` and record the paper/coverage counts.
- [ ] Run `python3 scripts/render.py --check` and confirm generated files are current.
- [ ] Run `python3 -m unittest discover -s tests -v` and record the test count.
- [ ] Run `python3 -m py_compile scripts/contributions/*.py`.
- [ ] Run `git diff --check` and inspect `git status --short --branch`.
- [ ] Push the feature branch, open a draft implementation PR, and confirm the
  remote repository setting permits GitHub Actions to create pull requests.
- [ ] Create labels `metadata-ready`, `needs-metadata`, `duplicate`, `approved`,
  and `pr-created` in `sjsj0101/good-quant-ai-papers` before the first live test.
- [ ] Open one real test Issue with a known non-duplicate paper link, verify the
  managed comment and label, then apply `approved` as the maintainer and confirm
  that one partial-record draft PR is created without merging it.
