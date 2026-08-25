# capybucks documentation

Market data as a one-liner: `download()` / `Ticker`, pandas DataFrames,
typed errors, and a path to paid APIs without changing your import.

```{admonition} Data is not the license
:class: warning

The **software** is MIT-licensed. The **data** is not. capybucks is not
affiliated with Yahoo, Inc. The default equity path uses unofficial Yahoo
Finance HTTP endpoints; they are usually delayed (~15 minutes) and Yahoo's
terms restrict automated collection. Do not redistribute provider data.
`df.attrs["delayed"]` exists so a delayed quote cannot masquerade as
real-time. See [Yahoo's terms](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html).
```

## Install

```bash
pip install capybucks
```

Python 3.11 or newer. Optional extras: `[calendars]`, `[stream]`, `[polars]`.
From a clone: `uv sync --all-groups` or `pip install -e .`.

## Quick start

```python
import capybucks as cb

df = cb.download("AAPL", period="1mo")
print(df.attrs["provider"], df.attrs["delayed"])

aapl = cb.Ticker("AAPL")
aapl.history(period="1mo")
aapl.financials
aapl.option_chain()
```

Several symbols (one dead name does not block the rest):

```python
cb.download(["AAPL", "MSFT", "GOOG"], period="1mo")
```

Crypto and a paid pin:

```python
cb.download("BTC-USD", period="5d")
cb.download("AAPL", provider="twelvedata")  # needs CAPYBUCKS_TWELVEDATA_KEY
```

The full surface is in {doc}`api/index`. Guides start at
{doc}`guide/index`. A Jupyter walkthrough lives in
[`examples/getting_started.ipynb`](https://github.com/witmondcal-maker/capybucks/blob/main/examples/getting_started.ipynb).

```{toctree}
:maxdepth: 1
:hidden:

guide/index
api/index
development/index
```
