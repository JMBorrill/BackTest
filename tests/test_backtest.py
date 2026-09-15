"""The calculation: series where the answer is known by hand, plus one
regression test pinning the published numbers for the shipped dataset."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backend.backtest import NotEnoughDataError, UnknownSymbolError, load_prices, run

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


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


@pytest.mark.skipif(
    not (DATA_DIR / "SYNTH.csv").exists(),
    reason="run scripts/make_synthetic_data.py first",
)
def test_synth_dataset_still_produces_the_published_numbers():
    """The seeded dataset is identical on every machine, so these are fixed
    values, not a range. They are the numbers quoted in the README. Any
    change to the maths - dropping the position shift, for instance - moves
    at least one of them and fails here."""
    prices = load_prices("SYNTH", "2019-01-01", "2024-12-31", DATA_DIR)
    result = run(prices, fast_window=20, slow_window=50)

    assert result["bars"] == 1500
    assert result["start"] == "2019-01-02"
    assert result["end"] == "2024-10-01"
    assert result["metrics"]["trades"] == 20
    assert result["metrics"]["total_return"] == pytest.approx(-0.1908, abs=1e-4)
    assert result["metrics"]["cagr"] == pytest.approx(-0.0349, abs=1e-4)
    assert result["metrics"]["max_drawdown"] == pytest.approx(-0.3079, abs=1e-4)
    assert result["benchmark"]["total_return"] == pytest.approx(0.1808, abs=1e-4)
