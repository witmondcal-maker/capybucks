# Provedores

Um **provedor** é uma fonte de dados. O capybucks nunca concatena duas
delas numa série OHLCV só. Ou você aceita o default da classe de ativo,
ou pinna `provider="…"`.

## Quem está registrado

| Nome | Chave? | Default para | History | Demonstrações | Options | Stream |
|---|---|---|---|---|---|---|
| `yahoo` | não | ações | sim | sim | sim | não |
| `coingecko` | não | cripto | sim | não | não | não |
| `stooq` | não | — (só pin) | CSV diário | não | não | não |
| `twelvedata` | **sim** | — (só pin) | sim | sim | não | sim (`[stream]`) |
| `memory` | não | só testes | sim | sim | sim | não |

`memory` não é mercado. Testes instalam como default de equity para o CI
nunca tocar a rede.

## Defaults vs pins

```python
cb.download("AAPL")  # Yahoo
cb.download("AAPL", provider="yahoo")
cb.download("AAPL", provider="stooq")
cb.download("AAPL", provider="twelvedata")
cb.download("BTC-USD")  # CoinGecko
cb.download("EUR/USD", provider="twelvedata")
```

FX **não** tem default. `EUR/USD` sem pin levanta `NoProviderError`. É
de propósito: não vamos fingir que a Yahoo entende todo par FX.

`provider="blob"` desconhecido levanta `ProviderNotFound`.

## Yahoo

Endpoints unofficial de chart e quoteSummary. Zero config. Em geral
**atrasado** (~15 minutos). `df.attrs["delayed"]` é `True`.

A Yahoo é o default de ações porque o Stooq, de muitos IPs de datacenter,
devolve uma página de challenge JavaScript em vez de CSV. Ainda assim
enviamos o Stooq como pin para quando o CSV responder.

Histórico intradaily é curto. Demonstrações e options existem no
`Ticker`. Termos de uso restringem coleta automatizada — veja o
disclaimer do README.

## Stooq

CSV diário em `stooq.com`. Pin com `provider="stooq"`. Se o corpo for
HTML (challenge), você leva `ProviderError` falando em bot-check — não um
frame lixo parseado.

Não misture uma série Stooq com uma Yahoo na mão e chame de um backtest.
Ajustes e calendários diferem.

## CoinGecko

OHLC público de moedas. Tickers como `BTC-USD`, `ETH-USD` ou `BTC` viram
ids internos. Rate limit do API grátis é apertado; o capybucks espaça
chamadas (~1s). `CAPYBUCKS_NO_RATELIMIT=1` desliga isso (só testes).

## Twelve Data

REST oficial (e WebSocket opcional). Exige `CAPYBUCKS_TWELVEDATA_KEY` ou
`[keys].twelvedata` em `~/.capybucks.toml`. Credencial ausente levanta
`MissingAPIKey` **antes** do HTTP.

Twelve Data nunca é o default silencioso. Você opta com `provider=`.
History REST continua `delayed=True` na proveniência até termos um feed
que possamos chamar de tempo real com honestidade. Quotes do stream
marcam `delayed=False` no objeto `Quote`.

Limites do plano (créditos, símbolos) são da Twelve Data, não do
capybucks. Um `429` vira `RateLimitError`. 401/chave inválida no JSON
vira `MissingAPIKey`.

Polygon **não** está implementado. Fica parado até a Twelve Data não
bastar (SIP dos EUA, options em volume).

## Uma série, uma fonte

Retry e backoff valem só **naquele** provedor. `SymbolNotFound` não é
retriado (o nome não vai aparecer porque pedimos duas vezes). Não há
`fallback=True` no `download()` hoje. Se entrar depois, será retry
completo noutro provedor com proveniência apontando quem de fato
respondeu — nunca costura de velas.

## Rate limits

GETs de saída são serializados por provedor (Yahoo ~0,15s, Stooq ~0,4s,
CoinGecko ~1s, Twelve Data ~0,8s). HTTP 429 → `RateLimitError`. HTTP 401
→ `MissingAPIKey`. HTTP 403 é rejeição / erro de ritmo (a Yahoo usa como
parede de bot).
