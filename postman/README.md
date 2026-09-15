# Postman

| File | What it is |
|---|---|
| `backtesting-api.postman_collection.json` | 6 requests: health, a successful authenticated call, missing token, invalid token, invalid parameters, unknown symbol. |
| `sandbox.postman_environment.json` | Sandbox. `api_token` is empty and typed `secret`. |
| `production.postman_environment.json` | Production. Same shape, `base_url` is a placeholder, token empty. |

Two environment files rather than one with a switchable `base_url`: a single
environment makes it possible to fire a production request while believing you
are in sandbox. Separate files make that mistake visible in the environment
selector.

## Run it

1. Import all three files (Import → Files).
2. Select the sandbox environment and set `api_token` to the value the server
   was started with. Leave it out of the file — Postman keeps it locally.
3. Start the API: `uvicorn backend.main:app --port 8000`.
4. Collection → Run. Expect 6 requests, 23 assertions, 0 failures.

Requests 3 and 4 are a deliberate pair: the same call with no token and with a wrong one. Both are `401 unauthenticated`; only the message separates them, and that is the distinction the worked support ticket relies on.

Request 1 is the health check. Run it on its own first: if it fails, `base_url`
is wrong or the server is not running, and nothing below it will mean anything.

## Headless

```bash
npm install newman
npx newman run postman/backtesting-api.postman_collection.json \
  -e postman/sandbox.postman_environment.json \
  --env-var "api_token=$API_TOKEN"
```

`--env-var` keeps the token out of the committed file.
