---
category: billing
tenant: acme
sourceUri: kb/billing/retries.md
---

Declined transactions are retried automatically for up to three attempts. Each retry is spaced roughly four hours apart so the customer's card issuer has time to clear a temporary hold.

If all three attempts are declined, the payment is marked failed and the customer is notified by email with a link to update their card. Support should not manually retry a payment before the automatic window has run its course.

A payment that keeps failing across different cards usually indicates the customer's bank is blocking the merchant category code, not a problem with the checkout flow itself.
