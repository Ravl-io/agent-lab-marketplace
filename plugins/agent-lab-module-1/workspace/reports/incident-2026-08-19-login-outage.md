# 2026-08-19 login outage raw notes (on-call: Priya S.)

the bad one. full login outage for web + mobile.

- 14:03 ET alerts + support flood. all logins failing with 500s. existing sessions fine.
- 14:07 identified: token-signing cert expired 14:00 exactly. the auto-renewal job has
  been failing since JULY 30 — its failure notifications were going to a slack channel
  that got archived in the reorg. three weeks of failure alerts into the void.
- 14:15 manual cert renewal started. renewal itself fast but propagation to all 6 auth
  pods needed a rolling restart
- 14:31 web logins recovering
- 14:38 mobile fully recovered. calling it 35 min total.

impact: nobody could START a session for ~35 min. sessions already active unaffected.
support: 210+ tickets, social media noticed (a few posts, nothing viral). SEV1, no debate.

what needs to change:
- cert expiry monitoring independent of the renewal job — check the cert itself, alert at
  14 days (Priya, started already)
- alert routing audit: what ELSE is notifying archived/dead channels?? (Dana to own, this
  scares me more than the cert)
- runbook for cert rotation was out of date, cost us maybe 5-8 min (Marcus)
- postmortem scheduled thursday
