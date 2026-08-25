# capybucks

Python library for market data: `download()` / `Ticker`, pandas
DataFrames, typed errors, pluggable providers, paid APIs later.

Keep this file under 150 lines. Longer rationale belongs in `docs/adr/`.

## Commands

```bash
uv sync --all-groups       # install runtime + dev deps
uv run pytest              # recorded/in-memory tests, no network
uv run pytest -m live      # live smoke tests (phase 1+)
uv run --group docs python docs/build.py   # HTML docs (en + pt)
uv run ruff check . --fix
uv run ruff format .
uv run mypy src/
```

Run ruff, format, and mypy before every commit. Do not disable a rule to
make a check pass — fix the issue, or ask before adding an ignore.

## Code style

- Python 3.11+, full type hints. No `Any` unless justified in a comment.
- Provider → core boundary is Pydantic (`OHLCVBar`, `Quote`, `Provenance`).
  The **public** return for time series is a pandas `DataFrame` (optional
  Polars via `as_frame="polars"`). See `docs/adr/0005-pandas-public-frames.md`.
- One provider = one module under `src/capybucks/providers/`. Do not import
  one provider from another.
- Async is the source of truth (`async_api/`). `sync/` only runs the loop.

## Testing

- Real HTTP providers need respx fixtures under `tests/fixtures/<provider>/`.
  Tests must pass with network disabled.
- `@pytest.mark.live` hits real APIs; never in the default `test.yml` job.
- New provider → fixture + unit test in the same PR. No exceptions.

## Boundaries

- Never commit API keys, tokens, or `.env` files.
- Don't add a third-party dependency without checking `pyproject.toml`.
- Don't silently stitch OHLCV from two providers in one series.
- Don't change public `download()` / `Ticker` signatures without an ADR
  or a documented major-version bump.
- User-facing guides live under `docs/` (`docs/README.md`). Update them
  when `download()` / `Ticker` behavior changes.
- Structural choices (cache backend, new asset type, fallback policy)
  need an ADR in `docs/adr/` before implementation.

## Claude Code

Claude Code auto-loads `CLAUDE.md`, which is a stub that pulls this file.
Do not duplicate rules there. Workflow: read the relevant files, plan,
implement, commit at logical checkpoints (one provider, one bugfix).

## When you're unsure

Ask before guessing on: default provider per asset/interval, cache TTL,
and anything on the public `sync/` or `async_api/` surface.
