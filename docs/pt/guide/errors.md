# Erros

O capybucks levanta **exceções tipadas** em vez de devolver um DataFrame
vazio ou uma coluna de `NaN`. Capture-as a partir de `capybucks` (estão
reexportadas no pacote).

```python
import capybucks as cb
from capybucks.exceptions import SymbolNotFound, MissingAPIKey

try:
    cb.download("NOPE")
except SymbolNotFound as err:
    print(err.symbol, err.provider, err.hint)
```

Todas as falhas públicas herdam `CapybucksError`.

## Hierarquia

```
CapybucksError
├── ProviderError          rede, schema, HTTP 4xx/5xx depois do mapeamento
│   ├── RateLimitError     HTTP 429 (e alguns 403)
│   ├── MissingAPIKey      chave ausente/inválida num provedor pago
│   └── SymbolNotFound     a fonte não tem série (incl. delistado)
├── ProviderNotFound       provider="…" não está registrado
├── NoProviderError        sem default para este ativo/intervalo
├── MultiDownloadError     todos os símbolos do lote falharam
└── StreamingNotSupportedError
```

`NotImplementedError` ainda pode aparecer se você chama
`Ticker.financials` num provedor sem demonstrações (CoinGecko, Stooq).
Isso é lacuna de capacidade, não ticker ausente.

## SymbolNotFound

O provedor não devolveu barras (ou um “not found” explícito). Campos:

- `symbol`
- `provider` (em teoria pode ser `None`; em geral vem preenchido)
- `hint` — para tickers à vista brasileiros no padrão `ABCD1` / `ABCD11`,
  o hint é `{symbol}.SA`

```python
try:
    cb.download("PETR4")
except cb.SymbolNotFound as err:
    assert err.hint == "PETR4.SA"
    cb.download(err.hint)
```

**Não** concatenamos `.SA` sozinhos. Reescrita silenciosa buscaria o
papel errado se você quisesse outra coisa.

## MissingAPIKey

Quando você pinna `provider="twelvedata"` (ou outra fonte com chave) sem
`CAPYBUCKS_TWELVEDATA_KEY` e sem `~/.capybucks.toml`. Também quando o JSON
da Twelve Data diz que a chave é inválida.

A mensagem diz qual variável de ambiente setar. Não faça commit de
`.env`.

## RateLimitError

O vendor pediu para ir mais devagar. Backoff/retry pode já ter rodado no
cliente. Se ainda levantar, espere ou pinne **outro** provedor
explicitamente — o capybucks não troca de fonte por você.

## MultiDownloadError

Só quando **nenhum** ticker do lote produziu frame. Olhe `exc.errors`:
dict de símbolo → erro daquele símbolo.

Um lote misto (dois vivos, um morto) **não** levanta isto. O morto cai em
`frame.attrs["errors"]`.

## ProviderError

Catch-all para fonte que respondeu errado: HTML em vez de CSV (challenge
do Stooq), JSON inesperado, HTTP 4xx/5xx não mapeado com mais detalhe.

## O que você não deve fazer

```python
df = cb.download("AAPL")
if df.empty:  # não é assim que dado ausente é sinalizado
    ...
```

Chamada bem-sucedida tem linhas. Ausência é exceção. Buracos de lote são
`attrs["errors"]`.
