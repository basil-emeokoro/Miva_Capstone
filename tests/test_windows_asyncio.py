import os

from src.runtime.windows_asyncio import install_windows_connection_reset_guard


def test_windows_connection_reset_guard_is_platform_safe() -> None:
    if os.name != "nt":
        assert install_windows_connection_reset_guard() is False
        return

    from asyncio import proactor_events

    transport_class = proactor_events._ProactorBasePipeTransport
    original = transport_class._call_connection_lost
    try:
        assert install_windows_connection_reset_guard() is True
        guarded = transport_class._call_connection_lost
        assert getattr(guarded, "_serps_win10054_guard", False) is True
        assert install_windows_connection_reset_guard() is True
        assert transport_class._call_connection_lost is guarded
    finally:
        transport_class._call_connection_lost = original
