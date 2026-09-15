"""Write data/SYNTH.csv - a deterministic fake price series.

This is NOT market data and is not named after a real ticker. It exists so
that tests and demos produce the same numbers on every machine. Real
portfolio numbers come from scripts/fetch_prices.py instead.

    python scripts/make_synthetic_data.py
"""
import numpy as np
import pandas as pd

SEED = 42
DAYS = 1500
START = "2019-01-02"


def main() -> None:
    rng = np.random.default_rng(SEED)
    dates = pd.bdate_range(START, periods=DAYS)
    # Random walk with a small upward drift, so trends exist to trade.
    daily = rng.normal(loc=0.0004, scale=0.011, size=DAYS)
    close = 100 * np.cumprod(1 + daily)

    frame = pd.DataFrame({"date": dates.date, "close": close.round(4)})
    frame.to_csv("data/SYNTH.csv", index=False)
    print(f"wrote data/SYNTH.csv - {len(frame)} rows, "
          f"{frame.date.iloc[0]} to {frame.date.iloc[-1]}")


if __name__ == "__main__":
    main()
