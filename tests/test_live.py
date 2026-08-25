from __future__ import annotations

import os

import pytest

import capybucks as cb
from capybucks.core.bootstrap import install_default_providers
from capybucks.core.registry import get_registry, reset_registry

pytestmark = pytest.mark.live


def _live_registry() -> None:
    reset_registry()
    install_default_providers(get_registry())


def test_yahoo_aapl_live() -> None:
    _live_registry()
    frame = cb.download("AAPL", period="5d", provider="yahoo", cache=False)
    assert not frame.empty
    assert frame.attrs["provider"] == "yahoo"


def test_coingecko_btc_live() -> None:
    _live_registry()
    frame = cb.download("BTC-USD", period="5d", cache=False)
    assert not frame.empty
    assert frame.attrs["provider"] == "coingecko"


@pytest.mark.skipif(
    not os.environ.get("CAPYBUCKS_TWELVEDATA_KEY"),
    reason="CAPYBUCKS_TWELVEDATA_KEY is not set",
)
def test_twelvedata_aapl_live() -> None:
    _live_registry()
    frame = cb.download("AAPL", period="5d", provider="twelvedata", cache=False)
    assert not frame.empty
    assert frame.attrs["provider"] == "twelvedata"
