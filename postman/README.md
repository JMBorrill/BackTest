# Postman

| File | What it is |
|---|---|
| `backtesting-api.postman_collection.json` | 7 requests: health, a successful authenticated call, missing token, invalid token, invalid parameters, unknown symbol, malformed JSON. |
| `sandbox.postman_environment.json` | Sandbox. `api_token` is empty and typed `secret`. |
| `production.postman_environment.json` | Production. Same shape, `base_url` is a placeholder, token empty. |

**This file is the authoritative count: 7 requests, 26 assertions, 0
failures.** Other documents refer to the collection without repeating the
numbers, so there is one place to update.

Two environment files rather than one with a switchable `base_url`: a single
environment makes it possible to fire a production request while believing you
are in sandbox. Separate files make that mistake visible in the environment
selector.

## Run it

1. Import all three files (Import → Files).
2. Select the sandbox environment and set `api_token` to the value the server
   was started with. Leave it out of the file — Postman keeps it locally.
3. Start the API: `uvicorn backend.main:app --port 8000`.
4. Collection → Run.

Request 1 is the health check. Run it on its own first: if it fails,
`base_url` is wrong or the server is not running, and nothing below it will
mean anything.

Requests 3 and 4 are a deliberate pair: the same call with no token and with a
wrong one. Both are `401 unauthenticated`; only the message separates them,
and that is the distinction the worked support ticket relies on.

Request 7 sends a body with a trailing comma. It returns `400 invalid_json`
whether or not a token is sent, because FastAPI decodes the body before the
auth dependency runs.

The 500 path is not in the collection. Nothing reachable from outside
triggers it — it is exercised by `tests/test_api.py` instead, by making a
dependency raise.

## Headless

```bash
npm install newman
npx newman run postman/backtesting-api.postman_collection.json \
  -e postman/sandbox.postman_environment.json \
  --env-var "api_token=$API_TOKEN"
```

`--env-var` keeps the token out of the committed file. The last run is
captured in [`../portfolio/evidence/newman-run.txt`](../portfolio/evidence/newman-run.txt).
