from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable, Coroutine
from typing import TypeVar

T = TypeVar("T")


def run_sync(factory: Callable[[], Coroutine[object, object, T]]) -> T:
    """Run an async factory from sync code, including Jupyter's running loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())

    result: list[T] = []
    error: list[BaseException] = []

    def _runner() -> None:
        try:
            result.append(asyncio.run(factory()))
        except BaseException as exc:  # noqa: BLE001 — re-raise on the caller thread
            error.append(exc)

    thread = threading.Thread(target=_runner, name="capybucks-sync")
    thread.start()
    thread.join()
    if error:
        raise error[0]
    return result[0]
