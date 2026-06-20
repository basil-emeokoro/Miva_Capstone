from __future__ import annotations

import os
from typing import Callable


def install_windows_connection_reset_guard() -> bool:
    """Suppress benign WinError 10054 noise from Windows asyncio pipe shutdown.

    Python 3.13 on Windows can report a ConnectionResetError from
    _ProactorBasePipeTransport._call_connection_lost when a browser/client
    disconnects while Streamlit/Uvicorn is closing a pipe transport. The
    Streamlit app remains healthy; the traceback is terminal noise. This guard
    preserves all non-10054 exceptions and is intentionally Windows-only.
    """
    if os.name != "nt":
        return False
    try:
        from asyncio import proactor_events
    except ImportError:
        return False

    transport_class = getattr(proactor_events, "_ProactorBasePipeTransport", None)
    if transport_class is None:
        return False

    original: Callable[..., object] = transport_class._call_connection_lost
    if getattr(original, "_serps_win10054_guard", False):
        return True

    def guarded_call_connection_lost(self: object, exc: BaseException | None) -> object | None:
        try:
            return original(self, exc)
        except ConnectionResetError as error:
            if getattr(error, "winerror", None) == 10054:
                return None
            raise

    guarded_call_connection_lost._serps_win10054_guard = True  # type: ignore[attr-defined]
    transport_class._call_connection_lost = guarded_call_connection_lost
    return True
