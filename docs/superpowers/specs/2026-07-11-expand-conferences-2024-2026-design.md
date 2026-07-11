# 2024–2026 Cross-Conference Expansion Design

## Purpose

Expand `good-quant-ai-papers` from an ICML 2026 seed into a transparent,
multi-conference catalog covering 2024 through 2026. The catalog remains
strictly limited to computer-science research with a direct contribution to
quantitative finance or asset management.

The expansion must solve two separate problems:

1. add verified papers from every venue in scope; and
2. make coverage visible even when a venue-year has no eligible paper or its
   proceedings are not yet available.

The repository must never imply that a venue-year was searched merely because
it contains no paper records.

## Coverage Contract

The first expansion covers the Cartesian product of these years and venues:

- years: 2024, 2025, and 2026;
- venues: ICML, NeurIPS, ICLR, KDD, AAAI, IJCAI, The Web Conference (stored as
  `WWW`), WSDM, SIGIR, AISTATS, and ACM ICAIF.

This produces 33 venue-year coverage units. Main-conference, workshop,
position, and affinity-track papers are eligible when their track is stated
explicitly and an official venue source proves acceptance. Workshop coverage
includes officially affiliated workshops that expose an accepted-paper list,
program, proceedings page, or official OpenReview venue.

Conference results that do not yet exist as of the verification date are
marked pending. They are not treated as zero-result searches and no acceptance
claim is inferred from a preprint.

## Scope Rules

An included paper must contribute directly to at least one of the following:

- asset allocation, portfolio construction, or portfolio optimization;
- alpha, return, factor, volatility, regime, or tail-risk modeling used for an
  investment decision;
- market microstructure, order flow, execution, transaction costs, or market
  impact;
- derivatives pricing, exercise, hedging, or risk management;
- market simulation, synthetic market data, or investment stress scenarios;
- investment-research, trading, or portfolio agents evaluated on financial
  decisions; or
- alternative data with an explicit asset-selection, trading, or portfolio
  application.

The following remain excluded unless the work has a direct investment,
trading, portfolio, derivatives, or market-risk decision:

- banking operations and customer service;
- credit scoring and lending;
- fraud, anti-money-laundering, payments, and insurance operations;
- accounting question answering and generic financial document analysis;
- regulatory technology; and
- generic forecasting, time-series, language-model, or reinforcement-learning
  work that mentions finance only as one benchmark.

Crypto papers are included only when they address investable portfolios,
trading, execution, market structure, pricing, or market risk. Blockchain
protocol, security, and payment papers are excluded.

## Evidence Policy

Every paper record requires an official acceptance source. Sources are
preferred in this order:

1. official proceedings or conference paper page;
2. official OpenReview venue page;
3. official conference program or accepted-paper list; and
4. official workshop program, proceedings, or organizer-maintained venue page.

An arXiv page may be the public paper link but cannot be the sole evidence of
venue acceptance. Titles and ordered author lists are transcribed from the
official acceptance source. Original summaries and relevance notes are written
for the catalog and must not copy abstracts.

Each venue-year review uses broad finance and market terms, followed by manual
scope adjudication. Candidate discovery terms include portfolio, asset,
equity, stock, return, factor, trading, market, order book, execution,
derivative, option, volatility, risk, finance, financial, and crypto. Discovery
terms do not determine inclusion; the direct-decision scope rules do.

## Coverage Ledger

Add `data/coverage.yaml` as the source of truth for the 33 venue-year audits.
Each record has this shape:

```yaml
- venue: NeurIPS
  year: 2025
  status: complete
  checked_on: 2026-07-11
  tracks_checked:
    - main
    - workshop
    - position
    - affinity
  official_sources:
    - https://neurips.cc/virtual/2025/papers.html
  notes: Reviewed the official program and linked workshop venues under the repository scope.
```

Allowed statuses are:

- `complete`: the official venue material was systematically reviewed and at
  least one eligible paper was found;
- `no-eligible-papers`: the official venue material was systematically reviewed
  and no paper passed the scope rules; and
- `pending`: final venue material or a required part of the program is not yet
  available, so coverage is explicitly incomplete.

The paper count is computed from `data/papers.yaml`; it is not duplicated in
the ledger. Validation enforces that `complete` has at least one matching paper
and `no-eligible-papers` has none. `pending` may contain already verified papers
while making clear that the venue-year search is not final.

`tracks_checked` lists only track families that exist and were actually
reviewed. `official_sources` is a non-empty list of audit entry points.
`checked_on` records the most recent systematic review date. `notes` gives a
short, factual coverage boundary and must not claim exhaustiveness beyond the
listed sources.

## Paper Metadata Changes

`data/papers.yaml` remains the paper catalog source of truth. The existing
required metadata contract remains intact. Add one optional field:

- `subvenue`: the official workshop, affinity event, or named special track for
  records whose `track` is not `main`.

The existing `topics` field remains the controlled representation of a paper's
quantitative-finance fields. Venue and year remain required scalar fields.
Track values remain `main`, `workshop`, `position`, and `affinity`.

Stable IDs continue to use `<year>-<venue>-<first-author>-<short-title>` with a
normalized venue slug. Existing IDs do not change solely because the catalog
expands.

## Repository and Rendering Design

The structured-data-first architecture is retained:

```text
data/papers.yaml                    verified paper records
data/coverage.yaml                  33 venue-year audit records
schema/paper.schema.json            paper metadata contract
schema/coverage.schema.json         coverage ledger contract
papers/<year>/<venue>.md            generated venue-year paper pages
README.md                           generated catalog landing page
scripts/validate.py                 cross-file validation
scripts/render.py                   deterministic Markdown generation
```

The README is reorganized around the expanded collection:

1. mission, strict inclusion rules, and badges;
2. a 2024–2026 coverage matrix with one cell per venue-year;
3. year and venue navigation;
4. topic navigation;
5. paper tables grouped by year, venue, and track; and
6. contribution and licensing instructions.

Each coverage-matrix cell displays its paper count plus `Complete`, `No eligible
papers`, or `Pending`. A cell links to `papers/<year>/<venue>.md` when that page
has verified records. Pending and zero-result cells remain visible in the
matrix even when no paper page is generated.

Venue-year pages show the venue, year, coverage status, last review date,
official audit sources, paper count, and track-separated paper tables. Paper
tables retain titles, authors, track and presentation, focus, asset class or
frequency, and the original `why_it_matters` note. Workshop and affinity rows
also display `subvenue` when present.

Sorting is deterministic: year descending, venue in the declared venue order,
track in main/position/workshop/affinity order, then normalized title.

## Validation Rules

Validation extends across both YAML sources and their JSON Schemas:

- exactly one coverage record exists for every one of the 33 required
  venue-year units;
- no coverage record exists outside 2024–2026 or outside the declared venue
  set for this release;
- coverage statuses, dates, tracks, sources, and URLs satisfy the coverage
  schema;
- every paper maps to one coverage record with the same venue and year;
- coverage status and computed paper count are consistent;
- every paper has a valid official acceptance URL and the existing duplicate,
  enum, stable-ID, date, and URL checks still pass;
- generated README and venue-year pages exactly match the YAML inputs; and
- obsolete marker-generated pages are removed without touching hand-written
  files.

Network availability is not required for CI. Source authenticity is checked
during curation; CI verifies the committed evidence metadata and deterministic
outputs. A future scheduled link checker is outside this expansion.

## Research and Data Flow

For each venue-year unit:

1. locate official main-track and affiliated-event entry points;
2. search broadly for finance and market candidates;
3. inspect the official record and paper content for direct scope relevance;
4. record accepted candidates with complete metadata and original summaries;
5. document reviewed official sources and track coverage in the ledger;
6. mark the unit `complete`, `no-eligible-papers`, or `pending`; and
7. run validation and rendering before committing the batch.

Research is parallelized by venue family, but all records pass the same final
scope and metadata review. Conflicting title, author, track, or acceptance
evidence is resolved in favor of the official proceedings or venue record and
documented in `notes` when useful.

## Testing

Add tests before production changes for:

- missing, duplicate, extra, and malformed coverage records;
- invalid coverage status/count combinations;
- papers without a matching coverage unit;
- pending venue-years with and without already verified papers;
- venue ordering and year ordering;
- coverage-matrix counts, labels, and links;
- pages containing multiple tracks and optional `subvenue` values;
- deterministic regeneration and stale-output detection; and
- preservation of the existing ICML 2026 records and duplicate protections.

The full local test suite, catalog validator, renderer freshness check, and
GitHub Actions workflow must pass on the same commit.

## Delivery Strategy

Implementation occurs in reviewable batches:

1. coverage schema, ledger, tests, and rendering support;
2. 2024 venue research and records;
3. 2025 venue research and records;
4. available 2026 venue research and explicit pending coverage;
5. full audit, generated documentation refresh, and GitHub publication.

No batch is described as exhaustive unless its ledger record names the official
sources and all available track families reviewed. Discoveries after a
`complete` audit are normal catalog corrections and update `checked_on`.

## Non-Goals

This expansion does not create a web application, ingest PDFs, copy abstracts,
rank paper quality, calculate citation metrics, scrape conference sites in CI,
or claim that every supported venue is a general-purpose computer-science
"top conference." ACM ICAIF is included as the field-specific AI-in-finance
venue already declared by the repository.

## Acceptance Criteria

The expansion is complete when:

- all 33 venue-year units exist in `data/coverage.yaml` with evidence-backed
  statuses;
- every available 2024 and 2025 venue-year has been reviewed, and any genuinely
  unavailable 2026 result is marked pending;
- all included papers satisfy the strict quantitative-finance and
  asset-management scope and have official acceptance evidence;
- the README visibly contains all 11 conferences and all three years;
- every paper-bearing venue-year has a generated, browsable page;
- coverage counts agree with paper records and no existing ICML 2026 record is
  lost without an evidence-backed correction;
- tests, validation, render freshness, and GitHub Actions pass; and
- the public GitHub repository displays the expanded catalog on its default
  branch.
