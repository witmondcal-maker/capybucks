# Ticker

`Ticker` é um handle para um símbolo. History segue o mesmo caminho de
`download()`. Os métodos extras (demonstrações, options, notícias,
eventos) chamam o **mesmo provedor** que você fixou — ou o default da
classe de ativo.

```python
import capybucks as cb

aapl = cb.Ticker("AAPL")  # Yahoo por padrão
aapl = cb.Ticker("AAPL", provider="twelvedata")  # caminho pago
```

O `Ticker` síncrono envolve `capybucks.async_api.AsyncTicker`.
Propriedades que batem na rede (`financials`, `news`, …) buscam **toda
vez que você acessa**. Ainda não há TTL in-process. Se precisar da tabela
duas vezes, ligue a um nome.

## History

```python
aapl.history(period="6mo", interval="1d")
aapl.history(start=..., end=..., auto_adjust=True, cache=True)
```

Mesmos parâmetros de `download()` menos `group_by` (um símbolo). Mesmas
colunas e `attrs`.

## Demonstrações financeiras

Yahoo (padrão) e Twelve Data implementam. Outros provedores levantam
`NotImplementedError` até ganharem o método.

| Propriedade | Demonstração | Períodos |
|---|---|---|
| `financials` | resultado | anual |
| `quarterly_financials` | resultado | trimestral |
| `balance_sheet` | balanço | anual |
| `quarterly_balance_sheet` | balanço | trimestral |
| `cashflow` | fluxo de caixa | anual |
| `quarterly_cashflow` | fluxo de caixa | trimestral |

Layout: **linhas no índice**, **datas de encerramento nas colunas**
(mais recente primeiro quando a fonte manda assim). Os nomes dos itens
são os da fonte (`totalRevenue` na Yahoo, `revenue` na Twelve Data). Não
renomeamos para um padrão falso — isso fingiria que duas taxonomias são
uma.

```python
inc = aapl.financials
inc.loc["totalRevenue"]  # nomes de campo da Yahoo
```

Demonstração vazia na fonte vira `SymbolNotFound`, não uma planilha de
zeros.

## Options

A Yahoo implementa a chain. History/financials da Twelve Data **não**
expõem options nesta biblioteca por enquanto.

```python
aapl.options  # tupla de vencimentos, ISO `YYYY-MM-DD`
chain = aapl.option_chain()  # vencimento mais próximo se omitir a data
chain = aapl.option_chain("2024-01-19")
chain.calls
chain.puts
```

`option_chain` devolve uma named tuple de dois DataFrames (`calls`,
`puts`) com colunas como `contractSymbol`, `strike`, `lastPrice`, `bid`,
`ask`, `volume`, `openInterest`, `impliedVolatility`, `inTheMoney`,
`expiration`.

## Dividendos, splits, actions

```python
aapl.dividends  # Series, valores de dividendo não-zero
aapl.splits  # Series, razão do split (ex.: 4.0 num 4-for-1)
aapl.actions  # DataFrame: Dividends, Stock Splits
```

A Yahoo lê isso dos eventos do chart (`div|split`). Nome sem eventos
devolve Series/frame vazio, não erro.

## Notícias

```python
aapl.news  # DataFrame: title, publisher, link, published_at
```

A Yahoo usa o endpoint de busca (um punhado de headlines). Outros
provedores podem levantar `NotImplementedError`. Isto não é um produto
de notícias.

## Snapshot de cotação

```python
q = aapl.quote()
q.symbol, q.price, q.timestamp, q.currency, q.delayed
```

`Quote` é um modelo Pydantic, não um DataFrame. A cotação da Yahoo é a
última barra diária; é **atrasada**. A quote REST da Twelve Data também
está marcada delayed nesta lib. Prints ao vivo ficam em
[AsyncTicker.stream()](async-and-streaming.md).

## O que não está aqui

Não há blob `info`, dump de recommendations, nem `fast_info`. Essas APIs
tendem a ser um dict sem tipo que muda todo trimestre. Se um campo
importa, vira método tipado com teste de fixture.
