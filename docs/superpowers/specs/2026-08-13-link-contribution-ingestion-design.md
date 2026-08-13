# Link-Only Paper Contribution MVP Design

**Date:** 2026-08-13

## Goal

Let a signed-in GitHub visitor suggest one paper by pasting its link. The
automation extracts reliable bibliographic metadata and checks for duplicates;
a maintainer decides whether the paper belongs in this quantitative-finance and
asset-management catalog. An approved suggestion produces a draft data-change
pull request, never a direct change to `main`.

## Scope

The MVP automates clerical work only:

- collect one HTTPS paper link through a GitHub Issue Form;
- extract title, authors, venue, year, identifiers, and paper URLs when the
  submitted source provides them;
- compare the candidate with `data/papers.yaml` for exact and likely
  duplicates;
- show the extracted facts and duplicate result in one managed Issue comment;
- wait for a maintainer to review topical fit and target-conference eligibility;
  and
- after maintainer approval, open a draft pull request containing a partial
  catalog record with the reliable base metadata.

The MVP does not generate summaries or classifications, decide topical scope,
infer acceptance status, modify coverage records, merge pull requests, or write
directly to `main`.

## Visitor Flow

1. The generated README shows a prominent **Suggest a Paper** link.
2. The link opens `.github/ISSUE_TEMPLATE/paper-suggestion.yml`.
3. The form supplies a stable `[Paper suggestion]` Issue-title prefix for
   workflow routing. It does not depend on a pre-existing routing label.
4. The visitor supplies one HTTPS paper URL and checks an acknowledgement that
   the repository is limited to target top conferences and quantitative finance
   or asset management.
5. The metadata workflow validates the form, extracts available base metadata,
   checks the catalog for duplicates, and updates one bot-managed Issue comment.
6. A maintainer reviews the source, conference eligibility, and topical fit.
7. If accepted, the maintainer applies the `approved` label.
8. The approval workflow re-extracts the candidate from the original Issue and
   opens a draft pull request.
9. The maintainer completes the repository's extended metadata fields in the
   pull request. Existing validation and rendering checks must pass before the
   pull request is merged.

The visitor never edits YAML or supplies controlled taxonomy values.

## Reliable Base Metadata

A candidate is `metadata-ready` only when extraction yields all of:

- a non-empty title;
- at least one author;
- a controlled conference name;
- an integer year from 2024 through 2026; and
- at least one canonical paper URL.

When available, the result also records DOI, arXiv ID, OpenReview ID, official
venue URL, track, subvenue, and presentation. These optional fields do not make
a candidate ready by themselves and do not replace maintainer review.

The automation does not create placeholder authors, venue names, years, or
links. A missing required base field produces `needs-metadata`; the Issue
comment tells the maintainer which facts could not be extracted.

## Source Support

The MVP has small source adapters for:

- OpenReview forum pages and their public API metadata;
- arXiv abstract pages and public API metadata;
- DOI links resolved through Crossref metadata; and
- a limited allowlist of official pages for the repository's controlled
  conferences.

Each adapter returns bibliographic facts, not an acceptance judgment. An arXiv
or Crossref record may name a venue, but the maintainer still decides whether
the submission is a qualifying conference paper.

Unrecognized hosts are not fetched. Their submitted URL can be shown in the
Issue report, but they produce `needs-metadata` unless the required base facts
are available through a recognized identifier and adapter.

## Basic URL Safety

The implementation keeps only the security controls needed for public-link
metadata extraction:

- accept `https://` only;
- fetch only recognized public hosts;
- reject loopback, private, link-local, and non-HTTPS redirect targets;
- use bounded connection/read timeouts, redirect counts, and response sizes;
- never interpolate Issue text into shell commands, branch names, workflow
  expressions, or repository paths; and
- do not persist HTML, PDFs, copied abstracts, credentials, or response bodies.

These controls are local to the fetch layer. The MVP does not add a general
transaction framework, crawler, proxy service, website, or database.

## Duplicate Checks

The metadata workflow compares the candidate with the current catalog using:

1. exact DOI, OpenReview ID, or arXiv ID;
2. normalized official URL or paper URL;
3. normalized title equality; and
4. a conservative normalized-title similarity check for a possible duplicate.

The result is one of:

- `clear`: no catalog match was found;
- `possible`: a title match needs maintainer review; or
- `duplicate`: an exact identifier, URL, or normalized title already exists.

The workflow reports matching catalog IDs. A `duplicate` cannot produce a
draft PR. A `possible` match remains a human decision: approval is allowed, but
the draft PR body must highlight the possible match.

## Human Review Boundary

Automation does not decide whether a paper:

- makes a direct contribution to quantitative finance or asset management;
- belongs to one of the target top conferences;
- was formally accepted in the stated track; or
- deserves particular topics, tasks, methods, asset classes, frequencies,
  summaries, or investment-relevance prose.

Applying `approved` is the maintainer's explicit decision on those questions.
Before creating repository changes, the approval workflow verifies through the
GitHub API that the label actor has `write`, `maintain`, or `admin` permission.
It then re-reads the Issue, re-extracts metadata, and reruns duplicate checks;
the earlier bot comment is not trusted as input.

Approval proceeds only when the candidate is `metadata-ready` and not an exact
duplicate. Otherwise, no branch or pull request is created and the Issue report
states the remaining problem.

## Draft Pull Request

The approval workflow creates or updates one branch named from the Issue number
and a sanitized paper slug. It appends one syntactically valid YAML record to
`data/papers.yaml` containing only extracted base metadata and any reliable
optional identifiers.

Fields required by the repository schema but not available from bibliographic
sources are omitted. Consequently, the initial draft pull request may fail the
existing catalog validator. This is intentional: the pull request body contains
a checklist for the maintainer to add controlled topics, tasks, methods,
original `summary`, original `why_it_matters`, status, and any other required
catalog fields. The maintainer then runs the existing renderer so generated
README, paper, and topic pages match the completed record.

The existing CI remains the merge gate:

```bash
python3 scripts/validate.py
python3 scripts/render.py --check
python3 -m unittest discover -s tests -v
git diff --check
```

The workflow opens a draft PR even when the new partial record makes validation
fail. It never disables, bypasses, or weakens those checks, and it never merges
the pull request.

## Labels and Managed Comment

The MVP uses five state labels:

- `metadata-ready`: reliable base metadata is complete and no exact duplicate
  exists;
- `needs-metadata`: extraction failed or one or more base fields are missing;
- `duplicate`: an exact catalog match exists;
- `approved`: maintainer-owned approval trigger; and
- `pr-created`: a draft pull request exists for the Issue.

`metadata-ready`, `needs-metadata`, and `duplicate` are mutually exclusive and
automation-owned. `approved` is maintainer-owned. The workflows maintain one
Issue comment identified by a stable HTML marker so edits update the same
report instead of adding comments.

The report contains the submitted and canonical URLs, extracted base metadata,
identifiers, duplicate result and matching IDs, missing base fields, and the
next maintainer action. It does not contain AI advice, copied abstracts, or an
automated scope or acceptance decision.

## Workflow Permissions and Idempotency

The metadata workflow runs for opened, edited, and reopened Issues whose title
has the stable `[Paper suggestion]` prefix, with `contents: read` and
`issues: write`. It cannot change repository contents or create pull requests.

The approval workflow runs when `approved` is added. It uses `contents: write`,
`issues: write`, and `pull-requests: write` only after checking the triggering
actor's repository permission. It derives all branch and file content through
Python commands with validated structured inputs.

Both workflows use an Issue-specific concurrency key. Repeated metadata runs
update the managed comment. Repeated approval events update or reuse the same
Issue branch and draft PR rather than creating duplicates.

## Error Handling

- Invalid form content produces `needs-metadata` with a short stable reason.
- Unsupported links and upstream timeouts do not create a PR.
- Exact duplicates produce `duplicate` and list matching IDs.
- A possible title match is visible to the maintainer but does not silently
  block an explicit approval.
- Permission failure, incomplete metadata, or an exact duplicate leaves the
  repository unchanged.
- A failed branch, commit, or PR command leaves the Issue without `pr-created`
  and reports a retryable automation failure without exposing secrets or raw
  response bodies.

## Testing Strategy

Tests use checked-in, minimal source fixtures and mocked network transports; no
test depends on live conference sites.

- Issue Form tests cover one-link parsing, HTTPS enforcement, duplicate
  headings, and acknowledgement validation.
- Source tests cover successful base extraction, missing fields, redirect and
  private-address rejection, size/time bounds, and unsupported hosts.
- Duplicate tests cover identifiers, canonical URLs, normalized titles,
  possible-title matches, and catalog rechecks at approval time.
- Report tests cover one managed marker, inert untrusted text, missing-field
  display, and the five-label state model.
- Materialization tests cover partial YAML record generation, duplicate refusal,
  sanitized branch/slug output, and leaving `data/coverage.yaml` untouched.
- Static workflow tests cover triggers, permissions, actor authorization,
  concurrency, re-extraction, and the absence of AI configuration.
- Existing catalog, rendering, unit, and diff checks remain unchanged.

## Acceptance Criteria

The MVP is complete when:

1. README opens the paper-suggestion Issue Form.
2. A visitor can submit exactly one HTTPS paper link without editing YAML.
3. Recognized sources produce title, authors, venue, year, and paper URL when
   those facts are available.
4. Missing base facts are listed and prevent PR creation.
5. Exact duplicates are listed and prevent PR creation; possible title matches
   are highlighted for the maintainer.
6. No automated component decides topical scope or acceptance status.
7. Only an authorized maintainer applying `approved` can trigger a draft PR.
8. The draft PR contains the reliable partial record and a checklist for the
   missing extended metadata.
9. Existing CI remains required before merge, even when the initial draft PR is
   intentionally incomplete.
10. No workflow merges a PR or writes directly to `main`.

## Explicitly Out of Scope

- AI-generated summaries, classifications, or scope advice;
- automatic conference-acceptance inference or proof scoring;
- automated topical eligibility decisions;
- automatic completion of controlled taxonomy fields;
- bulk submissions, journal papers, taxonomy changes, or coverage-ledger work;
- a website, database, queueing service, or external ingestion API;
- direct commits to `main`, automatic merging, or bypassing existing CI; and
- a generalized crawler, security platform, or multi-file transaction system.
