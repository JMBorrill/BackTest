# Troubleshooting

The failures that come up while integrating against this API, in the order
you are likely to hit them. Every one below except the 500 is reproducible
from the Postman collection; the 500 is forced from the test suite, because
nothing in the shipped API triggers it.

---

## 401 `unauthenticated`

```json
{"error": {"code": "unauthenticated", "message": "Bearer token missing"}}
```

**Cause.** Either no `Authorization` header, or `api_token` is empty in the
selected Postman environment. The committed environment files ship with an
empty token on purpose, so this is the first thing that happens to anyone
who imports them.

**Diagnosis.** The two messages distinguish the cases: "Bearer token
missing" means no header arrived at all — usually the request overrode
collection auth, or the wrong environment is selected. "Bearer token
invalid" means a token arrived and did not match, which is a value problem,
not a wiring problem.

**Fix.** Select the sandbox environment and set `api_token` to the same
value the server was started with. Check the environment selector before
assuming the token is wrong — being pointed at the wrong environment looks
identical from the response.

**Prevention.** Auth is set once at collection level, so individual requests
cannot drift. `GET /health` reports `environment`, which is the cheapest way
to confirm what you are actually talking to.

Requests 3 and 4 of the Postman collection are this pair, kept side by side
so the difference can be shown rather than described.

---

## 422 `validation_failed`

```json
{"error": {"code": "validation_failed", "message": "Request failed validation",
  "fields": [{"path": "fast_window", "message": "must be less than slow_window"}]}}
```

**Cause.** Valid JSON, impossible configuration — here a 50-day fast average
against a 20-day slow one.

**Diagnosis.** `fields[].path` names the input to change. The cross-field
check is a Pydantic field validator rather than a model validator for exactly
this reason: a model validator reports the path as the model, so the response
says something is wrong without saying what.

**Fix.** Correct the named field. Unknown fields are rejected too — a
request with `fast_windows` (plural) is a 422, not a silently ignored typo
and a surprising result.

**Prevention.** Validate before doing any work, and always return a field
path. "Invalid request" without a path turns a ten-second fix into a support
conversation.

---

## 422 `unknown_symbol`

```json
{"error": {"code": "unknown_symbol", "message": "No price data for NOPE. Available: SYNTH"}}
```

**Cause.** No data file for the requested symbol. In a real integration this
is the customer requesting something they have not been enabled for.

**Diagnosis.** The message lists what *is* available, so the answer is in the
response. `Available: none` means something different and more important —
the data directory resolved but was empty, so this is a configuration
problem on our side, not a bad request from the customer.

**Fix.** Customer-side: use a symbol that exists. `Available: none`: run
`python scripts/make_synthetic_data.py`, and check `DATA_DIR` and the
directory the server was started from.

**Prevention.** Error messages that enumerate the valid options end the
guessing. A separate code (`unknown_symbol`, not a generic
`validation_failed`) lets the caller branch on it.

---

## 400 `invalid_json`

```json
{"error": {"code": "invalid_json", "message": "Request body is not valid JSON"}}
```

**Cause.** The body never parsed — usually a trailing comma after hand-editing
in the Postman body tab.

**Diagnosis.** 400 rather than 422 is the signal: the body never reached the
schema, so there is no field to name. If you get a 422 with a field path, the
JSON was fine and the values were wrong.

**Fix.** Fix the JSON. Postman highlights the offending line in the body tab.

**Prevention.** Change values through environment variables rather than
retyping the body.

---

## Server will not start

```
backend.config.ConfigError: Missing environment variable(s): API_TOKEN.
Copy .env.example to .env and fill them in.
```

**Cause.** `API_TOKEN` is not set and has no default.

**Diagnosis.** Configuration is read in `create_app()`, not lazily on first
use. Read lazily, a missing variable would start the server cleanly and turn
the first customer request into an opaque `500 internal_error` — a startup
problem presenting as a runtime one.

**Fix.** `cp .env.example .env` and set `API_TOKEN`.

**Prevention.** A missing credential that only shows up under traffic is a
production incident. Read configuration at startup.

---

## Server starts, but every request is 401 `unauthenticated`

```json
{"error": {"code": "unauthenticated", "message": "Bearer token invalid"}}
```

**Cause.** `API_TOKEN` is set to an empty string — what `cp .env.example .env`
leaves behind if you never edit the file.

**Diagnosis.** The message says *invalid*, not *missing*, so credentials are
arriving and the server has something to compare them against. If your client
is definitely sending the right token, the value on the server side is the
suspect.

**Fix.** Set `API_TOKEN` in `.env` and restart. An empty value is now rejected
at startup with the same `ConfigError` as a missing one, so this should not
survive a restart.

---

## 422 `validation_failed` on a date range

Two different problems share this code, and the `fields[].message` separates
them:

| `fields[0].message` | Means |
|---|---|
| `no data in this date range` | The symbol exists but has no bars between `start` and `end` — usually a range outside the data entirely. |
| `date range holds fewer bars than slow_window` | The range has bars, just not enough to fill the slow moving average. |

The first needs a different range; the second needs a longer range or a
smaller `slow_window`.

---

## When to escalate

The cases above are answerable from the response body alone. Escalate
to engineering when:

- The response is `500 internal_error` — the body carries only a
  `request_id`, by design. Nothing further can be diagnosed without the
  server log line carrying that same id. **Send the `request_id`,** the
  timestamp, the endpoint, and the request body.
- The same request succeeds in sandbox and fails in production. That is a
  configuration difference between environments, not a request problem, and
  it needs someone with access to both.
- The response is correct but the numbers look wrong. That is a question
  about the calculation, not the integration.

Do not escalate a 4xx before checking the `code` and `fields` — those exist
so that first-line support can resolve it.
