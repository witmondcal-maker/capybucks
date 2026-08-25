# Primeiros passos

O capybucks é uma biblioteca Python de dados de mercado. Você chama
`download()` ou `Ticker`, recebe um DataFrame pandas, e consegue dizer
**de onde vieram os números**. Essa última parte é o ponto.

Helpers comuns na internet tendem a esconder a fonte, engolir um ticker
inexistente como frame vazio ou coluna de `NaN`, e te deixar preso a um
endpoint unofficial quando você precisa de um feed licenciado. O
capybucks mantém o one-liner e torna esses modos de falha explícitos.

## Instalação

```bash
pip install capybucks
```

Extras opcionais, só quando precisar:

| Extra | O que libera |
|---|---|
| `[ta]` | Marcador — os indicadores já rodam em pandas |
| `[calendars]` | Calendários de pregão (`BVMF` para `.SA`) |
| `[stream]` | Cotações WebSocket da Twelve Data |
| `[polars]` | Reservado; frames públicos são pandas hoje |

```bash
pip install "capybucks[calendars,stream]"
```

A partir de um clone: `uv sync --all-groups` (ou `--all-extras`) / `pip install -e .`.
Python 3.11 ou mais novo.

## Primeira chamada

```python
import capybucks as cb

df = cb.download("AAPL", period="1mo")
df.tail()
```

O que você deve ver:

- Um `DatetimeIndex` chamado `Date`, com fuso (em geral o da bolsa).
- Colunas `Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`.
- Metadados no frame, não como colunas extras:

```python
df.attrs["provider"]  # ex.: "yahoo"
df.attrs["delayed"]  # True em feeds unofficial / atrasados
df.attrs["adjustment"]  # "split_and_dividend" ou "none"
df.attrs["asof"]  # quando este processo buscou a série
df.attrs["currency"]  # ex.: "USD"
```

`delayed=True` é contrato. Uma cotação atrasada não pode parecer tempo
real. Se você plotar isso ao lado de um stream pago, leia essa flag.

## Quem respondeu?

Ações como `AAPL` vão para a **Yahoo** sem chave. Esse endpoint é
unofficial e em geral **atrasado** (~15 minutos). Cripto como `BTC-USD`
vai para o **CoinGecko**. Você pode fixar outra fonte com `provider=`:

```python
cb.download("AAPL", provider="twelvedata")  # precisa de chave; ver Configuração
```

**Não há fallback silencioso.** Se a Yahoo cair, o capybucks não cola
velas do Stooq na mesma série. Misturar ajuste e calendário num frame só
é bug de backtest com cara de sucesso. Fixe um provedor, ou espere e
tente de novo o mesmo.

## Símbolo ausente levanta exceção

```python
from capybucks.exceptions import SymbolNotFound

try:
    cb.download("THISISNOTATICKER")
except SymbolNotFound as err:
    print(err.symbol, err.provider)
```

Você não ganha um DataFrame vazio. Capture `CapybucksError` (ou uma
subclasse) em vez de testar `df.empty`.

Ações à vista da B3 na Yahoo precisam do sufixo `.SA`. `PETR4` levanta
`SymbolNotFound` com `err.hint == "PETR4.SA"`. Veja
[Indicadores e calendários](indicators-and-calendars.md) para fuso e
pregão.

## Jupyter

`download()` é seguro num notebook. Se já houver um event loop, o
capybucks busca num thread de trabalho em vez de levantar
`RuntimeError`. A API async está em `capybucks.async_api` — veja
[Async e streaming](async-and-streaming.md).

O notebook de passeio está em
[examples/getting_started.ipynb](../../../examples/getting_started.ipynb).
Essas células usam a rede.

## Dado não é licença

O **software** é MIT. Os **dados** pertencem ao provedor. Não redistribua
séries da Yahoo (nem de outro vendor) como se fossem o seu feed. Os
termos da Yahoo restringem coleta automatizada; trate o caminho padrão
como conveniência de pesquisa, não como direito comercial.

Próximo: [download()](download.md) para períodos, lotes e intervalos.
