# Metadata reference

The repository has two canonical metadata files. `data/papers.yaml` is the
source of truth for included paper records. `data/coverage.yaml` is the source
of truth for the venue-year audit ledger rendered in the coverage matrix. The
validators in `scripts/catalog.py` and `scripts/coverage.py`, together with the
public contracts in `schema/paper.schema.json` and
`schema/coverage.schema.json`, define which fields and controlled values are
accepted.

The exploratory finance-journal watchlist in
`data/finance_journal_ai_watchlist.yaml` is intentionally non-canonical for now.
It records EDITH-local-corpus metadata for JF/JFE/RFS AI + finance papers, but
it does not use the conference-only schema below. It is checked by
`scripts/finance_journal_watchlist.py` as part of `python3 scripts/validate.py`.
Treat its `year` field as the EDITH local corpus year and check
`metadata_quality` before relying on publication-year precision.

The file contains a YAML list of mappings, one mapping per paper. Field names
are case-sensitive, unlisted fields are rejected, and every list must be
non-empty, contain no duplicates, and use non-empty strings.

## Required fields

Every record must contain all of the following fields.

| Field | Type | Meaning and rules |
| --- | --- | --- |
| `id` | string | Permanent lowercase ASCII slug in the form `<year>-<venue>-<first-author>-<short-title>`. See [Stable IDs](#stable-ids). |
| `title` | string | Full paper title from the accepted-paper or publication record. Must be non-empty. |
| `authors` | list of strings | Non-empty, duplicate-free author list in the order shown by the official venue record. Preserve the source's spelling and capitalization. |
| `venue` | controlled string | Conference family. Use one value from [Venues](#venues). |
| `year` | integer | Four-digit venue year represented as an integer, not a quoted string. It must agree with the year encoded in `id`. |
| `track` | controlled string | Acceptance track. Use one value from [Tracks](#tracks). Track and presentation type are separate facts. |
| `presentation` | controlled string | Presentation format. Use one value from [Presentations](#presentations). |
| `official_url` | HTTP(S) URL | Official page that proves the paper's venue and track status. See [Source priority](#source-priority). |
| `paper_url` | HTTP(S) URL | Best public paper landing page or full-text link. It may equal `official_url` when there is no separate paper page. |
| `topics` | list of controlled strings | One or more distinct values from the [Topic taxonomy](#topic-taxonomy). Tag material contributions, not passing mentions. |
| `summary` | string | Original, concise editorial description of what the paper does. Do not copy the abstract. |
| `why_it_matters` | string | Original explanation of the paper's direct consequence for an investment, trading, portfolio, derivatives, or market-risk decision. |
| `status` | controlled string | Publication state: `accepted` or `published`. See [Statuses](#statuses). |
| `verified_on` | string | Last date on which the venue proof and metadata were checked, as a valid ISO date in `YYYY-MM-DD` form. |

Required URLs must be absolute `http://` or `https://` URLs. Records are
rejected when an `id`, normalized title, `official_url`, or `paper_url`
duplicates an earlier record.

## Optional fields

Omit an optional field when the fact is unknown. Do not use empty strings or
empty lists as placeholders.

| Field | Type | Meaning and rules |
| --- | --- | --- |
| `arxiv_id` | string | arXiv identifier only, such as `2602.23784`; do not put the URL here. |
| `openreview_id` | string | OpenReview forum or note identifier only, such as `anK6dppdfa`. |
| `doi` | string | DOI identifier, normally without a resolver URL. |
| `code_url` | HTTP(S) URL | Public source-code repository supplied by the authors or venue. |
| `project_url` | HTTP(S) URL | Author or institutional project page for the paper. |
| `subvenue` | string | Official workshop, affinity event, position-paper program, or other side-program container. Use this for the container name; keep `notes` for caveats. |
| `asset_classes` | list of controlled strings | One or more materially studied asset classes from [Asset classes](#asset-classes). |
| `data_frequency` | controlled string | Primary empirical sampling frequency from [Data frequencies](#data-frequencies). Use `mixed` for multiple material frequencies and `not-applicable` when the paper has no meaningful sampling frequency. |
| `tasks` | list of strings | Concise task names used in the paper, such as `portfolio construction` or `return forecasting`. Use source terminology where practical. |
| `methods` | list of strings | Concise method or model-family names. |
| `datasets` | list of strings | Named datasets, markets, or benchmark collections used in the evaluation. |
| `notes` | string | Short factual caveat, especially a workshop name or archival-status qualification. It is not a second summary field. |

The optional identifier and notes fields must be non-empty strings when
present. Optional lists must be non-empty and duplicate-free. Optional URL
fields must be absolute HTTP(S) URLs.

## Controlled values

### Venues

Use the official capitalization shown here:

- `ICML`
- `NeurIPS`
- `ICLR`
- `KDD`
- `AAAI`
- `IJCAI`
- `WWW`
- `WSDM`
- `SIGIR`
- `AISTATS`
- `ACM ICAIF`

### Tracks

- `main`: accepted to the venue's main conference research track.
- `workshop`: accepted to an officially affiliated workshop, not to the main
  conference. Name the workshop and state known archival status in `notes`.
- `position`: accepted under an official position-paper designation. Do not
  relabel it as a main research paper even when it appears on the same venue
  site.
- `affinity`: accepted to an official affinity track or affiliated affinity
  event. It remains distinct from both the main conference and workshops.

The track records the acceptance route, not perceived paper quality. Main,
workshop, position, and affinity records remain visibly separated in generated
indexes.

### Presentations

- `oral`: designated as an oral presentation by the venue or track.
- `spotlight`: designated as a spotlight or equivalent highlighted short oral.
- `poster`: designated as a poster presentation.
- `not-specified`: the official source does not state a presentation format.

Do not infer a presentation type from the track.

### Statuses

- `accepted`: official acceptance is verified, but a final proceedings record
  is not yet available or has not been verified.
- `published`: an official proceedings or publication record has been verified.

### Asset classes

- `equities`: common stocks, equity indexes, equity factors, or equity-linked
  investment decisions.
- `fixed-income`: sovereign or corporate bonds, rates, credit instruments, or
  fixed-income portfolios.
- `derivatives`: options, futures, swaps, or other derivative contracts when
  they are the empirical asset class.
- `FX`: currencies and foreign-exchange markets. Capitalization is exact.
- `commodities`: physical commodities or commodity futures and indexes.
- `crypto`: cryptoassets and digital-asset markets.
- `multi-asset`: a material combination of more than one asset class or a
  cross-asset allocation problem.

### Data frequencies

- `tick`: individual quote, order, or trade events.
- `intraday`: observations aggregated within a trading day, such as bars or
  snapshots.
- `daily`: one observation or decision interval per trading day.
- `weekly`: weekly observations or decisions.
- `monthly`: monthly observations or decisions.
- `mixed`: multiple materially used sampling frequencies.
- `not-applicable`: no meaningful market-data frequency applies, for example a
  methodological position paper without an empirical time series.

## Topic taxonomy

Choose every topic that describes a substantive contribution, while avoiding
tags that appear only as motivation or a minor example.

- `asset-allocation`: deciding how much capital to place across assets or asset
  classes through time using return, risk, or liability information.
- `portfolio-optimization`: computing portfolio weights under objectives and
  constraints such as risk, sparsity, turnover, costs, or position limits.
- `alpha-modeling`: constructing predictive signals, scores, or rankings aimed
  at generating risk-adjusted investment returns.
- `financial-forecasting`: forecasting returns, volatility, order flow, macro
  inputs, or other future financial quantities used in an investment or risk
  decision.
- `factor-investing`: discovering, estimating, ranking, timing, or allocating
  to systematic return factors and factor exposures.
- `risk-management`: measuring, forecasting, stress-testing, or controlling
  portfolio and market risk, including downside and tail risk.
- `market-regimes`: identifying or using changes in volatility, correlation,
  liquidity, or other latent market states for portfolio or risk decisions.
- `market-microstructure`: modeling order books, trades, liquidity, price
  formation, or short-horizon market interactions.
- `execution`: choosing order placement, scheduling, rebalancing, or trading
  policies to manage market impact, transaction costs, and implementation risk.
- `derivatives`: pricing, hedging, exercising, or managing options and other
  derivatives.
- `market-simulation`: reproducing market dynamics or participant interactions
  to study trading, policy, robustness, or stress outcomes.
- `synthetic-data`: generating or augmenting financial time series, order flow,
  returns, or scenarios for investment-model development or risk analysis.
- `alternative-data`: turning nontraditional information such as text, ESG,
  imagery, or web data into an explicit asset-selection or portfolio input.
- `financial-agents`: autonomous or language-model agents that perform
  investment research, trading, allocation, or market-risk tasks and are
  evaluated on those decisions.
- `evaluation`: benchmarks, protocols, or bias controls that test the validity
  of investment, trading, portfolio, or market-risk models; generic finance QA
  alone is not sufficient.

Adding a topic requires a coordinated maintainer change to `scripts/catalog.py`,
`schema/paper.schema.json`, and this page. Propose the definition first so
near-duplicate labels do not accumulate.

## Stable IDs

Construct a new ID as `<year>-<venue>-<first-author>-<short-title>`:

1. Start with the integer venue year.
2. Convert the controlled venue name to lowercase alphanumeric tokens joined
   by hyphens (`ACM ICAIF` becomes `acm-icaif`).
3. Add a lowercase ASCII slug for the first listed author's family name. Keep
   enough tokens to avoid ambiguity for compound names.
4. Add a short, distinctive lowercase ASCII title slug. Remove punctuation and
   join tokens with single hyphens.

For example, `2026-icml-sood-tradefm` follows the convention. The validator
enforces the lowercase hyphenated shape and the `<year>-<venue>-` prefix; review
also checks that the author and title components are sensible and unique.

An ID is permanent after merge. A later title spelling or capitalization
correction does not change it. Change an existing ID only when the ID itself
was erroneous, and treat that as an explicit correction because links may
already depend on it.

## Source priority

Prefer links in this order: official conference page, official OpenReview venue
record, official proceedings page, arXiv, author code repository, then author
project page. The first three may serve as `official_url` only when the page
itself proves the venue, year, and track. An official workshop organizer or
program page may prove a workshop record when no conference-level or OpenReview
venue record exists.

An arXiv page, author website, code repository, search result, social post, or
paper PDF does not by itself prove acceptance. Use such a page only for the
appropriate paper, code, or project link after venue status has been proven by
an official source. Update `verified_on` whenever that proof is rechecked.

## Coverage ledger

`data/coverage.yaml` contains one row for every controlled venue-year in the
2024–2026 scope. It is a conservative audit ledger, not a claim that every
pending venue-year has been exhausted.

| Field | Type | Meaning and rules |
| --- | --- | --- |
| `venue` | controlled string | Same venue values as paper records. |
| `year` | integer | One of the controlled coverage years. |
| `status` | controlled string | `complete`, `no-eligible-papers`, `pending`, or `unavailable`. |
| `checked_on` | string | ISO date when the coverage evidence was last checked. |
| `eligible_paper_count` | integer | Count of cataloged papers for this venue-year; it must equal matching records in `data/papers.yaml`. |
| `tracks_checked` | list of controlled strings | Tracks with paper rows actually screened. It may be empty only for `pending` or `unavailable` rows. |
| `tracks_pending` | list of mappings | Unresolved track-level surfaces. Each item has `track`, `state`, and `note`. |
| `official_sources` | list of HTTP(S) URLs | Official or organizer sources used for the audit. |
| `notes` | string | Human-readable audit notes, including exact blockers for pending rows. |

Coverage statuses mean:

- `complete`: the recorded official paper-bearing sources were screened for the
  venue-year and no material paper-list blocker remains.
- `no-eligible-papers`: the screened official sources produced zero papers that
  pass the strict quant-finance scope test.
- `pending`: some official sources, side programs, accepted-paper rows, or paper
  rosters remain unresolved. This is not a zero-eligible finding.
- `unavailable`: the relevant source is not currently published or cannot be
  reached as an accepted-paper source; it must have zero cataloged papers.

`tracks_pending[*].state` uses:

- `source_mapped`: the source family was identified but not fully screened.
- `partial`: some rows for the same track were screened, but a paper-level
  blocker remains.
- `blocked`: an access or source-availability boundary prevented screening.
- `unpublished`: the accepted-paper source is not yet published.

Only update `data/coverage.yaml` after a systematic venue-year audit, a source
availability correction, or a paper change that alters the venue-year count or
track state. A casual single-paper candidate does not by itself make a pending
venue-year complete.

## Complete YAML example

This example is a currently valid catalog record. It shows useful optional
identifier and workshop-note fields; optional fields not supported by evidence
are simply omitted.

```yaml
- id: 2026-icml-sood-tradefm
  title: "TradeFM: A Generative Foundation Model for Trade-flow and Market Microstructure"
  authors:
    - Srijan Sood
    - Maxime Kawawa-Beaudan
    - Daniel Borrajo
    - Manuela Veloso
  venue: ICML
  year: 2026
  track: workshop
  presentation: poster
  official_url: https://openreview.net/forum?id=anK6dppdfa
  paper_url: https://openreview.net/forum?id=anK6dppdfa
  arxiv_id: "2602.23784"
  openreview_id: anK6dppdfa
  subvenue: 2nd ICML Workshop on Foundation Models for Structured Data (FMSD 2026)
  topics:
    - market-microstructure
    - market-simulation
    - synthetic-data
  summary: Trains a generative trade-event model with scale-invariant features designed to transfer across equity markets.
  why_it_matters: Supports cross-asset order-flow simulation and synthetic microstructure data without asset-specific tokenization.
  notes: "Non-archival workshop paper. Authors follow the accepted FMSD record; the later arXiv version has a revised author list."
  status: accepted
  verified_on: "2026-07-11"
```

Validate edits with `python3 scripts/validate.py`. Regenerate indexes with
`python3 scripts/render.py`, then confirm freshness with
`python3 scripts/render.py --check`.
