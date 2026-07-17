# Public Catalog Contribution And Rewards

## Document metadata

- **Purpose:** Strategy for public recipe contributions, reputation, incentives, reward safety, and catalogue quality.
- **Authority:** Strategy document. Implementation details belong in a future public-catalog feature spec.
- **Status:** Planning assumptions — not implemented and not a rewards commitment.
- **Update when:** Public catalog, contribution scoring, reward credits, licensing, or moderation policy changes.

---

Public recipes can create a useful growth loop:

```text
Useful public recipes
  -> easier onboarding
  -> more households stay active
  -> more real usage data
  -> better discovery and ranking
  -> more useful contributions
```

The incentive system must reward lasting usefulness, not the act of pressing "Publish".

## Core Principle

```text
Reward verified usefulness over time, not publication itself.
```

Bad loop:

```text
Publish low-quality recipe
  -> receive credits
  -> make recipe private again
  -> repeat
```

Better loop:

```text
Contribute useful recipe
  -> recipe survives review
  -> other households adopt and use it
  -> contributor earns reputation or limited credits
  -> public catalogue improves
  -> onboarding becomes easier
```

## Publication Model

Publication creates an immutable public version or snapshot.

```text
Household recipe
  -> publish
Public recipe version 1
  -> later household edits
Household recipe changes independently
```

Recommended shape:

```text
public_recipes
- id
- originating_household_id
- originating_recipe_id
- current_version_id
- publication_status
    private
    submitted
    public_pending
    public
    deprecated
    withdrawn

public_recipe_versions
- id
- public_recipe_id
- version_number
- immutable_recipe_snapshot
- published_at
- superseded_at NULL
```

The contributor may publish a new version, but should not silently rewrite or destroy the version other households adopted.

## Adoption And Forking

When another household adopts a public recipe, copy it into that household.

```text
public_recipe_version
  -> adopt
household recipe
```

The adopted copy may then change independently.

Preserve provenance:

```text
derived_from_public_recipe_id
derived_from_version_id
```

Existing adopters may retain copied recipes even if the public recipe is later delisted, subject to the eventual legal/product contract.

## Reward Timing

Do not reward publication immediately with financially valuable credits.

Possible milestones:

| Milestone | Reward type |
| --- | --- |
| Accepted into public catalogue | Points only |
| First 3 independent household adoptions | Small points / possible pending credit |
| 10 households confirm cooking | Limited credit |
| 25 positive meal reviews | Limited credit |
| High quality after 90 days | Badge or bonus |
| Translation reviewed and adopted | Fractional credit or points |

Credits should be delayed and capped.

## Credit Safety

Recommended properties:

- credits vest after a validation period, for example 30 days;
- monthly cap per contributor household;
- monthly cap per recipe;
- global monthly contribution-credit pool;
- no reward from the contributor's own household;
- no reward for ratings without linked cooked meals;
- no casual clawback after vesting;
- clawback only for fraud, manipulation, plagiarism, policy violations, or duplicate-content farming.

Start with reputation only. Add limited credit rewards only after real contribution behavior is understood.

## Contribution Signals

Positive signals:

- independent household adoption;
- manual selection from catalogue;
- confirmed cooked/eaten outcome;
- positive meal review after eating;
- repeated use after several weeks;
- approved translation;
- accepted correction;
- accepted ingredient proposal.

Negative signals:

- adopted but never planned;
- planned then repeatedly rerolled;
- frequently edited immediately after adoption;
- marked skipped;
- poor ratings;
- ingredient-resolution problems;
- duplicate reports.

Do not reward algorithmic exposure alone. A roulette selection is not value until the household keeps it, eats it, and preferably reviews it positively.

## Scoring Dimensions

Avoid one opaque universal score. Track separate dimensions.

Popularity:

- unique adopting households;
- unique cooking households;
- repeat cooking rate.

Quality:

- Bayesian or confidence-weighted rating;
- positive review rate;
- low skip/reroll rate.

Reliability:

- complete structured steps;
- canonical ingredients;
- no blocking validation warnings;
- tested serving scaling.

Contribution:

- translations;
- corrections;
- useful variants;
- taxonomy proposals;
- moderation help.

Show badges such as:

- Popular;
- Highly rated;
- Frequently repeated;
- Well tested;
- Easy weekday recipe;
- Family favourite;
- Recently trending.

## Rating Math

Use a confidence-aware rating, not raw average.

Example Bayesian weighted rating:

```text
weighted_rating =
  (v / (v + m)) * recipe_average
  + (m / (v + m)) * global_average
```

Where:

- `v` is review count;
- `m` is confidence threshold;
- `global_average` is catalogue average.

Wilson score may be useful for positive/negative outcomes.

## Contribution Types Beyond Recipes

Reward valuable curation, not only recipe authorship.

Possible contribution categories:

- ingredient proposals;
- valid aliases;
- ambiguous alias flags;
- storage or family classification improvements;
- translation and translation review;
- recipe corrections;
- timer additions;
- serving-scaling improvements;
- compatibility and pairing feedback;
- duplicate and plagiarism reports;
- moderation help by trusted users.

Points and badges are safer than direct financial rewards for most of these.

## Gamification

Use:

- contribution points;
- badges;
- category-specific reputation;
- trusted contributor status;
- seasonal challenges;
- featured contributor lists.

Avoid:

- daily streaks;
- cash payouts;
- rewards for clicks;
- rewards for publishing volume;
- opaque creator-score leaderboards.

Example badges:

- First Contribution;
- Ten Households Fed;
- Weeknight Specialist;
- Translation Contributor;
- Taxonomy Gardener;
- Reliable Reviewer;
- Family Favourite Creator;
- Thermomix Expert.

## Licensing And Provenance

Public recipes require explicit contributor attestation:

```text
I created this recipe, have permission to share it,
or have rewritten it sufficiently based on my own cooking experience.
```

Before launch, define:

- rights granted to MealRoulette;
- whether public versions remain after account deletion;
- whether adopters retain copied versions;
- attribution;
- takedown process;
- AI-generated content policy;
- plagiarism reporting.

Do not launch a public catalogue without this.

## Fraud Resistance

Basic safeguards:

- rewards only from independent households;
- contributor household excluded;
- minimum account age;
- email verification;
- suspicious IP/device/account clustering detection;
- diminishing rewards from repeated interactions between the same households;
- delayed vesting;
- monthly caps;
- manual review for unusual patterns;
- one qualifying event per household per recipe per period.

Do not overbuild anti-fraud during alpha, but design ledgers and event logs so suspicious rewards can be investigated.

## Rollout

Phase 1 — Provenance without rewards:

- public recipe snapshots;
- adoption/forking;
- provenance;
- usage metrics;
- ratings;
- delisting;
- moderation state.

Phase 2 — Reputation:

- contribution points;
- badges;
- contributor profile;
- transparent recipe metrics;
- trusted contributor status.

Phase 3 — Small capped credit rewards:

- limited rewards for verified milestones;
- delayed vesting;
- fixed global monthly credit pool or strict caps.

Phase 4 — Optimize:

- adjust weights;
- detect fraud;
- introduce themed challenges;
- improve ranking.

## Strategic Priority

The public catalogue is valuable mainly because it reduces empty-household onboarding friction.

Starter packs such as "Catalan family basics", "French weekday meals", "Vegetarian quick meals", or "Thermomix essentials" may be more important than gamification.

Rewards should support catalogue quality; they are not the product.
