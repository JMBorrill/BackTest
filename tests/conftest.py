import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

TOKEN = "test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}

REQUEST = {
    "symbol": "SYNTH",
    "start": "2020-01-01",
    "end": "2023-12-31",
    "fast_window": 20,
    "slow_window": 50,
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client with its own data directory and token."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    rng = np.random.default_rng(11)
    dates = pd.bdate_range("2020-01-01", periods=900)
    closes = 100 * np.cumprod(1 + rng.normal(0.0004, 0.011, len(dates)))
    pd.DataFrame({"date": dates, "close": closes}).to_csv(
        data_dir / "SYNTH.csv", index=False
    )

    monkeypatch.setenv("API_TOKEN", TOKEN)
    monkeypatch.setenv("DATA_DIR", str(data_dir))

    from backend.config import get_settings

    get_settings.cache_clear()
    from backend.main import create_app

    with TestClient(create_app(), raise_server_exceptions=False) as test_client:
        yield test_client
    get_settings.cache_clear()
