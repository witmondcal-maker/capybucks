# Documentação capybucks

Dados de mercado em uma linha: `download()` / `Ticker`, DataFrames pandas,
erros tipados e um caminho para APIs pagas sem trocar o import.

```{admonition} O software não é a licença dos dados
:class: warning

O **software** é MIT. Os **dados** não são. O capybucks não é afiliado à
Yahoo, Inc. O caminho padrão de ações usa endpoints unofficial da Yahoo
Finance; em geral vêm atrasados (~15 minutos) e os termos da Yahoo
restringem coleta automatizada. Não redistribua dados do provedor.
`df.attrs["delayed"]` existe para um print atrasado não se passar por
tempo real. Veja os [termos da Yahoo](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html).
```

## Instalação

```bash
pip install capybucks
```

Python 3.11 ou mais novo. Extras opcionais: `[calendars]`, `[stream]`, `[polars]`.
A partir de um clone: `uv sync --all-groups` ou `pip install -e .`.

## Início rápido

```python
import capybucks as cb

df = cb.download("AAPL", period="1mo")
print(df.attrs["provider"], df.attrs["delayed"])

aapl = cb.Ticker("AAPL")
aapl.history(period="1mo")
aapl.financials
aapl.option_chain()
```

Vários símbolos (um nome morto não trava os outros):

```python
cb.download(["AAPL", "MSFT", "GOOG"], period="1mo")
```

Cripto e um pin pago:

```python
cb.download("BTC-USD", period="5d")
cb.download("AAPL", provider="twelvedata")  # precisa de CAPYBUCKS_TWELVEDATA_KEY
```

A superfície completa está em {doc}`api/index`. Os guias começam em
{doc}`guide/index`. O notebook está em
[`examples/getting_started.ipynb`](https://github.com/witmondcal-maker/capybucks/blob/main/examples/getting_started.ipynb).

```{toctree}
:maxdepth: 1
:hidden:

guide/index
api/index
development/index
```
