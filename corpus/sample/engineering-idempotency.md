---
category: engineering
tenant: acme
sourceUri: kb/engineering/idempotency.md
---

An idempotency key collision happens when two different request bodies are sent with the same idempotency key. The service must reject the second request rather than silently returning the first request's result, because the caller likely made a bug, not a legitimate retry.

Legitimate retries reuse the same key with the same body on purpose, and the service returns the original response without reprocessing. The distinction is enforced by hashing the request body and comparing it to the hash stored alongside the key on first use.
