"""Backtesting API - two endpoints.

    uvicorn backend.main:app --reload

GET  /health         unauthenticated; says which environment is running
POST /v1/backtests   authenticated; validates, runs one backtest, returns metrics
"""
import logging

from fastapi import Depends, FastAPI

from backend import errors
from backend.auth import require_token
from backend.backtest import (
    NoDataInRangeError,
    NotEnoughDataError,
    UnknownSymbolError,
    load_prices,
    run,
)
from backend.config import Settings, get_settings
from backend.errors import ApiError
from backend.schemas import BacktestRequest, BacktestResponse

logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    # Read configuration now, not on the first request. A missing variable
    # should stop the server starting, not turn into a confusing 500 later.
    get_settings()

    app = FastAPI(title="Backtesting API", version="1.0.0")
    errors.install(app)

    @app.get("/health")
    def health(settings: Settings = Depends(get_settings)) -> dict:
        return {"status": "ok", "environment": settings.environment}

    @app.post(
        "/v1/backtests",
        response_model=BacktestResponse,
        dependencies=[Depends(require_token)],
    )
    def create_backtest(
        payload: BacktestRequest, settings: Settings = Depends(get_settings)
    ) -> BacktestResponse:
        try:
            prices = load_prices(
                payload.symbol, str(payload.start), str(payload.end), settings.data_dir
            )
            result = run(prices, payload.fast_window, payload.slow_window)
        except UnknownSymbolError as exc:
            # A typed error, so a symbol the customer has not been enabled
            # for is a 422 they can act on rather than a 500 from pandas.
            raise ApiError(422, "unknown_symbol", str(exc)) from exc
        except NoDataInRangeError as exc:
            # The range is not short - it is empty. Different fix, so a
            # different message.
            raise ApiError(
                422,
                "validation_failed",
                str(exc),
                fields=[{"path": "start", "message": "no data in this date range"}],
            ) from exc
        except NotEnoughDataError as exc:
            raise ApiError(
                422,
                "validation_failed",
                str(exc),
                fields=[
                    {
                        "path": "start",
                        "message": "date range holds fewer bars than slow_window",
                    }
                ],
            ) from exc

        return BacktestResponse(symbol=payload.symbol.upper(), **result)

    return app


app = create_app()
