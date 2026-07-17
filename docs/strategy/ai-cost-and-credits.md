# AI Cost And Credits

## Document metadata

- **Purpose:** Business and operating assumptions for managed AI recipe creation, translation, credits, and cost controls.
- **Authority:** Strategy document. Technical implementation details live in [features/ai-usage-accounting.md](../features/ai-usage-accounting.md).
- **Status:** Planning assumptions — not implemented and not a pricing commitment.
- **Update when:** Before implementing billing, changing providers, opening public signup, or every 3-6 months during beta.

---

## Pricing Snapshot

**Research date:** 2026-07-17  
**Currency:** EUR unless noted  
**Purpose:** order-of-magnitude planning only  
**Refresh when:** before managed AI launch, before translation billing, before public signup, or when provider pricing changes materially.

Provider prices, hosting plans, payment fees, and model capabilities change frequently. Treat this section as a snapshot, not a contract.

## Durable Conclusions

- Text-only AI recipe creation should usually be cheap relative to hosting and support.
- Unlimited managed AI is unsafe even if normal usage is cheap.
- Bill users by understandable outcomes, such as "AI recipe credits", not tokens or tool calls.
- Enforce hard budgets per import session: model calls, tokens, tool iterations, wall-clock time, and provider cost.
- Store AI usage events and credit ledger entries from the first managed-AI implementation.
- Support bring-your-own provider credentials for self-hosted users to avoid MealRoulette carrying variable model cost.
- Keep manual recipe creation and core roulette/planning free from managed-AI billing.

## Planning Ranges

These are deliberately broad. They are useful for sizing risk, not for accounting.

| Estimate | 2026-07-17 planning value | Refresh trigger |
| --- | ---: | --- |
| Text AI recipe creation | EUR 0.002-0.15 each | Before managed AI launch |
| Translation per language | typically below EUR 0.01, premium up to about EUR 0.04 | Before translation billing |
| Early VPS hosting | EUR 10-35/month | Before public beta |
| Managed platform hosting | EUR 35-120/month | Before choosing host |
| Transactional email beta | EUR 0-20/month | Before email OTP rollout |

## Example Recipe-Creation Budget

Generous text-only workflow:

| Operation | Input tokens | Output tokens |
| --- | ---: | ---: |
| Extract recipe structure | 3,000 | 1,500 |
| Resolve / recheck ingredients | 3,000 | 750 |
| Quality validation | 3,000 | 750 |
| **Total** | **9,000** | **3,000** |

Approximate model-price classes:

| Model-price class | Example price shape | Approx. cost per recipe |
| --- | ---: | ---: |
| Very cheap | USD 0.10 / 1M input, USD 0.40 / 1M output | USD 0.002 |
| Cheap | USD 0.25 / 1M input, USD 1.50 / 1M output | USD 0.007 |
| Mid/high | USD 2 / 1M input, USD 10 / 1M output | USD 0.048 |
| Expensive | USD 5 / 1M input, USD 30 / 1M output | USD 0.135 |

Ingredient searches against MealRoulette's own PostgreSQL/API do not materially change provider cost beyond the tool-call messages included in the session.

## Example Translation Budget

One target-language recipe translation might use:

- 1,500 input tokens;
- 1,000 output tokens.

Approximate cost:

| Model-price class | Approx. cost per translation |
| --- | ---: |
| Very cheap | USD 0.0006 |
| Cheap | USD 0.0019 |
| Mid/high | USD 0.013 |
| Expensive | USD 0.038 |

Translation lifecycle and quality are more important risks than raw cost.

## Public-Beta Cost Scenarios

Small community:

```text
200 active households/month
× 5 AI recipes/month
× EUR 0.02 per recipe
= EUR 20/month
```

Larger usage:

```text
10,000 active households/month
× 5 AI recipes/month
× EUR 0.02 per recipe
= EUR 1,000/month
```

Abuse case:

```text
100,000 generated recipes
× EUR 0.02 per recipe
= EUR 2,000
```

Therefore managed AI must never be anonymous and unlimited.

## Commercial Model Hypothesis

The initial commercial model should be:

- free/open-source core application;
- manual recipe creation free;
- optional bring-your-own AI provider key for self-hosters;
- small free managed-AI trial;
- prepaid managed AI recipe-credit packs.

Potential beta offer:

| Package | Included operations | Hypothesis price |
| --- | ---: | ---: |
| Trial | 3-5 AI recipe creations | Free |
| Small | 25 AI recipe creations | EUR 3.99 |
| Household | 100 AI recipe creations | EUR 8.99 |
| Large | 500 AI recipe creations | EUR 24.99 |

These are product-price hypotheses, not prices derived directly from API cost.

Do not sell individual EUR 0.10 recipes. Payment fees and support overhead would dominate.

## Credit Semantics

One AI recipe creation credit should include:

- structured extraction;
- ingredient matching/resolution;
- validation;
- one quality review pass;
- a small number of user-requested corrections, for example two.

It should not include:

- unlimited regenerations;
- arbitrary URL scraping;
- OCR/photo import;
- recipe image generation;
- translations into many languages;
- premium reasoning loops with no budget.

Translations may be separate lower-cost translation credits or included in larger packs after usage is measured.

## Session Budget

Suggested hard ceiling per managed recipe creation:

```text
maximum model calls: 4
maximum input tokens: 20,000
maximum output tokens: 8,000
maximum tool iterations: 12
maximum wall-clock duration: 60 seconds
maximum provider cost: EUR 0.15
```

If the budget is exhausted, return the best draft and ask the user to edit manually.

## Risks That Change Cost

- image generation;
- arbitrary web recipe extraction;
- OCR or photo import;
- premium reasoning model used for every step;
- repeated invisible retries;
- very long pasted inputs;
- translation into many languages automatically;
- abuse and bot traffic;
- support, payment, hosting, email, backup, and monitoring costs.

## Decision Boundary

Pricing can change later. Accounting, budgets, and ledgers are difficult to retrofit.

Build usage measurement before managed credits. Decide prices after beta usage shows actual retention, support burden, and provider cost.
