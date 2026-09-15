# Go-live checklist

Run before a customer's integration is pointed at anything other than
sandbox. Everything below is verified in sandbox, or in production only with
prior authorisation, using an authorised test account, at an agreed time.

**Nothing on this list involves deliberately provoking failures in a live
environment, or making an unapproved call against one.** Error handling is
proved in sandbox, where breaking things is free. Production is confirmed
with one approved, low-impact request and nothing more.

## Before anything touches production

- [ ] Change or release approval is in place, under whatever process applies.
- [ ] An **authorised test account** exists in production — one created for
      this purpose, with no real customer data and no financial impact.
- [ ] The **test payload is agreed in advance** with the customer and
      whoever owns the service: the smallest, lowest-impact request that
      still proves the integration works.
- [ ] A **time window is agreed**, chosen so that someone who can act is
      available — not last thing on a Friday.
- [ ] A **named escalation contact** is on call for the window, and both
      sides have their details.
- [ ] A rollback or stop position is agreed: who calls it, and what happens
      to in-flight work if they do.

## Configuration

- [ ] `GET /health` against the target `base_url` returns `200` and the
      `environment` you expect. If it says `sandbox`, you are not in
      production, whatever the URL looks like. This is a read-only call and
      is safe to run anywhere.
- [ ] Sandbox and production are **separate Postman environments**, not one
      environment with an edited `base_url`. A single environment makes it
      possible to fire a production request believing you are in sandbox.
- [ ] `api_token` is a **secret** variable in each environment, and is empty
      in the committed files.
- [ ] No token appears in the collection, in a saved example response, or in
      a screenshot attached to a ticket.
- [ ] The production credential is different from the sandbox one, was issued
      through the proper channel, and the customer has been told which is
      which.

## Behaviour — proved in sandbox

- [ ] The full collection passes against sandbox: 6 requests, 23 assertions.
- [ ] Both 401 cases are understood, not just passing — a missing token and
      an invalid token return different messages, and support knows what each
      one means.
- [ ] Validation failures return a field path the customer can act on.
- [ ] Error responses use the documented envelope, with `error.code` present.

## Production — the approved call only

- [ ] The one agreed low-impact request is made from the authorised test
      account, within the agreed window, and the response is read and
      recorded.
- [ ] The response uses the same shape as sandbox. If an error comes back, it
      carries `error.code` rather than an HTML page from a proxy in front of
      the API — which would mean the request is not reaching the service.
- [ ] The result is shared with the customer and the escalation contact, and
      the window is formally closed.

Authentication behaviour in production is confirmed by the service owner's
own controls and monitoring, not by firing unauthenticated requests at it.
If there is genuine doubt that auth is enforced, that is a question for the
service owner before go-live, not something to test by probing a live system.

## Handover

- [ ] The customer has the endpoint list, an example request and response,
      and the table of error codes.
- [ ] The customer knows that a `500` carries a `request_id`, and that
      quoting it is what makes the issue traceable.
- [ ] The escalation criteria in
      [troubleshooting.md](troubleshooting.md#when-to-escalate) are agreed and
      shared, so both sides know what first-line resolves and what does not.

## Known limits of this build

Stated here rather than discovered later. This is a demonstration project,
not a production service:

- A single shared bearer token, with no per-customer credentials and no
  rotation. It is a simplified model chosen to exercise a real 401 path, and
  is not how any particular payments provider authenticates — a real
  integration follows that provider's current documentation and controls.
- No persistence, so there is no run history to audit.
- The workload runs synchronously, so a very long date range holds the
  request open.
- No rate limiting.
