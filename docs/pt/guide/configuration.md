# Configuração

O capybucks roda com **zero config** para ações Yahoo e cripto CoinGecko.
Provedores pagos precisam de chave. Nada neste projeto deve commitar
segredo.

## Chaves de API

Ordem de resolução para o provedor `twelvedata`:

1. Variável de ambiente `CAPYBUCKS_TWELVEDATA_KEY` (não vazia).
2. `~/.capybucks.toml`, tabela `[keys]`, chave `twelvedata`.

Env ganha se os dois existirem. Testes podem redirecionar o toml com
`set_config_path` para o arquivo da home nunca ser lido.

```toml
# ~/.capybucks.toml
[keys]
twelvedata = "cole-a-chave"
```

```bash
# POSIX
export CAPYBUCKS_TWELVEDATA_KEY="cole-a-chave"

# PowerShell
$env:CAPYBUCKS_TWELVEDATA_KEY = "cole-a-chave"
```

Um arquivo `.env` no repo **não** é carregado pela biblioteca. Está no
`.gitignore` para segredo local ficar local. Para testes que precisam da
chave:

```bash
uv run --env-file .env pytest -m live
```

Copie [`.env.example`](../../../.env.example) para `.env` e preencha.
Nunca faça commit de `.env`.

O teste live da Twelve Data olha a **variável de ambiente**, não o toml.
Sete o env (ou `--env-file`) para `pytest -m live`.

## Outras variáveis de ambiente

| Variável | Efeito |
|---|---|
| `CAPYBUCKS_TWELVEDATA_KEY` | Chave Twelve Data |
| `CAPYBUCKS_CACHE_DIR` | Raiz do cache parquet (padrão `~/.cache/capybucks`) |
| `CAPYBUCKS_NO_RATELIMIT=1` | Pula o espaçamento por provedor (testes) |

`CAPYBUCKS_POLYGON_KEY` aparece no `.env.example` como placeholder.
Polygon não está implementado.

## Jupyter / vida do processo

Chaves são lidas na **hora do pedido**, não no import. Exporte o env e
depois importe o capybucks, ou sete o env antes da célula que chama
`download(..., provider="twelvedata")`.
