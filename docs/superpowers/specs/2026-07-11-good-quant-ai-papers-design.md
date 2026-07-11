# good-quant-ai-papers Repository Design

## Purpose

Create a public GitHub repository at `sjsj0101/good-quant-ai-papers` that curates computer-science conference papers directly relevant to quantitative finance and asset management. The repository should be easy to browse on GitHub, machine-readable, and simple to maintain through pull requests.

## Scope

Included work must make a direct contribution to at least one of these areas:

- asset allocation and portfolio construction;
- alpha modeling, return forecasting, and factor investing;
- market state, regime, volatility, and tail-risk modeling;
- market microstructure, execution, order flow, and transaction costs;
- derivatives pricing and hedging;
- market simulation, synthetic financial data, and stress scenarios;
- investment-research or trading agents whose evaluation uses financial decisions;
- ESG or alternative-data methods with an explicit asset-selection or portfolio application.

General banking, credit scoring, fraud detection, payment systems, accounting QA, regulatory technology, and generic financial NLP are excluded unless the paper has a clear investment, trading, portfolio, or market-risk contribution. Generic machine-learning papers with only a passing finance example are also excluded.

The initial venue set is ICML, NeurIPS, ICLR, KDD, AAAI, IJCAI, WWW, WSDM, SIGIR, AISTATS, and ACM ICAIF. Main-conference, workshop, and position-paper records are permitted, but their track must be labeled explicitly. A preprint without a verified venue record is not eligible.

## Content and Copyright Policy

The repository stores metadata, original one-sentence summaries, and links. It does not store paper PDFs or copy full abstracts. Official conference, OpenReview, proceedings, arXiv, code, and project links are preferred in that order. Curated metadata and prose will use a CC BY 4.0 license.

## Chosen Architecture

Use a structured-data-first design. `data/papers.yaml` is the single source of truth. Human-readable Markdown indexes are generated deterministically from it.

This approach is preferred over a README-only list because it supports validation, deduplication, filtering, and future automation without sacrificing GitHub readability. A database-backed website or network scraper is intentionally out of scope for the first version.

## Repository Layout

```text
good-quant-ai-papers/
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── data/
│   └── papers.yaml
├── schema/
│   └── paper.schema.json
├── papers/
│   └── 2026/
│       └── icml.md
├── docs/
│   ├── metadata.md
│   └── superpowers/specs/
│       └── 2026-07-11-good-quant-ai-papers-design.md
├── scripts/
│   ├── render.py
│   └── validate.py
├── tests/
│   ├── test_render.py
│   └── test_validate.py
└── .github/workflows/
    └── validate.yml
```

`README.md` contains a short mission statement, inclusion rules, topic navigation, venue navigation, and a generated recent-papers section. Files under `papers/<year>/<venue>.md` provide full generated lists. Contributors edit only `data/papers.yaml`; generated indexes are refreshed with `scripts/render.py`.

## Paper Metadata Contract

Every record has these required fields:

```yaml
- id: 2026-icml-hwang-signature-informed-transformer
  title: Signature-Informed Transformer for Asset Allocation
  authors:
    - Yoontae Hwang
    - Stefan Zohren
  venue: ICML
  year: 2026
  track: main
  presentation: poster
  official_url: https://icml.cc/virtual/2026/poster/62694
  paper_url: https://openreview.net/forum?id=eBM5ALLJNx
  topics:
    - asset-allocation
    - portfolio-optimization
  summary: End-to-end asset allocation with path signatures and a risk-aware objective.
  why_it_matters: Aligns model training with downstream portfolio risk instead of forecast error alone.
  status: accepted
  verified_on: 2026-07-11
```

Required fields are `id`, `title`, `authors`, `venue`, `year`, `track`, `presentation`, `official_url`, `paper_url`, `topics`, `summary`, `why_it_matters`, `status`, and `verified_on`.

Optional fields are:

- `arxiv_id`, `openreview_id`, `doi`;
- `code_url`, `project_url`;
- `asset_classes`: equities, fixed-income, derivatives, FX, commodities, crypto, or multi-asset;
- `data_frequency`: tick, intraday, daily, weekly, monthly, mixed, or not-applicable;
- `tasks`, `methods`, and `datasets`;
- `notes` for short factual caveats such as non-archival workshop status.

`track` is one of `main`, `workshop`, `position`, or `affinity`. `presentation` is one of `oral`, `spotlight`, `poster`, or `not-specified`. `status` is one of `accepted` or `published`.

Stable IDs use `<year>-<venue>-<first-author>-<short-title>`. Renaming a title does not change an existing ID unless the original record was erroneous.

## Topic Taxonomy

The initial controlled topic vocabulary is:

- `asset-allocation`
- `portfolio-optimization`
- `alpha-modeling`
- `financial-forecasting`
- `factor-investing`
- `risk-management`
- `market-regimes`
- `market-microstructure`
- `execution`
- `derivatives`
- `market-simulation`
- `synthetic-data`
- `alternative-data`
- `financial-agents`
- `evaluation`

New topics require a short definition in `docs/metadata.md` so near-duplicate labels do not accumulate.

## Generation and Validation Flow

1. A contributor adds or edits records in `data/papers.yaml`.
2. `scripts/validate.py` validates required fields, enumerations, date formats, URL syntax, stable IDs, and controlled tags.
3. The validator rejects duplicates based on normalized title, official URL, paper URL, and stable ID.
4. `scripts/render.py` sorts records by year descending, then venue, track, and title, and regenerates `README.md` sections and `papers/<year>/<venue>.md`.
5. `scripts/render.py --check` fails when committed generated files are stale.
6. GitHub Actions runs validation, tests, and render checks for pushes and pull requests.

Errors must identify the record ID, field, and corrective action. Rendering must be deterministic so repeated runs produce no diff.

The first version performs no automated web scraping. Link availability checks may be added later as a non-blocking scheduled job because conference sites and OpenReview can rate-limit automated requests.

## Initial Data Seed

The first release will include the high-confidence ICML 2026 main-conference and workshop papers already verified from official ICML, OpenReview, and workshop-organizer pages. It will include portfolio optimization, forecasting, market-state learning, merger arbitrage, risk control, market simulation, order-flow generation, financial stress scenarios, and investment-agent papers. Records without an official ICML 2026 venue entry, including contemporaneous preprints such as OpenFinGym, will not be included.

Historical years and other venues will be added incrementally after the ICML 2026 seed passes validation.

## Contribution Workflow

`CONTRIBUTING.md` will require contributors to:

- demonstrate direct quantitative-finance or asset-management relevance;
- provide an official venue source;
- write original summaries rather than copying abstracts;
- edit the YAML source and run validation and rendering;
- keep workshop and position papers visibly distinct from main-track papers.

Pull requests are the normal update mechanism. Issues can propose papers or taxonomy changes.

## Testing

Tests use Python's standard library where practical to keep setup small. They cover valid and invalid records, duplicate detection, deterministic sorting, Markdown escaping, and stale generated-output detection. The GitHub workflow must pass on a clean checkout without network access.

## Success Criteria

The first release is complete when:

- `sjsj0101/good-quant-ai-papers` exists as a public repository on the `main` branch;
- the ICML 2026 seed contains only verified in-scope papers;
- every record satisfies the metadata contract;
- generated Markdown is current and browsable;
- validation and tests pass locally and in GitHub Actions;
- no PDFs, copied full abstracts, credentials, or private data are committed;
- the README clearly explains scope, exclusions, contribution rules, and licensing.
