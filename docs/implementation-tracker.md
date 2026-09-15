# Implementation tracker

> **⚠ SIMULATED.** Three invented customers, used to show how I would keep
> several implementations visible at once. No real organisation, person or
> commitment appears here. The API behaviours referenced are real and
> reproducible from this repository; the customers are not.

Reporting date: **Mon 14 Sep**. One page, updated weekly, readable in a
stand-up.

## Portfolio at a glance

| Customer | Stage | Target go-live | RAG | Owner | Next action |
|---|---|---|---|---|---|
| Northwind Treasury | Sandbox validation | Fri 2 Oct | 🟢 | Me | Confirm collection run on their infra |
| Calder & Voss | Blocked — credentials | Fri 25 Sep | 🔴 | Me | Chase security for sandbox token reissue |
| Halyard Finance | Kick-off | Fri 13 Nov | 🟡 | Me | Book technical scoping call |

RAG is set on **whether the go-live date is still credible**, not on how the
week felt. Calder & Voss is red because a dependency outside my control has
slipped past the point where the date survives — not because the work is
hard.

---

## Milestones

Same five stages for every customer, so progress is comparable.

| Stage | Northwind | Calder & Voss | Halyard |
|---|---|---|---|
| 1. Kick-off and scope agreed | ✅ 18 Aug | ✅ 1 Sep | 🔄 in progress |
| 2. Sandbox credentials issued | ✅ 20 Aug | ⛔ blocked | ⬜ not started |
| 3. Customer completes sandbox workflow | ✅ 8 Sep | ⬜ | ⬜ |
| 4. Go-live checklist signed off | 🔄 in progress | ⬜ | ⬜ |
| 5. Approved production call, handover | ⬜ 2 Oct | ⬜ 25 Sep | ⬜ 13 Nov |

Stage 4 is the [go-live checklist](go-live-checklist.md). Nothing reaches
stage 5 without an authorised test account, an approved payload, an agreed
window and a named escalation contact.

---

## Response commitments

What I hold myself to during an implementation. These are internal working
commitments for this exercise, not a contractual SLA.

| Item | Commitment | Measured from |
|---|---|---|
| Acknowledge a new integration query | 1 working day | Ticket raised |
| First diagnosis or request for detail | 2 working days | Acknowledgement |
| Credential request passed to security | Same working day | Request received |
| Escalation to engineering | Same working day for a `500`; 2 working days otherwise | Criteria in [troubleshooting.md](troubleshooting.md#when-to-escalate) met |
| Weekly status to the customer | Every Friday | — |

**Current breach:** Calder & Voss credential reissue, raised 3 Sep, still
open on day 8. Logged in risks below rather than quietly carried.

---

## Risks

| # | Risk | Customer | Impact | Likelihood | Mitigation | Owner |
|---|---|---|---|---|---|---|
| R1 | Credential reissue slips again; go-live date fails | Calder & Voss | High | High | Escalated to security lead 11 Sep; proposed a fallback date of 9 Oct so the customer can plan | Me |
| R2 | Two go-lives land in the same week if Calder slips to October | Both | Medium | Medium | Hold 2 Oct for Northwind; Calder's fallback is 9 Oct, deliberately a week apart | Me |
| R3 | Customer tests error handling against production | All | High | Low | Go-live checklist states error handling is proved in sandbox only; covered in handover call | Me |
| R4 | Scope not yet confirmed, so the date is provisional | Halyard | Medium | Medium | Scoping call to be booked this week; date marked provisional until then | Me |

R3 is on the list because it is the expensive mistake in this kind of work:
an integrator who proves their error handling by making a live system fail.

---

## Dependencies

| Dependency | Customer | Needed by | Owner | Status |
|---|---|---|---|---|
| Sandbox token reissue | Calder & Voss | 17 Sep | Security team | ⛔ Overdue — raised 3 Sep |
| Confirmation the customer's IP range is allowed | Northwind | 24 Sep | Platform team | 🔄 In progress |
| Customer-side named escalation contact | Northwind | 30 Sep | Customer | ⬜ Requested 10 Sep |
| Authorised production test account | Northwind | 1 Oct | Service owner | ⬜ Requested 12 Sep |
| Technical scoping call booked | Halyard | 19 Sep | Me | ⬜ |

Each dependency names one owner and one date.

---

## Handover

An implementation is finished when the customer can run without me. For each:

| Handover item | Northwind | Calder | Halyard |
|---|---|---|---|
| Endpoint list, example request and response | ✅ | ✅ | ⬜ |
| Error-code table, and what `request_id` is for | ✅ | ⬜ | ⬜ |
| Troubleshooting guide shared | ✅ | ⬜ | ⬜ |
| Escalation contacts exchanged both ways | 🔄 | ⬜ | ⬜ |
| Go-live checklist signed by both sides | 🔄 | ⬜ | ⬜ |
| Post-go-live check-in booked | ⬜ | ⬜ | ⬜ |
| Moved to business-as-usual support | ⬜ | ⬜ | ⬜ |

The check-in is booked *before* go-live, not after. Booking it afterwards
means it competes with whatever has gone wrong in the meantime.

---

## This week

1. Chase the Calder & Voss token reissue; if it is not resolved by Wed, tell
   the customer the 25 Sep date is at risk rather than letting them find out.
2. Get Northwind's production test account approved — it is on the critical
   path for 2 Oct and has been open six days.
3. Book the Halyard scoping call so the 13 Nov date stops being provisional.
