from __future__ import annotations

import os
import sys
from pathlib import Path

DOC_LANG = os.environ.get("DOC_LANG", "en")
_IS_PT = DOC_LANG.startswith("pt")

# GitHub Pages project site lives under /capybucks. Empty prefix = site at domain root.
_DOCS_PREFIX = os.environ.get("DOCS_PREFIX", "/capybucks").rstrip("/")
_DOCS_ORIGIN = os.environ.get(
    "DOCS_ORIGIN",
    "https://witmondcal-maker.github.io/capybucks",
).rstrip("/")
_EN_URL = f"{_DOCS_PREFIX}/en/" if _DOCS_PREFIX else "/en/"
_PT_URL = f"{_DOCS_PREFIX}/pt/" if _DOCS_PREFIX else "/pt/"

_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_SRC))

project = "capybucks"
author = "Ricardo Margalho"
copyright = "2026, Ricardo Margalho"
release = "0.0.1"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_autodoc_typehints",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "tasklist",
]
myst_heading_anchors = 3

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "README.md",
    "architecture.md",
    "adr/0000-template.md",
    "pt" if not _IS_PT else "en",
]

language = "pt_BR" if _IS_PT else "en"
root_doc = "pt/index" if _IS_PT else "en/index"

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_logo = "assets/logo.jpg"
html_title = "capybucks"
html_short_title = "capybucks"
html_show_sourcelink = True
html_baseurl = f"{_DOCS_ORIGIN}/"

html_theme_options = {
    "github_url": "https://github.com/witmondcal-maker/capybucks",
    "use_edit_page_button": True,
    "show_toc_level": 2,
    "navbar_align": "left",
    "header_links_before_dropdown": 6,
    "logo": {"text": "capybucks"},
    "external_links": [
        {"name": "English", "url": _EN_URL},
        {"name": "Português", "url": _PT_URL},
    ],
    "footer_start": ["copyright"],
    "footer_end": ["sphinx-version"],
}

html_context = {
    "github_user": "witmondcal-maker",
    "github_repo": "capybucks",
    "github_version": "main",
    "doc_path": "docs",
}

autodoc_typehints = "description"
autodoc_member_order = "bysource"
napoleon_numpy_docstring = False
napoleon_google_docstring = True
typehints_fully_qualified = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
}
