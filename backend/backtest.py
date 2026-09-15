"""The sample workload: one SMA crossover, run with pandas.

Deliberately basic. This project is about the API and how it fails, not
about the strategy - so the maths is short enough to read in a minute and
has no tuning knobs to argue about.

Rule: hold the asset while the fast moving average is above the slow one,
otherwise hold cash.
"""
from pathlib import Path

import pandas as pd


class UnknownSymbolError(Exception):
    """No price file for the requested symbol."""


class NotEnoughDataError(Exception):
    """The date range has fewer bars than the slow moving average needs."""


def available_symbols(data_dir: Path) -> list[str]:
    if not data_dir.exists():
        return []
    return sorted(path.stem.upper() for path in data_dir.glob("*.csv"))


def load_prices(symbol: str, start: str, end: str, data_dir: Path) -> pd.DataFrame:
    """Read one symbol's closes from a CSV. No network call at request time."""
    path = data_dir / f"{symbol.upper()}.csv"
    if not path.exists():
        raise UnknownSymbolError(
            f"No price data for {symbol.upper()}. "
            f"Available: {', '.join(available_symbols(data_dir)) or 'none'}"
        )

    frame = pd.read_csv(path)
    frame.columns = [column.strip().lower() for column in frame.columns]
    frame["date"] = pd.to_datetime(frame["date"])
    window = frame.set_index("date").sort_index().loc[str(start):str(end), ["close"]]

    if window.empty:
        raise NotEnoughDataError(f"No {symbol.upper()} data between {start} and {end}")
    return window


def run(prices: pd.DataFrame, fast_window: int, slow_window: int) -> dict:
    """Run the crossover and return four metrics."""
    if len(prices) <= slow_window:
        raise NotEnoughDataError(
            f"{len(prices)} bars is not enough for a {slow_window}-day average"
        )

    frame = prices.copy()
    frame["fast"] = frame["close"].rolling(fast_window).mean()
    frame["slow"] = frame["close"].rolling(slow_window).mean()

    # The signal is known at the close of day t, so it is traded on day t+1.
    # Without this shift the backtest buys at a price it could not have known.
    signal = (frame["fast"] > frame["slow"]).astype(int)
    position = signal.shift(1).fillna(0)

    daily_return = frame["close"].pct_change().fillna(0)
    strategy_return = position * daily_return
    equity = (1 + strategy_return).cumprod()

    years = len(frame) / 252
    peak = equity.cummax()

    return {
        "bars": len(frame),
        "start": frame.index[0].date().isoformat(),
        "end": frame.index[-1].date().isoformat(),
        "metrics": {
            "total_return": round(float(equity.iloc[-1] - 1), 4),
            "cagr": round(float(equity.iloc[-1] ** (1 / years) - 1), 4) if years else 0.0,
            "max_drawdown": round(float((equity / peak - 1).min()), 4),
            # One trade = one entry. Position changes from 0 to 1 that many times.
            "trades": int((position.diff() > 0).sum()),
        },
        "benchmark": {
            "total_return": round(float(frame["close"].iloc[-1] / frame["close"].iloc[0] - 1), 4),
        },
    }
