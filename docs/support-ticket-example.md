# Worked example: a simulated support ticket

> ## ⚠ THIS IS A SIMULATED EXERCISE
>
> **Nothing on this page is a record of real events.** There is no customer,
> no ticket INT-2291, no integration lead, and no support conversation. The
> customer's words and the reply to them were both written by me, as a
> training exercise against this demonstration API.
>
> What *is* real: every API response quoted below was produced by running
> this repository locally, and each one is reproducible from the Postman
> collection. They are captured in
> [`portfolio/evidence/api-transcript.md`](../portfolio/evidence/api-transcript.md).
>
> The point of the exercise is to show how I would diagnose an integration
> failure and write to a customer about it — not to claim I have handled this
> ticket for an employer.

The bearer token used here is this demonstration API's simplified auth model.
It is not a representation of any payments provider's production
authentication; real integrations follow that provider's current
documentation and access controls.

---

## The scenario

An invented customer, integrating against sandbox, reports that every call is
being rejected.

**Ticket:** INT-2291 *(invented reference)*
**Raised by:** Integration lead, customer side *(invented persona)*
**Severity:** High — the customer's UAT is blocked

## Reported issue *(written for this exercise)*

> We've been integrating against your sandbox since yesterday and every
> single call is coming back rejected. Nothing has changed our end since it
> was working on Tuesday. Can someone look at this urgently — we're supposed
> to be signing off UAT on Friday.

No status code, no response body, no timestamp. First job is to get those.

## Checks performed

**1. Is the service up?** Ruled out "the API is down" before asking the
customer for anything.

```
GET /health -> 200
{"status": "ok", "environment": "sandbox"}
```

Service is up and is the sandbox environment. Not an outage.

**2. Asked the customer for the exact response**, specifically the status
code and the full body. They sent:

```json
{"error": {"code": "unauthenticated", "message": "Bearer token invalid"}}
```

That narrows it immediately. `unauthenticated` is an auth failure, and
crucially the message is *invalid*, not *missing* — a token did arrive, it
just did not match. So the header is wired up correctly and the value is
wrong. That rules out a whole class of "our HTTP client isn't sending the
header" problems, which is where this would otherwise have gone.

**3. Reproduced both cases** in Postman to confirm the distinction is real
and not something I was assuming. Requests 3 and 4 of the collection exist
for exactly this — they are the same call with no token and with a wrong
one, kept side by side so the difference can be demonstrated rather than
asserted:

| Collection request | Status | `code` | `message` |
|---|---|---|---|
| 3. Missing bearer token | 401 | `unauthenticated` | Bearer token missing |
| 4. Invalid bearer token | 401 | `unauthenticated` | Bearer token invalid |
| 2. Run a backtest | 200 | — | returns metrics |

Same status, same code, different message. Anything that reported only
"401 unauthenticated" would have left both possibilities open and cost
another round trip with the customer.

**4. Asked what changed on Tuesday.** The customer had rotated their own
staging secrets on Wednesday morning as part of an unrelated security task,
and their sandbox token was pulled from the same secret store.

## Evidence

- `GET /health` returning `200` with `environment: sandbox` — service up.
- Customer's own response body showing `"message": "Bearer token invalid"`.
- A successful `200` from the same endpoint with the correct token, from my
  Postman run, same timestamp window — proving the endpoint itself was fine
  throughout.

## Resolution

The customer's secret rotation had replaced the sandbox token with a value
that was never issued for our API. I reissued the sandbox token, they updated
their store, and their next call returned `200`.

Total time to diagnose after receiving the response body: under five
minutes. Time spent before that, waiting for the body: most of the ticket.

## The reply I would send

> Drafted for this exercise; not sent to anyone.
>
> Hi — thanks for the response body, that was the bit we needed.
>
> The `401` you're seeing is specifically `"Bearer token invalid"` rather
> than `"missing"`, which tells us your integration *is* sending the header
> correctly — the token value itself just isn't one we recognise. That lines
> up with the secret rotation you ran on Wednesday morning.
>
> I've reissued your sandbox token; it's in the secure link below. Once your
> secret store has it, your existing requests should work unchanged — no code
> changes needed at your end.
>
> Two things worth knowing for the future. First, `GET /health` is
> unauthenticated, so it's a quick way to separate "the API is down" from
> "our credentials are wrong" before raising a ticket. Second, every error we
> return has a stable `error.code` — if you can include that and the response
> body when something fails, we can usually skip a round trip.
>
> I'll leave this open until you confirm UAT is unblocked.

Note what the reply does *not* do: it does not say "you broke it". The cause
was on the customer's side, and saying so plainly is fine — but the useful
part is the diagnostic they can run themselves next time.

## When escalation would have been appropriate

This one did not need escalating. It would have, if:

- The response had been `500 internal_error`. That body carries only a
  `request_id`; nothing more can be determined without the server log line
  under the same id. I would have escalated with the `request_id`, timestamp,
  endpoint and request body attached.
- The correct token had returned `401` from my own Postman run too. That
  moves the fault to our side — a token store or auth configuration problem,
  not a customer one.
- The same request had succeeded in sandbox and failed in production. That is
  an environment configuration difference and needs someone with access to
  both.
- The customer had been unable to reach `/health` at all from their network.
  That is connectivity or allowlisting, and belongs with whoever owns the
  edge.
