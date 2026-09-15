# Data

One CSV per symbol, with `date` and `close` columns. The API reads from here
and never fetches prices at request time, so a request cannot fail because a
third party is down, and the same request always returns the same numbers.

Generate the sample file:

```bash
python scripts/make_synthetic_data.py
```

That writes `SYNTH.csv` — 1,500 bars of a seeded random walk. It is **not
market data**. The seed makes it identical on every machine, which is what
lets the tests and the Postman assertions check exact values.

CSVs are git-ignored; this README is not.
