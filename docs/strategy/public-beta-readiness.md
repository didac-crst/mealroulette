# Public Beta Readiness

## Document metadata

- **Purpose:** Go/no-go criteria, operating limits, success metrics, and risk register for opening MealRoulette beyond private use.
- **Authority:** Strategy document. Technical implementation details remain in feature specs and operations runbooks.
- **Status:** Planning assumptions — not a launch commitment.
- **Update when:** Before private alpha, before capped public beta, after beta metrics are reviewed, or when support/operational risk changes.

---

## Current Position

MealRoulette can be developed as a multi-household product, but it should not be treated as a business or guaranteed hosted service yet.

The next product objective is:

```text
Prove that 10 unrelated households can onboard, build a usable recipe catalogue,
and still use MealRoulette four weeks later.
```

## Beta Principles

- Core planning, shopping, manual recipes, Telegram integration, and cooking mode should remain usable without managed AI.
- Public access must be capped until retention, cost, and support burden are measured.
- Every variable-cost feature must have hard technical ceilings.
- Backups and recovery matter more than horizontal scale.
- User support time is a real cost and should be measured.
- Do not promise enterprise uptime, SLAs, or unlimited free hosted usage.

## Do Not Open Public Signup Until

Minimum technical gates:

- automated database backups are enabled;
- restore has been tested from a recent backup;
- email verification/recovery or another reliable recovery path exists;
- rate limits exist for signup, login, invitations, OTP, and managed AI;
- platform admin can disable managed AI globally;
- per-user and per-household AI limits exist if managed AI is enabled;
- basic audit logs exist for auth, AI generation, and catalog mutation;
- privacy/data handling notes exist for LLM prompts and stored drafts;
- user data export path is documented;
- deletion/support policy is documented, even if manual;
- monitoring or alerts exist for downtime, disk, backup failure, and high AI spend.

Minimum product gates:

- a nontechnical household can create or import enough recipes to generate a week;
- household invitation and role flows are understandable;
- dish vs recipe vs recipe variant does not block onboarding;
- shopping list output is trusted by testers;
- at least one recovery path exists when Telegram/email is unavailable.

## Alpha And Beta Stages

### Private Alpha

Target:

- 5-10 households;
- invite-only;
- no public signup;
- manual support accepted.

Success signals:

- 8/10 households complete onboarding;
- 6/10 households create at least 15 usable recipes;
- 5/10 households generate at least two weekly plans;
- 5/10 households are still active after four weeks;
- support stays below 3 hours/week.

### Capped Public Beta

Target:

- 100-500 households maximum;
- invite codes or waiting list;
- beta/no-guarantee wording;
- hard managed-AI, image, email, and signup limits.

Success signals:

| Metric | Initial target |
| --- | ---: |
| Four-week household retention | >= 40% |
| Active households generating a plan weekly | >= 50% |
| Active households opening shopping list | >= 40% |
| Median usable recipes per active household | >= 15 |
| Support burden | <= 5 hours/week |
| Infra + managed AI cost per active household | measurable and bounded |
| Critical data-loss incidents | 0 |

## Go / No-Go Criteria

Continue development toward a broader hosted beta when:

- unrelated households return after four weeks;
- onboarding friction is clearly understood and shrinking;
- support burden is manageable;
- backups and restores are trusted;
- managed-AI spend is bounded;
- no major privacy/security concern is unresolved.

Stay private or self-hosted only when:

- most households fail to build a usable recipe catalogue;
- users do not return after initial setup;
- support burden dominates development time;
- shopping/planning output is not trusted;
- operating costs are unpredictable;
- auth/recovery/backups remain fragile.

## Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Data loss | Severe trust loss | Automated backups, restore tests, export path |
| Managed AI abuse | Unexpected bill | Credits, budgets, rate limits, global kill switch |
| Email deliverability failure | Users locked out | Password fallback, provider abstraction, monitoring |
| Signup spam | Support and cost | Invite codes, IP/account limits, email verification |
| Image storage growth | Storage cost | Upload limits, resize, object storage |
| Support overload | Project becomes unsustainable | Capped beta, self-service docs, no SLA |
| Privacy concern around LLM prompts | User trust/legal risk | Explicit data handling, retention limits, BYO-key mode |
| Provider lock-in | Migration cost | Provider abstractions for AI and email |
| Security vulnerability | Data exposure | conservative auth, dependency updates, audit logs |
| Premature scaling complexity | Slower development | Single VPS first, measure before scaling |

## Non-Decisions

The following are intentionally not decided by this strategy:

- final public pricing;
- subscription vs credits beyond initial credit preference;
- managed-hosting commitment;
- SLA or uptime guarantee;
- unlimited free hosted tier;
- public launch date;
- legal structure or company formation.

## Decision Log Template

When a beta decision is made, add a short note:

```text
Date:
Decision:
Evidence:
Risk accepted:
Review date:
```

Keep this lightweight. The goal is to remember why a launch or operating decision was made.
