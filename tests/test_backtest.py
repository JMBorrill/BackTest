"""The calculation. Five tests on series where the answer is known by hand."""
import numpy as np
import pandas as pd
import pytest

from backend.backtest import NotEnoughDataError, UnknownSymbolError, load_prices, run


def frame(closes):
    dates = pd.bdate_range("2020-01-01", periods=len(closes))
    return pd.DataFrame({"close": closes}, index=pd.DatetimeIndex(dates, name="date"))


def test_rising_market_captures_most_but_not_all_of_buy_and_hold():
    # Rising every day, so the strategy goes long as soon as the moving
    # averages are defined and never sells. It still trails buy and hold,
    # because it sits in cash during the warm-up bars - which is the
    # behaviour to check, not an imperfection to hide.
    prices = frame(100 * np.cumprod(np.repeat(1.01, 120)))
    result = run(prices, fast_window=2, slow_window=3)
    assert 0 < result["metrics"]["total_return"] < result["benchmark"]["total_return"]


def test_drawdown_is_negative_when_equity_falls():
    closes = list(100 * np.cumprod(np.repeat(1.02, 60))) + list(
        100 * 1.02**60 * np.cumprod(np.repeat(0.98, 60))
    )
    assert run(frame(closes), 5, 20)["metrics"]["max_drawdown"] < 0


def test_a_market_that_only_rises_produces_exactly_one_entry():
    # Buy once when the averages cross, then never sell.
    prices = frame(100 * np.cumprod(np.repeat(1.01, 120)))
    assert run(prices, 2, 3)["metrics"]["trades"] == 1


def test_too_few_bars_for_the_slow_window_is_rejected():
    with pytest.raises(NotEnoughDataError):
        run(frame([100.0] * 10), fast_window=2, slow_window=50)


def test_unknown_symbol_lists_what_is_available(tmp_path):
    (tmp_path / "SYNTH.csv").write_text("date,close\n2020-01-01,100\n")
    with pytest.raises(UnknownSymbolError) as caught:
        load_prices("NOPE", "2020-01-01", "2020-12-31", tmp_path)
    assert "SYNTH" in str(caught.value)
