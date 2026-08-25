# Configuration

capybucks runs with **zero config** for Yahoo equities and CoinGecko
crypto. Paid providers need a key. Nothing in this project should ever
commit a secret.

## API keys

Resolution order for provider name `twelvedata`:

1. Environment variable `CAPYBUCKS_TWELVEDATA_KEY` (non-empty).
2. `~/.capybucks.toml`, table `[keys]`, key `twelvedata`.

Env wins if both are set. Tests can redirect the toml path with
`set_config_path` so your home file is never read.

```toml
# ~/.capybucks.toml
[keys]
twelvedata = "paste-the-key"
```

```bash
# POSIX
export CAPYBUCKS_TWELVEDATA_KEY="paste-the-key"

# PowerShell
$env:CAPYBUCKS_TWELVEDATA_KEY = "paste-the-key"
```

A `.env` file in the repo is **not** loaded by the library. It is listed
in `.gitignore` so local secrets stay local. To run tests that need the
key:

```bash
uv run --env-file .env pytest -m live
```

Copy [`.env.example`](../../../.env.example) to `.env` and fill it. Never
commit `.env`.

The live Twelve Data test looks at the **environment variable**, not the
toml file. Set the env (or `--env-file`) for `pytest -m live`.

## Other environment variables

| Variable | Effect |
|---|---|
| `CAPYBUCKS_TWELVEDATA_KEY` | Twelve Data API key |
| `CAPYBUCKS_CACHE_DIR` | Parquet cache root (default `~/.cache/capybucks`) |
| `CAPYBUCKS_NO_RATELIMIT=1` | Skip per-provider spacing (used in unit tests) |

`CAPYBUCKS_POLYGON_KEY` appears in `.env.example` as a placeholder.
Polygon is not implemented.

## Jupyter / process lifetime

Keys are read at **request** time, not at import time. Export the env,
then import capybucks, or set the env before the cell that calls
`download(..., provider="twelvedata")`.
