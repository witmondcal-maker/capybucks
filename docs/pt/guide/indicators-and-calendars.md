# Indicadores e calendários

## Indicadores (`capybucks.ta`)

Funções **vetorizadas em pandas** sobre colunas OHLCV. Elas não baixam
dados. Você passa `Close` (e `High`/`Low`/`Volume` quando precisar).

O extra `[ta]` é um marcador; pandas já é dependência dura.
`pip install capybucks[ta]` só documenta a intenção.

```python
import capybucks as cb
from capybucks.ta import rsi, sma, ema, macd, bollinger, atr, vwap, enrich

df = cb.download("AAPL", period="6mo")
rsi(df["Close"]).tail()
enrich(df, window=20).tail()
```

| Função | Entradas | Notas |
|---|---|---|
| `sma` / `ema` | close, `window=20` | EMA usa `span=window`, `adjust=False` |
| `rsi` | close, `window=14` | Suavização de Wilder (`alpha=1/window`) |
| `macd` | close, `fast=12`, `slow=26`, `signal=9` | DataFrame `macd`, `signal`, `histogram` |
| `bollinger` | close, `window=20`, `num_std=2` | `mid`, `upper`, `lower` |
| `atr` | high, low, close, `window=14` | True range, média Wilder |
| `vwap` | high, low, close, volume | Preço típico × volume acumulado |
| `enrich` | frame OHLCV completo | Adiciona SMA, EMA, RSI, MACD, BB, ATR, VWAP |

Fórmulas de livro, não um sistema de trading. Janelas são parâmetros, não
conselho.

## B3

A Yahoo lista ações à vista brasileiras como `{ticker}.SA` (Petrobras ON
→ `PETR4.SA`). Um `PETR4` nu levanta `SymbolNotFound` com
`hint="PETR4.SA"`. Não reescrevemos o símbolo por você.

Fusos do gráfico vêm da fonte. O meta B3 da Yahoo é
`America/Sao_Paulo`, então o DatetimeIndex fica nessa zona quando o
payload diz isso. Se o fuso faltar e o símbolo terminar em `.SA`, o
parser da Yahoo cai para `America/Sao_Paulo`.

A moeda nessa série em geral é `BRL`.

```python
import capybucks as cb

df = cb.download("PETR4.SA", period="1mo")
df.index.tz  # America/Sao_Paulo
df.attrs["currency"]
```

## Calendários de pregão (`capybucks[calendars]`)

Instale `exchange-calendars` pelo extra:

```bash
pip install "capybucks[calendars]"
```

```python
from datetime import datetime, timezone
from capybucks.calendars import calendar_for_symbol, is_session

calendar_for_symbol("PETR4.SA")  # "BVMF" (B3)
calendar_for_symbol("AAPL")  # "XNYS"
calendar_for_symbol("VOD.L")  # "XLON"

is_session(datetime(2024, 1, 8, 17, tzinfo=timezone.utc), symbol="AAPL")
```

`is_session` converte timestamps com tz para a zona do calendário antes
de perguntar “isso é um dia de pregão?”. Datetimes naive são tratados
como datas de calendário.

Sem o extra, `get_calendar` / `is_session` levantam `ImportError` com a
dica de install.
