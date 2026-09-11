# Triage note — house format

What an L2 engineer writes for every escalated ticket. Same order, every time.

**This is a worked example from a case closed in August.** Its numbers come from that case,
not from the current database — read it for the shape, not the figures.

---

## TRIAGE — CASE-4233 / Pinehurst Clinics / SSO not working for new staff

**Classification:** Configuration

**What is happening:** Six users on this account are being sent to password login instead of
the identity provider. The platform is behaving correctly — their email domain is not on the
account's registered SSO domain list, and unregistered domains fall back to password login by
design.

**Evidence**
- `sso_domains` for acc-7734 contained only `pinehurstclinics.com`
- the six affected users all had `@pinehurst-health.com` addresses
- `audit_log`: 14 × `sso_login` / `denied` / `DOMAIN_NOT_REGISTERED` over three days
- the reporting admin's own address is on the registered domain, which is why it worked when
  tested with their account

**Ruled out**
- Entitlement: acc-7734 is Growth, and this needed no multi-domain support at the time
- Product defect: no successful action with a wrong outcome anywhere in the audit log

**Resolution:** Add `pinehurst-health.com` to the account's SSO domains. Takes effect within
a minute; affected users need take no action.

**Reply to customer:** Explain that the second domain was never registered, that we have
added it, and that anyone acquiring a further domain needs it registered too. Do not describe
this as a fault on their side; the fallback behaviour is not obvious.

**Escalate to vendor:** No.

**Confidence:** High. The audit log names the exact refusal reason.

---

Notes on the format, for whoever writes the next one:

- **Classification** is one of the four in `triage-policy.md`. One word, first line.
- **Evidence** is observable rows and settings, not inference. If you cannot point at a
  database row or a document, it does not belong in Evidence.
- **Ruled out** is not optional. It is what makes a defect escalation survive the vendor's
  review, and what stops us escalating configuration problems by mistake.
- **Confidence** is High, Medium or Low, with a reason. Low confidence is a useful answer.
