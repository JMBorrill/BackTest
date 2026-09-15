# Backtesting API — an integration and troubleshooting exercise

I built a small authenticated REST API and used Postman to reproduce a
customer onboarding workflow: check the service is up, make a successful
authenticated call, then work through the failures that come up during
integration — investigating each one, verifying the sandbox configuration,
documenting the resolution, and preparing a go-live checklist.

The API runs a moving-average backtest. **The calculation is not the point** —
it is a sample workload, kept deliberately basic, so that the interesting
part is the integration surface: authentication, validation, error responses,
environment separation, and what you do when a call fails.

Two endpoints:

```
GET  /health         unauthenticated. Reports which environment is running.
POST /v1/backtests   authenticated. Validates, runs, returns four metrics.
```

---

## The five-minute version

Python 3.10 or newer. Last validated on 3.10.12 from a clean virtual
environment.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # set API_TOKEN to any string
python scripts/make_synthetic_data.py
pytest -q                          # 18 tests

uvicorn backend.main:app --port 8000
```

`.venv/`, `.env` and the generated CSVs are git-ignored — no virtual
environment and no credential is ever committed.

Then import `postman/backtesting-api.postman_collection.json` and
`postman/sandbox.postman_environment.json`, set `api_token`, and run the
collection: 6 requests, 23 assertions.

Read in this order:

1. [`docs/support-ticket-example.md`](docs/support-ticket-example.md) — a
   **simulated** ticket worked end to end, including the reply to the
   customer. The customer is invented; the API responses in it are real and
   reproducible.
2. [`docs/troubleshooting.md`](docs/troubleshooting.md) — the five failures,
   with how each was diagnosed and when to escalate.
3. [`docs/go-live-checklist.md`](docs/go-live-checklist.md) — what to verify
   before a customer points at production, and what requires approval first.
4. [`docs/implementation-tracker.md`](docs/implementation-tracker.md) — a
   **simulated** three-customer tracker: milestones, response commitments,
   risks, dependencies and handover on one page.

---

## Example request

```bash
curl -X POST http://127.0.0.1:8000/v1/backtests \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"SYNTH","start":"2019-01-01","end":"2024-12-31",
       "fast_window":20,"slow_window":50}'
```

```json
{
  "symbol": "SYNTH",
  "start": "2019-01-02",
  "end": "2024-10-01",
  "bars": 1500,
  "metrics": {
    "total_return": -0.1908,
    "cagr": -0.0349,
    "max_drawdown": -0.3079,
    "trades": 20
  },
  "benchmark": { "total_return": 0.1808 }
}
```

The strategy loses to buy-and-hold here. That is the expected result of a
moving-average crossover on a random walk — there is no trend to follow —
and it is reported as it came out rather than tuned until it looked better.

## Errors

Every failure uses one shape, so a caller can handle all of them the same
way:

```json
{"error": {"code": "validation_failed", "message": "...", "fields": [...]}}
```

`code` is the stable part — it is what the Postman tests assert on and what a
support conversation quotes.

| Status | `code` | Meaning |
|---|---|---|
| 400 | `invalid_json` | Body did not parse. No field path, because it never reached the schema. |
| 401 | `unauthenticated` | Token missing or wrong. Carries `WWW-Authenticate`. |
| 422 | `validation_failed` | Valid JSON, invalid values. Carries `fields[].path`. |
| 422 | `unknown_symbol` | No data for that symbol. Message lists what is available. |
| 500 | `internal_error` | Unexpected. Body carries a `request_id` only; the traceback goes to the log under the same id. |

The two 401 messages differ deliberately. "Bearer token missing" means no
usable header arrived, so the integration is not sending credentials at all.
"Bearer token invalid" means one arrived and did not match — the wiring is
right and the value is stale. Requests 3 and 4 of the Postman collection are
that pair, and the distinction is what the
[worked support ticket](docs/support-ticket-example.md) turns on.

### A note on the authentication model

A single shared bearer token is this demonstration API's **simplified** auth
model. It was chosen because it is the smallest scheme that still exercises a
real 401 path and a real credential-rotation failure.

It is not a representation of how any particular payments provider — Modulr
included — authenticates in production, and nothing here should be treated as
a template for one. Real integrations follow the provider's own current
documentation, key management, and access controls, which cover things this
project deliberately does not: per-customer credentials, rotation, signing,
and IP or certificate controls.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `API_TOKEN` | *(none)* | Bearer token. No default — the server will not start without it. |
| `ENVIRONMENT` | `sandbox` | Reported by `/health`, so you can tell what you are pointed at. |
| `DATA_DIR` | `data` | Where the price CSVs live. |

`.env` is git-ignored. `.env.example` is committed and contains no secret.

## Postman

Two environment files, not one with a switchable `base_url` — a single
environment makes it possible to fire a production request while believing
you are in sandbox. Both ship with `api_token` empty and typed `secret`.

Headless:

```bash
npm install newman
npx newman run postman/backtesting-api.postman_collection.json \
  -e postman/sandbox.postman_environment.json \
  --env-var "api_token=$API_TOKEN"
```

Last run is captured in
[`portfolio/evidence/newman-run.txt`](portfolio/evidence/newman-run.txt).

## Tests

```bash
pytest -q
```

18 tests, in two files:

| File | Tests | Covers |
|---|---|---|
| `tests/test_backtest.py` | 5 | The calculation, on series where the answer is known by hand: a rising market, a drawdown, the one-entry case, too few bars for the slow window, and an unknown symbol. |
| `tests/test_api.py` | 13 | Health; the happy path; both 401 cases; four validation cases; unknown symbol; malformed JSON; the shared error envelope; the 500 path; and that a missing `API_TOKEN` stops the app starting. |

The two documents marked *simulated* use invented customers to show working
method. Every API response quoted inside them was produced by running this
repository and is reproducible from the Postman collection.

The 500 is forced from the test by making a dependency raise. Nothing in the
shipped API is left broken to demonstrate it.

## Layout

```
backend/
  main.py             the two endpoints
  auth.py             bearer token check
  config.py           environment variables
  errors.py           the one error shape
  schemas.py          request and response validation
  backtest.py         the sample workload
tests/
  test_backtest.py    5 tests on the calculation
  test_api.py         13 tests on the API
  conftest.py         test client fixture
postman/
  backtesting-api.postman_collection.json
  sandbox.postman_environment.json
  production.postman_environment.json
docs/
  troubleshooting.md
  go-live-checklist.md
  support-ticket-example.md      simulated
  implementation-tracker.md      simulated
data/                 price CSVs (generated, git-ignored)
scripts/
  make_synthetic_data.py
portfolio/
  evidence/           captured output from real runs
  case-study/         the generated case-study page and its assets
```

`portfolio/case-study/` holds the HTML page plus the runtime and design-system
files it needs (`support.js`, `_ds/`). They are kept together because the page
references them by relative path; open
`portfolio/case-study/Backtesting API Case Study.dc.html` in a browser. The
README and `docs/` carry the same story in text, so the page is optional
reading.

## Data

`scripts/make_synthetic_data.py` writes `data/SYNTH.csv` — a seeded random
walk, identical on every machine, which is what makes the tests and the
Postman assertions reproducible. It is **not market data**, and every figure
in this repository comes from it.

## What this is not

A demonstration project, not a production service. It has a single shared
token, no persistence, no rate limiting, and runs the workload synchronously.
Those limits are listed in the
[go-live checklist](docs/go-live-checklist.md#known-limits-of-this-build)
rather than left for someone to find.
