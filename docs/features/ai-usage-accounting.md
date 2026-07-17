# AI Usage Accounting

## Document metadata

- **Purpose:** Technical design for managed AI usage measurement, budgets, and credits.
- **Authority:** Feature specification for future managed AI. Business assumptions live in [strategy/ai-cost-and-credits.md](../strategy/ai-cost-and-credits.md).
- **Status:** Accepted design — implementation not started.
- **Update when:** Billing model, provider abstraction, LLM workflow, or credit semantics changes.

---

Managed AI must be auditable and budget-limited from the first implementation.

## Goals

- Track provider usage per operation and import session.
- Support managed MealRoulette credits and bring-your-own provider credentials.
- Prevent unlimited spend from abuse, bugs, retries, or agent loops.
- Charge users by useful outcomes, not raw tool calls.

## Non-goals

- No pricing implementation in the recipe-draft foundation phase.
- No subscriptions in the initial design.
- No anonymous AI endpoints.
- No unlimited managed AI tier.

## Usage Events

```text
ai_usage_events
- id UUID
- user_id
- household_id
- recipe_import_session_id NULL
- provider
- model
- operation
    recipe_extraction
    ingredient_resolution_review
    recipe_quality_review
    translation
    retry
- input_tokens
- output_tokens
- cached_input_tokens
- reasoning_tokens NULL
- tool_call_count
- provider_cost_usd NULL
- charged_credits
- success
- error_code NULL
- latency_ms
- created_at
```

Store provider cost when available. Do not depend on provider billing APIs being perfectly synchronized with application events.

## Credit Ledger

Use a ledger, not only a mutable balance.

```text
ai_credit_ledger
- id UUID
- user_id NULL
- household_id NULL
- delta
- reason
    trial_grant
    purchase
    reservation
    reservation_release
    recipe_creation_consumed
    translation_consumed
    refund
    admin_adjustment
- recipe_import_session_id NULL
- payment_reference NULL
- created_by_user_id NULL
- created_at
```

Current balance is the sum of ledger deltas.

## Credit Lifecycle

Suggested managed recipe-credit rule:

1. Reserve one recipe credit when generation starts.
2. Release it if provider failure prevents a usable draft.
3. Consume it once a structured draft is available.
4. Normal edits are free.
5. Explicit full regeneration consumes another credit.
6. Ingredient resolution retries inside the same run are included until budget is exhausted.

The user sees recipe credits. They do not see tool calls, provider tokens, or intermediate model invocations.

## Session Budgets

Every managed AI session must have explicit limits.

Suggested defaults:

```text
maximum model calls: 4
maximum input tokens: 20,000
maximum output tokens: 8,000
maximum tool iterations: 12
maximum wall-clock duration: 60 seconds
maximum provider cost: EUR 0.15 equivalent
```

Budget exhaustion returns the best available draft and asks the user to edit manually.

## Provider Modes

`byo_provider_key`:

- installation owner supplies provider credentials;
- MealRoulette does not charge credits;
- usage events are still stored for observability if configured;
- self-hosted default.

`managed_credits`:

- MealRoulette supplies provider credentials;
- credits are required;
- rate limits and global spend limits apply;
- hosted/public default.

## Rate Limits

Minimum controls:

- authenticated users only;
- per-user daily generation limit;
- per-household daily generation limit;
- per-IP request limit for public deployments;
- maximum source text size;
- maximum concurrent import sessions per household;
- global monthly provider spend limit.

When the global managed-AI budget is exhausted, disable managed AI temporarily. Manual recipe entry remains available.

## Security And Privacy

- Do not include secrets in prompts.
- Do not give the model direct SQL or trusted-data CRUD.
- Do not send cross-household recipe context.
- Treat provider responses as untrusted input.
- Store raw model responses for debugging only where privacy policy and retention rules permit it.
- Redact or limit logs that may contain private recipe text.

## Acceptance Criteria

- Every managed provider call creates an `ai_usage_events` row.
- Credits are reserved, released, or consumed through ledger entries.
- A failed provider call before usable draft creation does not consume a recipe credit.
- A session cannot exceed configured token/model/tool/time/provider-cost budgets.
- BYO-key mode bypasses MealRoulette credit charging but still uses the same draft validation pipeline.
- Manual recipe creation does not require AI credits.
