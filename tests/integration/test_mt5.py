import os

import pytest

from data import mt5_client

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.getenv("MT5_LOGIN") or not os.getenv("MT5_PASSWORD") or not os.getenv("MT5_SERVER"),
    reason="MT5 credentials are not configured",
)
def test_mt5_connection_returns_account_info():
    pytest.importorskip("MetaTrader5")

    try:
        mt5_client.disconnect()
        assert mt5_client.connect() is True

        account = mt5_client.account_info()
        assert account is not None

        account_login = getattr(account, "login", None)
        if account_login is None and hasattr(account, "get"):
            account_login = account.get("login")

        assert account_login == int(os.environ["MT5_LOGIN"])
    finally:
        mt5_client.disconnect()
