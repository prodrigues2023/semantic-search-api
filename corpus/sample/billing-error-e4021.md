---
category: billing
tenant: acme
sourceUri: kb/billing/error-codes.md
---

Error code E-4021 means the card issuer declined the charge for insufficient funds. This is distinct from E-4022 (expired card) and E-4030 (issuer flagged as suspected fraud).

When a customer reports E-4021, the correct next step is to ask them to confirm their available balance or try a different card. Do not escalate E-4021 to engineering; it is an issuer-side decline, not a platform bug.

E-4021 shows up in the payment gateway logs with the raw issuer response code 51, which most processors map directly to insufficient funds.
