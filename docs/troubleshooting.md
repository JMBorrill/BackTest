# Troubleshooting

The five failures that actually came up while building and testing this API,
in the order you are likely to hit them. Each one is reproducible from the
Postman collection.

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

> **Scope.** The single shared bearer token here is this demonstration API's
> simplified auth model, not a representation of any payments provider's
> production authentication. Real integrations follow that provider's current
> documentation, key management and access controls.

---

## 422 `validation_failed`

```json
{"error": {"code": "validation_failed", "message": "Request failed validation",
  "fields": [{"path": "fast_window", "message": "must be less than slow_window"}]}}
```

**Cause.** Valid JSON, impossible configuration — here a 50-day fast average
against a 20-day slow one.

**Diagnosis.** `fields[].path` names the input to change. This was worth
getting right: the check was first written as a whole-model validator, which
reported the path as the model rather than the field, so the response said
something was wrong without saying what.

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

**Diagnosis.** This originally behaved much worse: configuration was read
lazily on first use, so the server started cleanly and the first request came
back as an opaque `500 internal_error`. The traceback was in the log, not the
response, which is correct — but it meant a startup problem presented as a
runtime one. Configuration is now read at startup.

**Fix.** `cp .env.example .env` and set `API_TOKEN`.

**Prevention.** Fail at startup, not on the first customer request. A missing
credential that only shows up under traffic is a production incident.

---

## When to escalate

The four cases above are answerable from the response body alone. Escalate
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
