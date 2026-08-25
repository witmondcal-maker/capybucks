# Contributing

Written before the first external contribution arrives, on purpose — the
goal is objective, predictable review criteria instead of maintainer mood.

## Before opening a PR

1. Check `ROADMAP.md` — if what you want to build isn't in the current
   phase, open an issue to discuss scope first. Unsolicited out-of-scope
   PRs (phase 3 work during phase 1, for example) will likely sit unreviewed.
2. Structural changes (new async pattern, new caching strategy, a new
   asset type) need an ADR (`docs/adr/0000-template.md`) proposed *before*
   the implementation PR, not after.
3. New provider → new fixture-backed test suite in the same PR (see
   `AGENTS.md`). No exceptions — this is the one rule with zero
   flexibility, since it's the specific failure mode this project exists
   to avoid.
4. If you change `download()` / `Ticker` / errors / providers, update the
   matching page under `docs/` (start at `docs/README.md`). User guides
   are part of the product, not an afterthought.

## Review criteria (objective, checked in this order)

1. `ruff check`, `ruff format --check`, `mypy` all pass in CI.
2. Tests pass with network disabled; new code has fixture-backed tests.
3. Public API changes (`sync/`, `async_api/`) are backward compatible, or
   the PR description explains why a breaking change is justified and
   what major-version bump it needs.
4. Any new dependency is justified in the PR description (why stdlib or
   an existing dependency wasn't enough).
5. If the public API changed, the matching guide under `docs/` was updated.

Meeting all five is sufficient for merge — review isn't a taste veto.

## Response time

Maintainers aim to give a first response (not necessarily a full review)
within 5 business days. If that slips repeatedly, say so in the issue —
it's a process bug worth fixing, not something to just live with.

## Releasing to PyPI

Trusted Publishing — no API token in GitHub. Do this **once** before the
first release, while logged into PyPI as the package owner:

1. GitHub → Settings → Environments → create `pypi`.
2. [PyPI publishing](https://pypi.org/manage/account/publishing/) → add a
   pending publisher: owner `witmondcal-maker`, repo `capybucks`, workflow
   `publish.yml`, environment `pypi`.

Each release: bump `version` in `pyproject.toml`, push, then create a
GitHub Release whose tag is `v` + that version (e.g. `v0.0.1`). The
`publish.yml` workflow runs tests, builds the sdist/wheel, and uploads.

## Code of conduct

Be direct about the code, not the person. Disagreements about design get
resolved by pointing at `docs/adr/` (or by writing a new ADR proposing a
change), not by seniority.
