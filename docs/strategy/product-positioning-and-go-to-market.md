# Product Positioning And Go-To-Market

## Document metadata

- **Purpose:** Product positioning, audience, competitive posture, onboarding, pricing hypotheses, and market-validation assumptions.
- **Authority:** Strategy document. It may guide roadmap priorities, UX language, and public-beta gates, but it is not a release commitment or code rename.
- **Status:** Planning assumptions — validate with users before irreversible branding, pricing, or launch decisions.
- **Research date:** 2026-07-18.
- **Source inputs:** Local marketing documents in `~/Repositories/mealroulette_marketing`: `PLACALMA_MARKETING.md`, `placalma-strategy-addendum.md`, and `placalma-competitor-benchmark.md`.
- **Update when:** Public positioning changes, public beta starts, pricing is tested, competitor assumptions are refreshed, or a brand rename becomes implementation work.

---

## Brand Boundary

The repository and current application remain **MealRoulette** until a separate implementation phase explicitly renames product surfaces, domains, assets, and user-facing copy.

The current strategy direction is to evaluate **PlaCalma** as the public brand:

```text
PlaCalma
Balanced meals. Less to manage.
```

Treat **Meal Roulette** as a historical/internal concept in future public messaging. The word "roulette" suggests randomness, while the product is increasingly about coordinated planning, leftovers, shopping, and household adaptation.

Do not perform a partial rename casually. A real rename should cover:

- product copy;
- navigation and action labels;
- logo and app icon assets;
- public URLs/domains;
- docs and release notes where appropriate;
- migration messaging for existing users;
- search, install, and app-store metadata if those exist.

## Core Positioning

The strongest product definition is:

```text
A household food-week coordination system.
```

Public-facing wording can be simpler:

```text
A weekly meal planner that keeps meals, leftovers, and shopping connected.
```

The product should not be positioned primarily as:

- a random meal generator;
- a recipe search tool;
- a shopping-list app;
- a calorie or diet tracker;
- an AI novelty product;
- a virtual chef.

The core promise:

```text
Balanced meals. Less to manage.
```

The strategic differentiator is continuity after the plan is created:

```text
Plan created
  -> meal changes
  -> leftovers appear
  -> schedule changes
  -> shopping consequences update
  -> balance is repaired
  -> household understands what happened
```

## Audience

The first target is not everyone who eats.

Primary segment:

```text
Busy households that cook several times per week and currently coordinate
meals, leftovers, and shopping through memory, messages, notes, and disconnected tools.
```

Likely strongest subsegment:

```text
Families with children where one or two adults repeatedly carry most of the meal-planning burden.
```

Other useful segments:

- couples;
- shared households;
- waste-conscious households;
- people with their own recipe collection;
- multilingual European households;
- people who want variety without calorie tracking.

The tone should be calm, practical, and direct. Avoid guilt, exaggerated AI claims, diet-culture positioning, and childish mascot copy.

## Sui

Sui is the assistant behind the product, not the product itself.

Use Sui for:

- explaining why a plan works;
- showing what changed;
- proposing alternatives;
- connecting leftovers to future meals;
- updating the shopping list;
- reducing decisions.

Do not frame Sui as:

- a chef;
- a magical AI;
- a chatbot that constantly interrupts;
- a food taster;
- a childish mascot;
- an animal visually living in the kitchen.

Useful boundary:

```text
Sui should feel like a calm digital assistant inspired by a newt,
not an amphibian living in the kitchen.
```

Recommended action vocabulary for future UX polish:

| User intent | Preferred label |
| --- | --- |
| Create first plan | Plan my first week |
| Manually create a week | Ask Sui to plan |
| Replace one meal | Try another |
| Repair balance after edits | Rebalance week |
| Replace most unlocked meals | Replan week |
| Understand a choice | Why this meal? |
| Apply leftovers | Use leftovers |
| Preserve a meal | Lock |

Avoid future public copy based on:

- roulette;
- reroll;
- spin;
- "Sui it";
- "Suify";
- "Chef Sui".

## Competitive Posture

The competitor benchmark reviewed Mealime, Paprika Recipe Manager, Plan to Eat, Samsung Food, AnyList, and Eat This Much on 2026-07-18.

Competitor facts and prices change. Before publishing external comparison claims, refresh the benchmark with hands-on testing and legal review.

Current strategic conclusions:

- Recipe import is table stakes.
- A starter catalogue is necessary to avoid cold-start failure.
- Manual calendar planning and shopping lists are common.
- Automatic planning exists, but competitors optimize for different goals.
- Some competitors handle leftovers in some form, so do not claim uniqueness.
- Native household identity is a real opportunity.
- Public recipe publishing alone is not unique; usefulness-based adoption and verified cooking signals are more interesting.
- Canonical ingredients are valuable only when they improve planning, shopping, import quality, safety, or explanation.

Reasonable claims to aim for:

- "Plan meals, leftovers, and shopping as one connected week."
- "Change one meal without rebuilding the whole plan."
- "Give leftovers a place in the week."
- "Keep the shopping list aligned when plans change."
- "Start from meals your household already eats."
- "See why a meal fits the rest of the week."
- "One household plan, shared by everyone."

Claims to avoid:

- "No other app handles leftovers."
- "The first intelligent meal planner."
- "Competitors only choose random meals."
- "The only household meal-planning app."
- "Perfectly balanced nutrition."
- "AI understands your family."
- "Never think about meals again."
- "Automatically eliminates food waste."

## Onboarding Strategy

The biggest product risk is cold start.

A household should not need to manually create 15-30 recipes before the app becomes useful. Recognition is easier than recall.

Recommended onboarding direction:

1. Ask only high-value household basics: size, adults/children, meals to plan, allergies/exclusions, broad dietary pattern, weekday effort tolerance.
2. Show familiar meal cards and ask whether the household eats them.
3. Infer provisional preferences and ask only high-information follow-up questions.
4. Help users adopt or import 15-30 familiar dish concepts.
5. Make at least 10-15 recipes shopping-ready before a serious first plan.
6. Generate a first plan that favors familiarity over novelty.

Starter catalogue target before serious public launch:

| Type | Target |
| --- | ---: |
| Complete mains | 120-180 |
| Centerpieces | 80-120 |
| Side dishes | 80-120 |
| Desserts | 30-50 |
| Soups / light meals / simple meal forms | 40-70 |
| Total concepts | 350-500 |

The starter catalogue should remain curated. A smaller reliable catalogue is better than thousands of low-quality entries.

## Dish And Recipe Trust States

Public catalogue and onboarding should distinguish:

| State | Meaning | Can be planned? | Shopping confidence |
| --- | --- | ---: | ---: |
| Recognized dish | The household eats this concept | Limited / conditional | Low |
| Public default adopted | A complete public recipe was copied | Yes | Medium / high |
| Household-customized recipe | The household confirmed its version | Yes | High |
| Verified recipe | The household cooked or reviewed it | Yes | Highest |

Do not silently treat a recognized dish concept as an exact household recipe.

## Planning Differentiator

The product should support three distinct operations:

| Operation | Meaning |
| --- | --- |
| Try another | Replace one meal while respecting the rest of the week |
| Rebalance week | Repair the current plan after changes while preserving most meals |
| Replan week | Reconsider most unlocked meals and create a substantially different plan |

`Rebalance week` is strategically important because it expresses the core promise: real weeks change, and the system repairs the consequences.

Future acceptance criteria for rebalance should measure:

- number of user actions after a meal cancellation;
- whether locked meals remain;
- whether leftovers are assigned appropriately;
- whether shopping-list changes are correct;
- whether the user can understand why the plan changed.

## Commercial Model Hypothesis

Self-hosted core should remain free and open source.

Hosted service should be treated as a validated product, not an unlimited free utility.

Planning assumption after validation:

| Offering | Model |
| --- | --- |
| Self-hosted | Free and open source |
| Private alpha | Free and invite-only |
| Capped public beta | Free with strict limits |
| Mature hosted household plan | Paid household subscription |
| Managed AI | Included allowance plus optional credits |
| Self-hosted AI | Bring your own provider credentials |

Possible hosted pricing test after retention is proven:

| Plan | Hypothesis |
| --- | ---: |
| Trial | 30 days, no payment card before value is experienced |
| Household monthly | EUR 4.99/month |
| Household annual | EUR 39.99/year |
| Founding household annual | EUR 29.99/year for a limited early cohort |

The household, not the individual user, should be the billing unit.

Do not split the central workflow across tiers. If hosted billing exists, the household plan should include:

- automatic weekly planning;
- manual planning;
- leftovers;
- shopping-list synchronization;
- all household members;
- manual recipes;
- swaps, locks, alternatives, and replanning;
- household preferences;
- planning history;
- notifications;
- integrations;
- public catalogue;
- data export;
- backups;
- a modest managed-AI allowance.

Managed AI credits remain useful for variable-cost features, but they should not be the only long-term revenue model because users may import recipes once and keep consuming hosted coordination value for years.

## Key Validation Metric

The central activation-retention metric:

```text
Of households that successfully generate a first plan,
what percentage voluntarily accept or generate a fourth weekly plan?
```

Interpretation:

| Four-week activated-household retention | Meaning |
| --- | --- |
| <15% | Weak product value |
| 15-25% | Some value, major friction |
| 25-40% | Promising niche |
| 40-55% | Strong product-market signal |
| >55% | Exceptional |

Public-beta pricing and growth decisions should wait until this metric is measured with unrelated households.

## Continue / Stop Criteria

The benchmark does not make the product less worth building. It makes the ambition narrower.

Continue treating PlaCalma as a serious niche product when evidence shows that it is materially better at one specific job:

```text
Keeping a real household's week coherent when meals change,
leftovers appear, and shopping consequences move with them.
```

Do not continue commercial investment merely because the architecture is elegant or the feature set is broad.

Evidence that the product is worth continuing commercially:

1. **Fast activation:** a new household reaches a credible first plan in roughly 10-15 minutes using starter dishes and a few imports.
2. **Trust:** households keep most generated meals; an initial target is at least 70% of planned slots retained, with low rates of inappropriate combinations.
3. **Recurring use:** at least 40% of activated households are still planning in week four.
4. **Workflow reduction:** users report that the app replaces existing mental work rather than adding a system to maintain.
5. **Willingness to pay:** after four weeks, a meaningful fraction accepts a real price around EUR 30-50/year.

Evidence that commercial ambition should stop or pause:

- households need too much configuration;
- generated combinations are not trusted;
- users rarely record leftovers;
- shopping lists need frequent correction;
- manual planning remains easier;
- users stop after two or three weeks;
- support burden grows faster than retained value.

If these tests fail, the project can remain a strong personal/open-source application. The next investment should buy evidence, not just more architecture.

## Product Priorities

Highest-priority differentiators:

1. Fast household onboarding.
2. Useful starter catalogue.
3. Reliable personal recipe import.
4. Trustworthy first plan.
5. Strong adaptation after changes.
6. Leftovers integrated into future plans.
7. Shopping list that remains aligned.
8. Explainable decisions.
9. Low interaction burden.
10. Good mobile experience.

Areas to avoid competing on initially:

- recipe discovery scale;
- nutrition optimisation;
- pantry scanning;
- grocery delivery integrations;
- social feeds;
- creator monetisation;
- global cuisine coverage;
- AI spectacle.

Main risks:

- overcomplicated onboarding;
- too much taxonomy exposed to users;
- unreliable shopping aggregation;
- catalogue too small or culturally narrow;
- technically valid but unattractive meal combinations;
- public recipe duplication and quality problems;
- managed AI abuse;
- support burden;
- ingredient ontology overengineering;
- opaque recommendation logic;
- excessive mascot presence;
- offering too much free hosted value indefinitely.

## Strategy Rule

The product should win by doing something ordinary meal planners do poorly:

```text
Keeping a household's meals, leftovers, preferences, and shopping coherent
as real life changes during the week.
```

Build and prioritize features by whether they reduce household coordination work. If a feature adds data entry, taxonomy exposure, or moderation burden without making the next weekly decision easier, defer it.
