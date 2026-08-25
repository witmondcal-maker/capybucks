# download()

`capybucks.download` busca OHLCV e devolve um DataFrame pandas. É a
entrada em lote. Para demonstrações, options e notícias, use
[`Ticker`](ticker.md).

```python
import capybucks as cb
from datetime import datetime, timezone

cb.download("AAPL")
cb.download("AAPL", period="1y", interval="1d")
cb.download("AAPL", start=datetime(2024, 1, 1, tzinfo=timezone.utc))
cb.download(["AAPL", "MSFT"], group_by="ticker")
cb.download("BTC-USD")  # cripto → CoinGecko por padrão
cb.download("AAPL", provider="twelvedata", cache=False)
```

## Parâmetros

| Nome | Padrão | Significado |
|---|---|---|
| `tickers` | (obrigatório) | Um símbolo, string com vírgula/espaço, ou uma sequência |
| `period` | `"1mo"` | Lookback se `start` for omitido |
| `interval` | `"1d"` | Tamanho da barra |
| `start` / `end` | `None` | Janela inclusiva; `end` default é agora |
| `auto_adjust` | `True` | Prefere close ajustado a split/dividendo quando a fonte tem |
| `provider` | `None` | Fixa uma fonte; senão o default da classe de ativo |
| `group_by` | `"ticker"` | Layout das colunas em multi-ticker |
| `cache` | `True` | Lê/grava o cache parquet nesta chamada |

Símbolos são uppercased. `"aapl, msft"` e `["AAPL", "MSFT"]` são o mesmo
pedido.

## Períodos

Se você passa `start`, `period` é ignorado. Senão `period` é subtraído
de `end` (ou de agora):

`1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `max`, `ytd`.

Período desconhecido levanta `ValueError` com a lista de nomes — não um
frame vazio silencioso.

`max` é um lookback longo (50 anos de calendário do nosso lado). O
**provedor** pode devolver menos. A Yahoo em especial trunca histórico
intraday.

## Intervalos

Valores comuns: `1m`, `5m`, `15m`, `30m`, `1h`, `1d`, `1wk`, `1mo`.

Nem todo provedor implementa todo intervalo. A Yahoo cobre a lista acima
(mais aliases como `1w` → `1wk`). Twelve Data mapeia `1d` → `1day`,
`1wk` → `1week`. O OHLC público do CoinGecko é grosso (quase diário). Se
a fonte recusar o intervalo você leva `ProviderError`, não um resample
chutado.

Ranges intradaily são curtos em endpoints unofficial. Peça
`period="5d"` em `1m`, não `period="max"`.

## Um ticker vs vários

Um símbolo → índice de colunas **plano** (`Open`, `High`, …).

Vários símbolos → **MultiIndex**. `group_by="ticker"` põe o símbolo em
cima (`AAPL, Open`). `group_by="column"` põe o campo em cima
(`Open, AAPL`), útil para `df["Close"]`.

```python
wide = cb.download(["AAPL", "MSFT"], group_by="column")
wide["Close"].tail()
```

## Falha parcial em lote

Se você pede três tickers e um está delistado, os outros dois ainda
voltam. O nome que falhou fica no frame combinado:

```python
frame = cb.download(["AAPL", "NOTAREALTICKER", "MSFT"])
frame.attrs["errors"]  # {"NOTAREALTICKER": "..."}
```

Se **todos** falham, `download` levanta `MultiDownloadError`. O mapa
`exc.errors` tem cada `CapybucksError`. É o oposto de retriar um ticker
morto até o kernel morrer.

## Inferência de tipo de ativo

O registry escolhe um provedor **padrão** pelo formato do símbolo quando
você não passa `provider=`:

| Padrão | Ativo | Default |
|---|---|---|
| `BTC-USD`, `ETH`, nomes com `-`, `…USDT` | cripto | CoinGecko |
| `EUR/USD` (uma barra) | FX | nenhum — você precisa pin, em geral `twelvedata` |
| todo o resto | ação | Yahoo |

Inferência é conveniência, não cadastro de ativos. `BRK-B` parece cripto
por causa do hífen; use `provider="yahoo"` se a Yahoo é o que você quer.
`PETR4.SA` é ação (sem barra, sem hífen).

## Flag de cache

`cache=True` (padrão) guarda barras em `~/.cache/capybucks` (ou
`CAPYBUCKS_CACHE_DIR`), chaveadas por **provedor + símbolo + intervalo**.
A próxima chamada só busca **buracos**. `cache=False` sempre vai à rede
e não grava.

Veja [Cache e proveniência](cache-and-provenance.md) para o porquê de
dois provedores nunca compartilharem arquivo.

## Valor de retorno

Sempre pandas hoje. Nomes de coluna são o conjunto OHLCV acima.
Proveniência em `df.attrs`. Série vazia com sucesso não acontece: zero
barras vira `SymbolNotFound`.
