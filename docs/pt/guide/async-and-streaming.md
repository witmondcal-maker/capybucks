# Async e streaming

## Por que duas APIs

`async_api/` é a fonte da verdade (HTTP, cache, retry).
`capybucks.download` e `capybucks.Ticker` são wrappers síncronos finos.
Eles chamam `run_sync`, que usa `asyncio.run` quando não há loop, ou um
**thread de trabalho** quando o Jupyter já tem um loop. Por isso
`download()` não levanta `RuntimeError: This event loop is already running`.

Não duplique lógica de negócio em `sync/`. Se você escreve um provedor,
implemente só os métodos async.

## Await de downloads

```python
from capybucks.async_api import download, AsyncTicker

df = await download("AAPL", period="5d")
hist = await AsyncTicker("AAPL").history(period="5d")
inc = await AsyncTicker("AAPL").financials()
```

No `AsyncTicker`, financials/news/options são **métodos async**, não
propriedades (`await ticker.financials()`). O `Ticker` síncrono expõe os
mesmos nomes como propriedades por conveniência de notebook.

`await download(["AAPL", "MSFT"])` busca em concorrência com
`asyncio.gather`. Um ticker morto não cancela os outros.

## Stream de cotações

Só a Twelve Data declara `supports_stream = True`. Yahoo, Stooq e
CoinGecko levantam `StreamingNotSupportedError`.

Instale o extra, sete a chave, pinne o provedor:

```bash
pip install "capybucks[stream]"
```

```python
from capybucks.async_api import AsyncTicker

ticker = AsyncTicker("AAPL", provider="twelvedata")
async for quote in ticker.stream():
    print(quote.symbol, quote.price, quote.timestamp, quote.delayed)
    break
```

`Quote.delayed` é `False` nos prints do websocket (são ao vivo tanto
quanto este cliente pode afirmar). History REST do mesmo vendor continua
`delayed=True` no DataFrame. Não misture os dois numa série sem perceber.

Heartbeats e eventos que não são preço são ignorados. Sem `[stream]`
(`websockets`) levanta `StreamingNotSupportedError`. Sem chave,
`MissingAPIKey` antes de conectar.

O `Ticker` síncrono **não** tem `stream()`. Streaming é só async.

## Configurar cache no código async

```python
from pathlib import Path
from capybucks.async_api import configure_cache

configure_cache(Path("./.cache/capybucks"))
```

O mesmo helper dos testes. Veja [Cache e proveniência](cache-and-provenance.md).
