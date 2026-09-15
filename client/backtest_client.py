"""A small HTTP client for the Backtesting API.

Talks to a running server over the network, unlike the test suite, which
uses FastAPI's in-process TestClient and never opens a socket.

    BASE_URL=http://127.0.0.1:8000 API_TOKEN=... python client/backtest_client.py
"""
from __future__ import annotations

import os

import httpx

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
API_TOKEN = os.environ.get("API_TOKEN", "")


class ApiError(Exception):
    """A non-2xx response, unpacked from the API's error envelope."""

    def __init__(self, status: int, code: str, message: str, fields: list | None = None):
        super().__init__(f"{status} {code}: {message}")
        self.status, self.code, self.message, self.fields = status, code, message, fields or []


class BacktestClient:
    def __init__(self, base_url: str = BASE_URL, token: str = API_TOKEN, timeout: float = 10.0):
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    def __enter__(self) -> "BacktestClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self._http.close()

    @staticmethod
    def _unwrap(response: httpx.Response) -> dict:
        if response.is_success:
            return response.json()
        try:
            error = response.json()["error"]
        except (ValueError, KeyError, TypeError):
            # Not this API's envelope - something in front of it answered.
            raise ApiError(response.status_code, "unexpected_response", response.text[:200])
        raise ApiError(
            response.status_code,
            error.get("code", "unknown"),
            # A 500 carries a request_id instead of a message; quote that.
            error.get("message") or error.get("request_id", ""),
            error.get("fields"),
        )

    def health(self) -> dict:
        return self._unwrap(self._http.get("/health"))

    def run_backtest(self, symbol: str, start: str, end: str, fast: int, slow: int) -> dict:
        return self._unwrap(
            self._http.post(
                "/v1/backtests",
                json={"symbol": symbol, "start": start, "end": end,
                      "fast_window": fast, "slow_window": slow},
            )
        )


if __name__ == "__main__":
    with BacktestClient() as client:
        print("health:", client.health())

        result = client.run_backtest("SYNTH", "2019-01-01", "2024-12-31", 20, 50)
        print(f"bars:   {result['bars']}  {result['start']} to {result['end']}")
        for name, value in {**result["metrics"], "benchmark": result["benchmark"]["total_return"]}.items():
            print(f"  {name:<13} {value}")

        # The same envelope, read as an exception rather than a dict.
        try:
            client.run_backtest("SYNTH", "2019-01-01", "2024-12-31", 50, 20)
        except ApiError as exc:
            print(f"error:  {exc.status} {exc.code} -> {exc.fields}")
