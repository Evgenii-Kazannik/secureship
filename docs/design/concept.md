# SecureShip concept

## Problem statement

If the chat can query the database before it knows who is asking, any user can
receive other users shipment details if they know the user's tracking number.
The database processes the query without knowing whether it was a legit user asking or a stranger.
A system prompt instruction is not a gate — it can be overridden by a rephrased question
or ignored entirely. The access control must live in the code that runs the query,
not in the text sent to the model.

## Business value

Customers get a 24/7 channel to check their own shipments without calling support.
Customer service teams stop handling routine calls and focus on
exceptions that actually need a person. For SecureShip the outcome is lower support
cost and faster resolution time for the cases that do escalate.

## Target users

**Anonymous visitor** — can open the chat and ask questions about shipping policy,
delivery times, or carrier information. Cannot see any shipment data. The assistant
will not confirm whether a tracking number exists or whether a name is in the system.

**Verified customer** — has passed the identity check and the 2FA code. Can ask about
their own shipments, packages, and delivery status. Cannot see another customer's data,
even if they supply a valid tracking number that belongs to someone else.

**Admin** — authenticated via Auth0 (Week 4). Can create, edit, and delete customers,
shipments, and packages through a separate admin panel. Cannot access another customer's
chat transcript through the admin routes.

## Success criteria

These are the checks to show a mentor.

1. Unverified visitor asks "Where is MX10001?" — assistant refuses and does not reveal
   whether that tracking number exists.
2. Unverified visitor asks "Where is Avery Chen's package?" — same refusal. The name
   is not confirmed or denied.
3. Visitor goes through the full identity flow as Avery Chen and enters the correct code
   — session becomes verified.
4. Verified Avery asks "Where is my package?" — assistant returns MX10001 data.
5. Verified Avery asks about MX10002 (Jordan's tracking number) — assistant returns
   nothing, because MX10002 is not linked to Avery's customer ID.
6. Jordan's exception shipment (address mismatch) + a policy question asked together —
   reply includes both the shipment status and a cited policy chunk in one response.
7. Either state: "I want to talk to a human" plays the scripted handoff sequence with
   at least three visible steps and marks the session as escalated.

## Data rules

All customer names, addresses, phone numbers, shipments, and packages in this project
are synthetic. They were generated for the workshop and do not represent real people.

Before verification, the assistant may answer public policy questions. It may not say
whether a tracking number exists, whether a name matches a customer record, or give any
status for any shipment.

Real client data — production tracking numbers, real customer names, real addresses or
phone numbers from an actual shipping system — must never be pasted into a prompt, a
log entry, a test fixture, or a demo scenario.
