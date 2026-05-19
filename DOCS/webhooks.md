Webhooks (Clerk) — ingestion and processing

Purpose
- The app listens for Clerk webhooks (user lifecycle events). Webhooks are verified and stored for later processing.

Where to look
- `app/router/webhookRouter.py` — HTTP POST endpoint receiving Clerk webhooks.
- `app/services/webhook.py` — helpers that:
  - check for duplicate events
  - persist raw webhook payloads to `webhook_events` table
  - mark events processed/failed

Flow summary
1. Clerk sends a signed webhook to `/webhooks/clerk`.
2. The route verifies the signature using `CLERK_WEBHOOK_SECRET`.
3. If verified, the payload is saved to the DB via `save_webhook_event`.
4. Downstream workers or endpoints can later mark the event processed or failed (`mark_webhook_processed`, `mark_webhook_failed`).

Security notes
- Keep `CLERK_WEBHOOK_SECRET` private; do not log it.
- Verify signatures before reading payloads.
