from __future__ import annotations

import importlib.util
from pathlib import Path

_BUILD = Path(__file__).resolve().parents[1] / "docs" / "build.py"
_spec = importlib.util.spec_from_file_location("capybucks_docs_build", _BUILD)
assert _spec is not None and _spec.loader is not None
_docs_build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_docs_build)
rewrite_hoisted_asset_paths = _docs_build.rewrite_hoisted_asset_paths


def test_rewrite_home_page_static_is_same_directory() -> None:
    html = '<link href="../_static/styles/theme.css" rel="stylesheet" />'
    assert (
        rewrite_hoisted_asset_paths(html)
        == '<link href="_static/styles/theme.css" rel="stylesheet" />'
    )


def test_rewrite_guide_page_static_is_one_level_up() -> None:
    html = '<script src="../../_static/documentation_options.js"></script>'
    assert (
        rewrite_hoisted_asset_paths(html)
        == '<script src="../_static/documentation_options.js"></script>'
    )


def test_rewrite_leaves_in_tree_links_alone() -> None:
    html = '<a href="guide/download.html">User guide</a>'
    assert rewrite_hoisted_asset_paths(html) == html
