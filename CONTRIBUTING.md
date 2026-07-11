# Contributing

Thank you for helping keep Good Quant AI Papers accurate and useful. Pull
requests may add a paper, correct existing metadata, or improve the repository's
curation documentation. Issues are welcome for candidate papers and proposed
taxonomy changes.

## Inclusion decision test

A paper is eligible only when **every** answer below is yes:

1. **Verified venue:** Is the work accepted or published at one of the
   controlled computer-science venues listed in `docs/metadata.md`, with an
   official source that proves the venue, year, and track? A preprint without a
   verified venue record fails this test.
2. **Direct decision relevance:** Can you name the investment, trading,
   portfolio-construction, derivatives, or market-risk decision that the paper
   changes or evaluates?
3. **Substantive contribution:** Does the method, evidence, or evaluation make
   a direct contribution to that decision rather than merely using finance as
   an example or motivation?
4. **Controlled topic:** Does at least one existing topic in
   `docs/metadata.md` describe that substantive contribution?
5. **Curatable record:** Can every required field be supported while the
   `summary` and `why_it_matters` remain original editorial prose?

When the decision relevance cannot be stated concretely, do not add the paper.
Open an issue if the evidence is genuinely ambiguous; acceptance at a selective
venue alone is not sufficient.

Examples that normally qualify include asset allocation and portfolio
construction; alpha, return, and factor modeling; volatility, regime, and tail
risk; market microstructure and execution; derivatives pricing and hedging;
market simulation and financial stress scenarios; and decision-evaluated
investment or trading agents.

## Explicit exclusions

Do not add:

- unverified preprints, including papers with only an arXiv or author-page
  claim of venue acceptance;
- generic machine-learning work with only a passing finance dataset or example;
- general banking or consumer-finance applications without a direct investment
  or market-risk contribution;
- credit scoring, loan approval, fraud detection, payment systems, accounting
  question answering, or regulatory technology without that direct
  contribution;
- generic financial NLP, sentiment, retrieval, or language-model benchmarks
  that do not affect or evaluate an asset-selection, portfolio, trading,
  derivatives, or market-risk decision;
- papers whose claimed relevance depends only on possible future use in
  investing rather than a contribution demonstrated by the paper; or
- duplicate records, even when a paper has multiple public landing pages.

## Primary-source proof

Every addition needs an `official_url` that visibly establishes venue status.
Prefer an official conference page, official OpenReview venue record, or
official proceedings page. For a workshop paper, an official workshop program
or organizer page is acceptable when no conference-level record exists. The
source must support the venue, year, and `main`, `workshop`, `position`, or
`affinity` label used in the YAML.

An arXiv page, paper PDF, author website, code repository, search result, news
item, or social post is not acceptance proof. These sources may supplement a
record, but they cannot replace the official source. Set `verified_on` to the
date you personally checked the primary source. See `docs/metadata.md` for link
priority and field-level rules.

## Track and presentation labels

Track labels describe the acceptance route and must not be upgraded based on
paper quality or visibility:

- Use `track: main` only for a main-conference acceptance.
- Use `track: workshop` for an affiliated workshop acceptance. Name the
  workshop and state known archival status in `notes`.
- Use `track: position` for an official position-paper track, even when the
  venue hosts it alongside the main program.
- Use `track: affinity` for an official affinity track or event.

`presentation` is a separate field. Record `oral`, `spotlight`, or `poster` only
when the official source says so; otherwise use `not-specified`. The renderer
keeps main, workshop, position, and affinity records in separate sections.

## Copyright and repository boundaries

Commit metadata, original editorial summaries, and links only.

- Do not commit paper PDFs, supplementary files, screenshots of papers, or
  local copies of third-party content.
- Do not copy full abstracts or sentences from abstracts into `summary` or
  `why_it_matters`. Read the paper and write concise original prose.
- Do not paste code, figures, tables, dataset contents, or project-page text
  from linked sources.
- Link to third-party material instead. Linked papers, code, datasets, and
  project pages remain under their owners' terms.

## Source-of-truth workflow

For paper additions and metadata corrections, edit
`data/papers.yaml`—the only paper-data source of truth. Do not hand-edit the
generated `README.md` or files under `papers/`. `scripts/render.py` regenerates
those files deterministically; include its generated changes in the same pull
request.

From the repository root, install the pinned development dependency:

```bash
python3 -m pip install -r requirements-dev.txt
```

Then validate, render, check freshness, and run the complete test suite:

```bash
python3 scripts/validate.py
python3 scripts/render.py
python3 scripts/render.py --check
python3 -m unittest discover -s tests -v
git diff --check
```

`scripts/validate.py` checks required fields, controlled values, stable-ID
shape, URLs, dates, and duplicates. `scripts/render.py` updates generated
Markdown. `scripts/render.py --check` must report that generated files are
current; it does not update them. All commands run offline and must succeed
before a pull request is ready for review.

## Adding a paper

1. Apply the inclusion decision test and collect the official venue proof.
2. Search `data/papers.yaml` for the normalized title and all known URLs to
   avoid duplicates.
3. Add one record using the field contract and stable-ID convention in
   `docs/metadata.md`. Keep author order and title spelling aligned with the
   official record.
4. Write an original `summary` of what the paper does and an original
   `why_it_matters` tied to a concrete quantitative-investment decision.
5. Label the track and presentation precisely. Include the workshop name and
   known archival status in `notes` for workshop records.
6. Run the install and verification commands above, inspect the rendered diff,
   and commit both `data/papers.yaml` and the regenerated Markdown.

Do not introduce a new topic just to fit one paper. Propose taxonomy changes in
an issue first; maintainers must update `scripts/catalog.py`,
`schema/paper.schema.json`, and `docs/metadata.md` together.

## Correcting an existing record

1. Identify the record by its stable `id` and describe what is wrong.
2. Link the official or author-controlled primary source that supports the
   correction. For removal of an invalid record, show which inclusion-test
   condition no longer holds.
3. Change the record in `data/papers.yaml` and update `verified_on` when you
   recheck venue or publication status.
4. Keep the existing `id` for title spelling, capitalization, URL, or metadata
   corrections. Change an ID only when the ID itself was erroneous, and call
   out that exceptional change in the pull request.
5. Rerun validation, rendering, the freshness check, tests, and
   `git diff --check`. Never patch the generated Markdown instead of its YAML
   source.

If the correction changes a workshop, position, affinity, or main-track label,
the proof must explicitly establish the new track. If a paper no longer has
verified venue status or no longer passes the scope test, remove the record
rather than inventing a new uncontrolled status.

## Pull request checklist

- [ ] Every added paper passes all five inclusion-test questions.
- [ ] `official_url` is a primary source proving venue, year, and track.
- [ ] The record is not an unverified preprint or a duplicate by ID, normalized
      title, official URL, or paper URL.
- [ ] Main, workshop, position, and affinity labels match the official source;
      workshop notes name the workshop and known archival status.
- [ ] `summary` and `why_it_matters` are original, concise, and directly tied to
      quantitative finance or asset management.
- [ ] No PDF, copied abstract, third-party text, credential, or private data is
      included.
- [ ] Paper data was changed only in `data/papers.yaml`; `README.md` and
      `papers/` changes came only from `scripts/render.py`.
- [ ] `python3 scripts/validate.py` passes.
- [ ] `python3 scripts/render.py --check` passes after rendering.
- [ ] `python3 -m unittest discover -s tests -v` passes.
- [ ] `git diff --check` passes and the rendered diff was reviewed.
- [ ] Corrections cite their evidence, preserve stable IDs unless erroneous,
      and refresh `verified_on` when source verification changed.
