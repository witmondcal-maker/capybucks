# Documentation (contributors)

Readers use the hosted site:
[https://witmondcal-maker.github.io/capybucks/](https://witmondcal-maker.github.io/capybucks/)
(English) and
[https://witmondcal-maker.github.io/capybucks/pt/](https://witmondcal-maker.github.io/capybucks/pt/)
(Portuguese). You do not need to build Sphinx to consume the library.

This folder is the **source**. CI publishes HTML to GitHub Pages on every
push to `main`. PRs only check that the site still builds.

## Build locally

From the repository root:

```bash
uv sync --all-groups
uv run --group docs python docs/build.py
```

`DOCS_PREFIX` defaults to `/capybucks` (GitHub Pages project URL). Language
links in the header are `{prefix}/en/` and `{prefix}/pt/`. For a local
preview at the HTML root, clear the prefix so `/en/` and `/pt/` resolve:

```bash
DOCS_PREFIX= uv run --group docs python docs/build.py
python -m http.server 8000 --directory docs/_build/html
```

A custom domain later is the same conf: empty `DOCS_PREFIX` and
`DOCS_ORIGIN` set to that origin.

## Layout

| Path | Role |
|---|---|
| `docs/en/` | English home, guide, API, development |
| `docs/pt/` | Portuguese translations of the same slugs |
| `docs/adr/` | Architecture decision records (English in both sites) |
| `docs/architecture.md` | Layer diagram (included from Development) |
| `docs/conf.py` | Sphinx config; `DOC_LANG=en` or `pt` |
| `examples/getting_started.ipynb` | Jupyter walkthrough |

Guide slugs match across languages (`en/guide/download.html` ↔
`pt/guide/download.html`) so switching language keeps you on the same
topic when you go via the home of each tree.

## Writing

User-facing prose lives in `en/guide/` and `pt/guide/`. If you change
`download()` / `Ticker` / errors / providers, update **both** languages.
API pages autodoc the public Python names (identifiers stay English).
