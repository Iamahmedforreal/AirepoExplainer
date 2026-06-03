# Webhooks — Clerk user ingestion

The backend uses Clerk for authentication, but the app still needs a local
`users` row so repositories, conversations, and messages can reference a user by
foreign key. Clerk webhooks are the bridge: when Clerk creates a user, this app
receives a signed event and inserts that user id into PostgreSQL.

## Files

- `app/router/webhookRouter.py` — HTTP endpoint: `POST /webhooks/clerk`
- `app/services/webhook.py` — persistence helpers:
  - `is_duplicate_webhook`
  - `save_webhook_event`
  - `create_new_user`
  - `mark_webhook_processed`
  - `mark_webhook_failed`
- `app/models/repo_models.py` — `User` and `WebhookEvent` tables

## Flow

```
Clerk ──signed Svix webhook──▶ POST /webhooks/clerk
                                      │
                                      ├─ verify signature
                                      ├─ dedupe by svix-id
                                      ├─ save raw payload as webhook_events row
                                      ├─ if event != user.created: mark processed + ignore
                                      └─ if user.created: insert users.id = Clerk user id
```

Step by step:

1. Clerk sends a signed webhook to `/webhooks/clerk`.
2. The route reads `CLERK_WEBHOOK_SECRET` from settings and verifies the Svix
   signature with `Webhook(...).verify(payload, headers)`.
3. The route requires the `svix-id` header. That id is used as the
   `webhook_events.id` primary key and the idempotency key.
4. If `svix-id` already exists, the event is acknowledged with
   `{ "status": "duplicate ignored" }`. Svix can retry delivery, so duplicates
   are expected and should not create duplicate users.
5. The raw event is stored immediately with status `pending`.
6. Only `user.created` is handled today:
   - other event types are marked `processed` and ignored,
   - `user.created` extracts `event["data"]["id"]` and inserts a `users` row.
7. The webhook event is marked `processed` on success or `failed` with an error
   message if processing fails.

## Idempotency and safety

- `create_new_user()` uses PostgreSQL `INSERT ... ON CONFLICT DO NOTHING` on
  `users.id`, so receiving the same user twice is safe.
- `webhook_events.id = svix-id` prevents the same webhook delivery from being
  processed twice.
- The raw payload is stored before processing so a failed webhook can be
  inspected or replayed later.

## Security notes

- Keep `CLERK_WEBHOOK_SECRET` private.
- Do not trust or process a webhook until the Svix signature has been verified.
- Do not log secrets. Logging event ids and user ids is fine; logging the secret
  is not.

## Common failures

- `500 CLERK_WEBHOOK_SECRET is not set` — missing `.env` config.
- `401 Webhook verification failed` — wrong secret, wrong endpoint config in
  Clerk, or invalid Svix headers.
- `400 Missing svix-id header` — malformed request.
- `400 Could not extract user id...` — event shape did not match the expected
  Clerk `user.created` payload.
