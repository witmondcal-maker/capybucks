# Cache e proveniência

Duas ideias, um objetivo: você deve sempre saber **qual vendor** produziu
um número, e não deve pagar o mesmo range da Yahoo duas vezes na mesma
tarde.

## Proveniência (`df.attrs`)

Depois de `download()` / `Ticker.history()`, o DataFrame carrega:

| Chave | Significado |
|---|---|
| `provider` | Nome no registry (`yahoo`, `twelvedata`, …) |
| `delayed` | `True` se este caminho não é print licenciado em tempo real |
| `adjustment` | `split_and_dividend` quando `auto_adjust=True` e a fonte ajustou; senão `none` |
| `asof` | Hora do fetch neste processo |
| `currency` | Da fonte, quando ela manda |
| `errors` | Lote: mapa de símbolos que falharam → mensagem (muitas vezes `{}`) |

`attrs` é o saco de metadados do pandas. `df.copy()` em geral preserva;
remontar o frame a partir de numpy pode dropar. Se você persistir parquet
por conta, grave os attrs ou perde o contrato.

Intraday vs diário, ajustado vs cru, atrasado vs ao vivo: se isso se
mistura numa coluna sem flag, o gráfico continua bonito. A proveniência
existe para isso não acontecer quieto.

## Cache em disco

Diretório padrão: `~/.cache/capybucks`, sobrescrito com
`CAPYBUCKS_CACHE_DIR`.

Layout:

```
{root}/{provider}/{SYMBOL}/{interval}/ohlcv.parquet
{root}/{provider}/{SYMBOL}/{interval}/meta.json
```

O **provedor está no path**. O diário AAPL da Yahoo não é o da Twelve
Data. Fundir no disco seria o mesmo bug do fallback silencioso.

O que se guarda é a série mais a cobertura (`covered_from` /
`covered_to` na proveniência). O próximo pedido sobreposto só busca
**buracos**. Fins de semana e feriados na janela não disparam refetch
infinito.

```python
cb.download("AAPL", period="1y")  # rede
cb.download("AAPL", period="1y")  # cache
cb.download("AAPL", period="1y", cache=False)  # rede, sem gravar
```

Testes apontam o cache para um temp dir. Você pode fazer o mesmo:

```python
from pathlib import Path
from capybucks.async_api import configure_cache

configure_cache(Path("/tmp/capybucks-cache"))
```

`configure_cache(None)` tira a camada de disco (a de memória continua
in-process).

## Só o mesmo provedor

`merge_history` recusa combinar dois `History` com
`provenance.provider` diferente. Isso é enforced no core, não um
conselho no README.

## Invalidação

Não há invalidação automática do tipo “a Yahoo reapresentou ontem”. Se
você souber de um restatement, apague a pasta daquele símbolo ou chame
com `cache=False`. TTL de cache de propósito não é chutado — pergunte
antes de inventar um (veja `AGENTS.md`).
