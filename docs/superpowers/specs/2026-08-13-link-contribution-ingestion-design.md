# Link-Only Paper Contribution Design

## Objective

Give a GitHub visitor a low-friction way to suggest one paper by submitting one
link. The repository will parse and verify the candidate, explain the result in
the issue, and create a validated draft pull request only after a maintainer
approves the candidate.

The feature preserves the repository's existing standard: a paper is not
verified unless an official venue source proves the venue, year, and track.
Artificial intelligence may advise on scope and editorial metadata, but it may
not establish acceptance or bypass deterministic validation.

## First-Version Scope

The first version will:

- expose a prominent **Suggest a paper** link in the generated README;
- collect a required paper URL and an optional relevance note through a GitHub
  Issue Form;
- accept official conference pages, OpenReview pages, proceedings pages, DOI
  links, and arXiv links as starting points;
- extract available metadata, resolve official venue evidence, detect likely
  duplicates, and evaluate the repository's conference-only quant-finance
  scope;
- post one idempotently updated verification report to the issue;
- use an optional language-model call to suggest controlled metadata and draft
  original `summary` and `why_it_matters` prose;
- require a maintainer-applied `approved` label before any repository write;
  and
- reverify the candidate, edit the canonical YAML, render generated Markdown,
  run all checks, and open a draft pull request.

The first version will not accept taxonomy changes, venue-scope changes,
coverage-ledger audits, bulk submissions, anonymous submissions, or journal
papers. It will not merge pull requests automatically.

## Visitor Experience

The generated README will show **Suggest a paper** near the top and repeat the
entry point in the Contributing section. Both links open
`.github/ISSUE_TEMPLATE/paper-suggestion.yml`.

The form contains:

1. `Paper URL` (required): one HTTPS URL.
2. `Why is it relevant?` (optional): a short explanation of the investment,
   trading, portfolio, derivatives, or market-risk decision affected.
3. A required acknowledgement that the repository covers only verified
   2024--2026 top-conference work in quantitative finance and asset management.

The contributor does not edit YAML, choose controlled metadata, run code, or
write a summary. The form automatically applies the `paper-suggestion` label.
Deployment creates every automation-owned label before enabling the form, so a
missing label cannot silently prevent routing.

## Architecture

The system has two workflows with different permissions.

### 1. Candidate verification

An issue-opened or issue-edited workflow runs with `contents: read` and
`issues: write`. A Python command reads the Issue Form body, validates the URL,
resolves it through source-specific adapters, compares the candidate with the
catalog, optionally enriches it with AI, and returns a structured result.

The workflow maintains one bot comment identified by an HTML marker rather
than appending a new comment on every edit. It reconciles machine-owned status
labels while leaving maintainer labels untouched. A per-issue concurrency key
cancels stale verification runs after rapid edits.

This workflow never modifies repository contents and never creates a branch or
pull request.

### 2. Approved candidate materialization

An issue-label workflow reacts to `approved`. Before using write permissions,
it checks through the GitHub API that the triggering actor has `write`,
`maintain`, or `admin` permission. It then parses and verifies the issue again
from the original URL; the prior bot comment is informative and is not trusted
as input.

Materialization proceeds only when all required paper fields are valid, the
candidate has official venue proof, no duplicate exists, and the candidate is
within scope. The workflow adds one record to `data/papers.yaml`, runs the
renderer and the complete offline verification suite, and creates a branch
named `contrib/issue-<number>-<paper-slug>` with a draft pull request that links
the issue. It does not change `data/coverage.yaml`, because a single visitor
suggestion is not a systematic venue-year audit.

If any gate fails, the workflow makes no repository commit and replaces the
`approved` label with the appropriate blocking status.

## Component Boundaries

The implementation will keep the existing catalog and renderer as the source
of truth and add focused modules:

- `scripts/contributions/issue_form.py` parses the stable Issue Form headings
  into a URL and optional note.
- `scripts/contributions/sources.py` normalizes URLs and dispatches to
  source-specific metadata adapters.
- `scripts/contributions/verify.py` applies evidence, date, venue, scope, and
  duplicate rules and emits a versioned JSON result.
- `scripts/contributions/enrich.py` performs optional AI enrichment and
  validates its response against controlled values.
- `scripts/contributions/report.py` renders the human-readable issue report and
  derives machine-owned labels.
- `scripts/contributions/materialize.py` turns a fully verified result into one
  schema-valid catalog record without modifying coverage data.

Network parsing, verification policy, AI advice, report formatting, and
catalog mutation remain separate so each can be tested without GitHub or live
network access.

## Verification Semantics

The result uses separate facts rather than one ambiguous confidence score:

- `source_resolved`: the submitted URL was recognized and safely read.
- `venue_verified`: an official source proves the controlled venue, year, and
  track.
- `duplicate_status`: `clear`, `possible`, or `duplicate` based on stable ID,
  normalized title, DOI, OpenReview ID, official URL, and paper URL.
- `scope_assessment`: `in-scope`, `uncertain`, or `out-of-scope`, with reasons.
- `record_complete`: every field required by `schema/paper.schema.json` is
  present and valid.
- `ready_for_approval`: all deterministic gates pass and the scope assessment
  is `in-scope`.

Only deterministic evidence can set `venue_verified`. An arXiv page, author
page, repository, or model statement cannot do so. If a DOI or arXiv record
links to a recognized official proceedings or venue page, that official page
is stored as `official_url`; otherwise the issue is labeled
`needs-official-source`.

The existing controlled venues and the 2024--2026 year range are imported from
repository code rather than duplicated in workflow YAML.

## AI Enrichment

AI enrichment runs only after deterministic extraction. It receives a bounded
plain-text packet containing extracted bibliographic metadata, abstract text
when available, the contributor's relevance note, the controlled taxonomy,
and the inclusion/exclusion rules. It does not receive raw HTML, arbitrary
linked content, repository secrets, or permission to fetch URLs.

The model returns schema-constrained JSON containing:

- a scope recommendation with concrete decision relevance and reasons;
- suggested `topics`, `asset_classes`, `data_frequency`, `tasks`, `methods`,
  and `datasets`;
- an original one-sentence `summary`; and
- an original `why_it_matters` tied to a quant-investment decision.

Every controlled value and required string is validated locally. Invalid AI
output is discarded rather than repaired silently. The verification report
labels all AI-derived fields as suggestions. The maintainer remains
responsible for their correctness when applying `approved`.

`OPENAI_API_KEY` is optional. Without it, deterministic parsing and venue
verification still run, the report states that enrichment was unavailable,
and the candidate cannot reach `record_complete` or automatic materialization.
The report directs the maintainer to the repository's existing manual pull-
request workflow for that candidate. This is a service degradation, not a
weaker verification standard.

The model name is supplied through an `OPENAI_MODEL` repository variable. It is
not hard-coded into parsing or verification logic, and changing it cannot
change any deterministic evidence rule.

## Labels and State

The automation owns these labels:

- `paper-suggestion`: identifies the submission type;
- `verifying`: a run is in progress;
- `verified-candidate`: deterministic proof and a complete candidate exist;
- `needs-official-source`: venue, year, or track lacks primary-source proof;
- `possible-duplicate`: a match requires maintainer review;
- `duplicate`: the catalog already contains the paper;
- `likely-out-of-scope`: the paper fails or probably fails the direct-decision
  relevance test;
- `needs-metadata`: required fields remain unresolved; and
- `automation-error`: a transient or internal failure prevented a conclusion.

`approved` is maintainer-owned. Blocking labels and `verified-candidate` are
mutually exclusive. Editing the issue reruns verification and may change
machine-owned labels; it never restores `approved` automatically.

## Error Handling and Safety

- Only HTTPS URLs are accepted.
- Network adapters fetch recognized public hosts only, use bounded timeouts,
  response-size limits, redirect limits, and reject private, loopback,
  link-local, and non-HTTP redirect targets.
- Unknown hosts may be recorded as `paper_url` evidence but are not fetched and
  cannot prove venue status.
- Parser, upstream timeout, rate-limit, and AI failures appear as separate
  report sections so maintainers know whether to retry or supply evidence.
- Logs redact authorization headers, tokens, submitted query parameters, and
  model credentials.
- User text is treated as data, escaped in Markdown, and never interpolated
  into shell commands, branch names, workflow expressions, or model system
  instructions.
- The read workflow has no content-write permission. The write workflow starts
  only from a maintainer-authorized label event and reverifies all untrusted
  input.
- A branch conflict, duplicate branch, or already-linked open pull request is
  handled idempotently: the existing draft pull request is updated rather than
  creating another one.

## Verification Report

The managed issue comment contains:

1. an overall state and the next required action;
2. submitted and canonical URLs;
3. extracted title, authors, venue, year, track, and identifiers;
4. the exact official evidence URL and deterministic checks;
5. duplicate matches and their catalog IDs;
6. the scope recommendation and explicit quant decision relevance;
7. proposed controlled metadata and editorial prose, visibly marked as AI
   suggestions; and
8. a maintainer instruction explaining when `approved` is safe to apply.

The report never calls a paper verified when only the scope recommendation or
an unverified preprint is available.

## Testing Strategy

Tests use checked-in HTML/JSON fixtures and mocked HTTP responses; the normal
test suite never requires live conference sites or an AI key.

- Unit tests cover Issue Form parsing, URL normalization, each source adapter,
  redirect and host safety, duplicate matching, controlled-value validation,
  AI-response rejection, report rendering, label reconciliation, and catalog
  materialization.
- Integration tests run representative official-link, arXiv-with-official-
  evidence, missing-evidence, duplicate, out-of-scope, unavailable-AI, and
  malicious-input cases through the complete verifier.
- Workflow tests validate event filters and least-privilege permissions as
  static YAML contracts.
- Existing catalog validation, rendering freshness, unit tests, and
  `git diff --check` remain mandatory before a draft pull request is created.

## Acceptance Criteria

The feature is ready when:

1. a signed-in visitor can open the form from README and submit one link;
2. one managed issue comment reports extracted facts, official proof,
   duplicates, scope advice, and the next action;
3. a preprint without official proof cannot receive `verified-candidate`;
4. AI output cannot set venue verification or bypass catalog validation;
5. missing AI configuration leaves deterministic verification operational;
6. an unprivileged issue author cannot trigger repository writes;
7. for a complete candidate, a maintainer-applied `approved` label reverifies
   the source and creates one valid draft pull request;
8. a failed approval attempt creates no commit or pull request and explains
   the blocking condition; and
9. all generated files and existing repository checks remain current.
