# Email Delivery

## Document metadata

- **Purpose:** Transactional email architecture for hosted and self-hosted MealRoulette.
- **Authority:** Feature specification for future email delivery and email OTP work.
- **Status:** Accepted design — implementation not started.
- **Update when:** Email provider choice, login/recovery policy, or notification strategy changes.

---

Google Workspace or similar mailbox products are appropriate for human mailboxes such as `support@mealroulette.app`. They should not be the primary application mail system.

Application email should use a transactional provider abstraction.

## Goals

- Support email OTP, password reset, invitations, account verification, and security alerts.
- Support self-hosted generic SMTP configuration.
- Keep provider-specific code behind a small interface.
- Separate authentication mail from optional notification mail.
- Preserve deliverability and auditability.

## Non-goals

- No high-frequency email meal reminders initially.
- No provider-specific lock-in.
- No use of human mailbox credentials as the hosted application's default transactional system.

## Provider Abstraction

```text
EmailDeliveryProvider
  - Resend API adapter
  - Postmark API adapter
  - Amazon SES adapter
  - Generic SMTP adapter
  - Disabled adapter
```

HTTP APIs are preferred for hosted MealRoulette because they provide clearer delivery IDs, errors, retries, webhooks, and metadata.

SMTP remains useful for self-hosted installations.

## Configuration

```text
EMAIL_PROVIDER=resend
EMAIL_FROM_AUTH="MealRoulette <login@auth.mealroulette.app>"
EMAIL_FROM_NOTIFICATIONS="MealRoulette <notifications@mail.mealroulette.app>"
EMAIL_REPLY_TO="support@mealroulette.app"
```

Provider secrets should stay in environment variables or the deployment secret store where practical.

## Message Interface

```text
EmailMessage
- recipient
- template
- subject
- variables
- category
    authentication
    notification
- idempotency_key
```

```text
DeliveryResult
- provider
- provider_message_id NULL
- status
- failure_code NULL
```

The rest of MealRoulette should not know whether delivery uses Resend, Postmark, SES, SMTP, or another provider.

## Delivery Records

```text
email_deliveries
- id UUID
- user_id NULL
- household_id NULL
- category
    authentication
    notification
- template
- recipient_hash
- provider
- provider_message_id NULL
- status
    queued
    sent
    delivered
    bounced
    complained
    failed
- failure_code NULL
- created_at
- delivered_at NULL
```

Avoid storing full OTP email bodies. Do not log OTP codes.

## Streams

Authentication stream:

- email OTP;
- password reset;
- email verification;
- invitation links;
- security alerts.

Notification stream:

- weekly plan email;
- shopping reminders;
- scheduled meal reminders.

Authentication mail should be immediate and high priority. Notification mail should be queued, opt-in, and rate limited.

## Email OTP Policy

Recommended baseline:

```text
code lifetime: 10 minutes
single use: yes
store only hash: yes
maximum attempts: 5
minimum resend interval: 60 seconds
per-email request limit: 5/hour
per-IP request limit: yes
generic response: yes
```

Generic response:

```text
If an account exists for this address, a code has been sent.
```

Log:

- request time;
- IP and user agent where policy permits;
- send result;
- provider message ID;
- verification result;
- rate-limit result.

Do not make email OTP the only login method initially. Keep email/password login and existing Telegram OTP.

## Domain And Deliverability

Use dedicated sending subdomains:

```text
auth.mealroulette.app
mail.mealroulette.app
```

Example senders:

```text
login@auth.mealroulette.app
notifications@mail.mealroulette.app
support@mealroulette.app
```

Configure:

- SPF;
- DKIM;
- DMARC;
- custom return path where supported.

Separate subdomains protect authentication deliverability from notification complaints.

## Provider Strategy

Planning assumption for early beta:

- Resend is likely the simplest first hosted transactional provider.
- Postmark is attractive when transactional deliverability becomes operationally important.
- Amazon SES is lowest-cost at scale but adds AWS operational complexity.
- Generic SMTP remains the self-hosted fallback.

Verify provider pricing and limits before implementation.

## Acceptance Criteria

- Application code sends email through `EmailDeliveryProvider`, not direct provider calls.
- Authentication and notification categories are separated.
- Email OTP is rate-limited, single-use, hashed, and generic against account enumeration.
- Delivery events are recorded without storing secrets or OTP bodies.
- Self-hosted deployments can use generic SMTP or disable email features.
- Hosted deployment can change providers without rewriting auth/business logic.
