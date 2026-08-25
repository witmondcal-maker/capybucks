# Ticker

`Ticker` is a handle for one symbol. History goes through the same path as
`download()`. The extra methods (financials, options, news, actions) call
the **same provider** you pinned — or the default for that asset class.

```python
import capybucks as cb

aapl = cb.Ticker("AAPL")  # Yahoo by default
aapl = cb.Ticker("AAPL", provider="twelvedata")  # paid path
```

The blocking `Ticker` wraps `capybucks.async_api.AsyncTicker`. Properties
that hit the network (`financials`, `news`, …) fetch **every time you
access them**. There is no in-process TTL yet. If you need the table
twice, bind it to a name.

## History

```python
aapl.history(period="6mo", interval="1d")
aapl.history(start=..., end=..., auto_adjust=True, cache=True)
```

Same parameters as `download()` minus `group_by` (one symbol). Same
columns and `attrs`.

## Financial statements

Yahoo (default) and Twelve Data both implement these. Other providers
raise `NotImplementedError` until they grow the method.

| Property | Statement | Periods |
|---|---|---|
| `financials` | income | annual |
| `quarterly_financials` | income | quarterly |
| `balance_sheet` | balance | annual |
| `quarterly_balance_sheet` | balance | quarterly |
| `cashflow` | cash flow | annual |
| `quarterly_cashflow` | cash flow | quarterly |

Layout: **line items as the index**, **period-end dates as columns**
(most recent first when the source sends them that way). Item names are
whatever the provider uses (`totalRevenue` on Yahoo, `revenue` on Twelve
Data). We do not rename them into a fake standard — that would pretend
two taxonomies are one.

```python
inc = aapl.financials
inc.loc["totalRevenue"]  # Yahoo field names
```

Empty statements from the source become `SymbolNotFound`, not a blank
sheet of zeros.

## Options

Yahoo implements a chain. Twelve Data history/financials do **not**
currently expose options in this library.

```python
aapl.options  # tuple of expiration dates, ISO `YYYY-MM-DD`
chain = aapl.option_chain()  # nearest expiry if you omit the date
chain = aapl.option_chain("2024-01-19")
chain.calls
chain.puts
```

`option_chain` returns a named tuple of two DataFrames (`calls`, `puts`)
with columns such as `contractSymbol`, `strike`, `lastPrice`, `bid`,
`ask`, `volume`, `openInterest`, `impliedVolatility`, `inTheMoney`,
`expiration`.

## Dividends, splits, actions

```python
aapl.dividends  # Series, non-zero dividend amounts
aapl.splits  # Series, split ratio (e.g. 4.0 for a 4-for-1)
aapl.actions  # DataFrame: Dividends, Stock Splits
```

Yahoo reads these from chart events (`div|split`). A name with no events
returns an empty Series/frame, not an error.

## News

```python
aapl.news  # DataFrame: title, publisher, link, published_at
```

Yahoo uses the search endpoint (a handful of headlines). Other providers
may raise `NotImplementedError`. This is not a full news product.

## Quote snapshot

```python
q = aapl.quote()
q.symbol, q.price, q.timestamp, q.currency, q.delayed
```

`Quote` is a Pydantic model, not a DataFrame. Yahoo's quote is the last
daily bar; it is **delayed**. Twelve Data's REST quote is also marked
delayed in this library. Live prints belong on
[AsyncTicker.stream()](async-and-streaming.md).

## What is not here

There is no `info` blob, no recommendations dump, no `fast_info`. Those
APIs tend to be an untyped dict that drifts every quarter. If a field
matters, it should become a typed method with a fixture test.
