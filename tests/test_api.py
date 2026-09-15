"""The API surface: the happy path, and each way a caller gets it wrong."""
import pytest

from tests.conftest import AUTH, REQUEST


def test_health_needs_no_token_and_names_the_environment(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["environment"] == "sandbox"


def test_valid_request_returns_metrics(client):
    response = client.post("/v1/backtests", json=REQUEST, headers=AUTH)
    assert response.status_code == 200

    body = response.json()
    assert body["symbol"] == "SYNTH"
    assert body["bars"] > 50
    assert set(body["metrics"]) == {"total_return", "cagr", "max_drawdown", "trades"}
    assert "total_return" in body["benchmark"]


def test_missing_token_is_401_with_a_challenge(client):
    response = client.post("/v1/backtests", json=REQUEST)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
    assert "Bearer" in response.headers["www-authenticate"]


def test_wrong_token_is_401(client):
    response = client.post(
        "/v1/backtests", json=REQUEST, headers={"Authorization": "Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_fast_window_not_below_slow_names_the_field(client):
    response = client.post(
        "/v1/backtests", json={**REQUEST, "fast_window": 50, "slow_window": 20}, headers=AUTH
    )
    assert response.status_code == 422

    error = response.json()["error"]
    assert error["code"] == "validation_failed"
    assert error["fields"][0]["path"] == "fast_window"
    assert error["fields"][0]["message"] == "must be less than slow_window"


def test_end_before_start_is_rejected(client):
    response = client.post(
        "/v1/backtests", json={**REQUEST, "start": "2023-01-01", "end": "2022-01-01"},
        headers=AUTH,
    )
    assert response.status_code == 422
    assert response.json()["error"]["fields"][0]["path"] == "end"


def test_unknown_field_is_rejected_rather_than_ignored(client):
    response = client.post("/v1/backtests", json={**REQUEST, "fast_windows": 20}, headers=AUTH)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_failed"


def test_unknown_symbol_is_422_and_lists_what_is_available(client):
    response = client.post("/v1/backtests", json={**REQUEST, "symbol": "NOPE"}, headers=AUTH)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unknown_symbol"
    assert "SYNTH" in response.json()["error"]["message"]


def test_date_range_too_short_names_the_slow_window(client):
    response = client.post(
        "/v1/backtests", json={**REQUEST, "start": "2020-01-01", "end": "2020-02-01"},
        headers=AUTH,
    )
    assert response.status_code == 422

    error = response.json()["error"]
    assert error["code"] == "validation_failed"
    assert error["fields"][0]["message"] == "date range holds fewer bars than slow_window"


def test_malformed_json_is_400(client):
    response = client.post(
        "/v1/backtests",
        content=b'{"symbol": "SYNTH",}',
        headers={**AUTH, "Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_json"


def test_every_failure_uses_the_same_envelope(client):
    """401, 422 and 400 must be shaped identically - that is what lets a
    caller (and the Postman tests) handle all of them the same way."""
    responses = [
        client.post("/v1/backtests", json=REQUEST),
        client.post("/v1/backtests", json={**REQUEST, "symbol": "NOPE"}, headers=AUTH),
        client.post("/v1/backtests", content=b"{,}",
                    headers={**AUTH, "Content-Type": "application/json"}),
    ]
    for response in responses:
        body = response.json()
        assert set(body) == {"error"}
        assert isinstance(body["error"]["code"], str)


def test_unexpected_error_returns_an_id_not_a_stack_trace(client, monkeypatch):
    """The 500 path, forced from the test - nothing in the app is left broken."""

    def boom(*args, **kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr("backend.main.load_prices", boom)

    response = client.post("/v1/backtests", json=REQUEST, headers=AUTH)
    assert response.status_code == 500
    assert set(response.json()["error"]) == {"code", "request_id"}
    assert response.json()["error"]["request_id"].startswith("req_")
    assert "Traceback" not in response.text


def test_unknown_path_uses_the_same_error_envelope(client):
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_wrong_method_uses_the_same_error_envelope(client):
    response = client.get("/v1/backtests")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_symbol_cannot_contain_a_path(client):
    """A symbol becomes part of a filename, so a path is rejected by the
    schema rather than reaching load_prices."""
    response = client.post(
        "/v1/backtests", json={**REQUEST, "symbol": "../data/SYNTH"}, headers=AUTH
    )
    assert response.status_code == 422

    error = response.json()["error"]
    assert error["code"] == "validation_failed"
    assert error["fields"][0]["path"] == "symbol"


def test_date_range_with_no_data_says_so(client):
    """Empty is not the same problem as short, so it must not borrow the
    short-range message."""
    response = client.post(
        "/v1/backtests",
        json={**REQUEST, "start": "2030-01-01", "end": "2031-02-01"},
        headers=AUTH,
    )
    assert response.status_code == 422

    error = response.json()["error"]
    assert error["fields"][0]["message"] == "no data in this date range"


def test_missing_api_token_stops_the_app_starting(monkeypatch):
    from backend.config import ConfigError, get_settings

    monkeypatch.delenv("API_TOKEN", raising=False)
    get_settings.cache_clear()
    from backend.main import create_app

    with pytest.raises(ConfigError) as caught:
        create_app()
    assert "API_TOKEN" in str(caught.value)
    get_settings.cache_clear()


def test_empty_api_token_stops_the_app_starting(monkeypatch):
    """`cp .env.example .env` and nothing else leaves API_TOKEN empty. That
    must fail at startup too, not start a server that 401s every call."""
    from backend.config import ConfigError, get_settings

    monkeypatch.setenv("API_TOKEN", "")
    get_settings.cache_clear()
    from backend.main import create_app

    with pytest.raises(ConfigError) as caught:
        create_app()
    assert "API_TOKEN" in str(caught.value)
    get_settings.cache_clear()
