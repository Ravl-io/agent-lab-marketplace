# Configuring SSO

Last reviewed: 2026-07-30. Applies to platform 5.2 and later.

## How login routing works

When a user enters their email address, the platform takes the domain part and looks it up
in the account's list of **registered SSO domains**.

- **Domain is registered** → the user is redirected to the account's identity provider.
- **Domain is not registered** → the platform falls back to password login, and writes an
  `sso_login` event to the audit log with `error_code = DOMAIN_NOT_REGISTERED`.

This fallback is deliberate. It means a mistyped domain does not lock anybody out. It also
means that **a missing domain looks exactly like "SSO is broken for some users"** from the
customer's side, and exactly like "SSO works fine" when tested with an address on the
registered domain.

## Multiple domains

An account can register more than one domain. This is common after an acquisition, or where
a business runs separate domains for separate divisions.

Every domain must be registered explicitly. There is no wildcard, and registering
`example.com` does **not** cover `example.org`, `example-group.com`, or any other variant.

To add one: Account Settings → Authentication → SSO Domains → Add. It takes effect within
about a minute, and no user action is needed.

## What this looks like in the audit log

```
action=sso_login  result=denied  error_code=DOMAIN_NOT_REGISTERED  target=<the domain tried>
```

If you see this for some users on an account and not others, compare the domains in the
affected users' email addresses against the registered list. It is nearly always a domain
that was never added.
