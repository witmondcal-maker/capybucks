from __future__ import annotations

import asyncio

import capybucks as cb


async def test_sync_download_inside_running_loop() -> None:
    """Jupyter already has a loop; the sync wrapper must not raise RuntimeError."""
    frame = cb.download("AAPL", period="5d")
    assert not frame.empty
    assert asyncio.get_running_loop().is_running()
