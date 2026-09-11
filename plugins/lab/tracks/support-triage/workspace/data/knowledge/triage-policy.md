# L2 triage policy

Last reviewed: 2026-08-18.

Every escalated ticket resolves to exactly one of four classifications. Choose the
classification first; the resolution follows from it.

## The four classifications

### 1. Configuration

Something in the account's own setup is wrong or incomplete. The platform is behaving
correctly given how it is configured. **We can fix this, or tell the customer how.**

Signals: audit log shows the platform refusing the action with a specific configuration
error code; the account's settings do not match what the customer believes they are.

### 2. User error

The user is attempting something their plan, role or permissions do not allow, or is using
the feature in a way it was never meant to work. **Nothing is broken.**

Signals: `NOT_ENTITLED`, `FORBIDDEN` or `INVALID_INPUT` in the audit log; the feature is
absent from the account's plan in the entitlement matrix.

Say this carefully to customers. "You are not entitled to this" is true and unhelpful;
name the workaround, or route them to their account manager.

### 3. Product defect

The platform did the wrong thing given a correct configuration and an entitled user.
**This goes to the vendor.** See `escalation-policy.md`.

Signals: the action was permitted and appeared to succeed, but the result is wrong or does
not persist; no configuration or entitlement explanation survives investigation.

### 4. Need more information

You cannot responsibly classify it yet. **This is a legitimate outcome, not a failure.**

Signals: no account identified, no reproduction, no specifics about what was expected.
Do not guess. Ask for the specific missing facts, and say why each one is needed.

## The rule that matters most

**Do not classify as a product defect until configuration and entitlement are both ruled
out with evidence.** Roughly two thirds of tickets escalated to L2 as "bugs" turn out to be
one of the first two categories. A defect raised with the vendor that turns out to be
configuration costs us credibility and a week of turnaround.

## Evidence standard

Every classification cites what it rests on: the audit log rows, the account setting, the
entitlement row, or the knowledge base article. A classification without evidence is an
opinion, and the vendor will treat it as one.
