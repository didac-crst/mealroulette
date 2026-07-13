# MealRoulette - Software Specification

## Document metadata

- **Purpose:** Long-term product requirements and data model overview.
- **Authority:** Canonical for product scope; feature behaviour detail in [docs/features/](docs/features/).
- **Status:** Living — update when product semantics change.
- **Update when:** New user-facing behaviour ships or data model contracts change.

## 1. Overview

MealRoulette is a self-hosted household meal planning application designed to reduce daily decision fatigue around what to eat.

The application stores dishes, recipes, ingredients, tags, ratings, seasonality, and meal history. It generates lunch and dinner plans, creates aggregated shopping lists, sends Telegram reminders, and provides a step-by-step cooking viewer.

The system is API-first, Dockerized, and intended to run on a Raspberry Pi.

## 2. Product Goals

MealRoulette should help a household answer:

- What are we eating today?
- What are we eating tomorrow?
- What are we eating this week?
- What ingredients do we need to buy?
- What can we cook that is seasonal, varied, and not repetitive?
- What recipes do we actually like?
- What should we avoid because we ate something similar recently?
- What can we cook with Thermomix?
- What can we skip, reroll, or replace when plans change?

The system should not be primarily a nutrition tracker. Its main goal is practical household meal planning.

## 3. Main Features

### 3.1 Recipe and Dish Library

The app stores dishes and recipes.

A dish represents the meal concept.

Examples:

- Salmon pasta
- Lentil soup
- Spanish tortilla
- Chicken curry
- Tomato mozzarella salad

A recipe represents a concrete preparation variant of a dish.

A dish may have multiple recipe variants:

- classic version
- Thermomix version
- quick version
- kids-friendly version
- leftovers version

Each recipe should contain structured steps, not only a free text instruction blob.

### 3.2 Meal Planning

The app should support planning meals for:

- lunch
- dinner

For each day, the user should be able to:

- see the planned meal
- view the recipe
- mark it as cooked
- skip it
- replace it with leftovers
- reroll it using "roulette again"
- lock it so that automatic regeneration does not modify it
- replace it manually with another dish

### 3.3 Automatic Scheduler

The automatic scheduler generates meal plans using a scoring system.

It should consider:

- weekly targets for food categories
- ratings
- seasonality
- last cooked date
- similarity to recent meals
- cooking time
- meal slot suitability
- locked meals
- skipped meals
- leftovers
- user preferences

The scheduler should be explainable. For each automatically selected meal, the system should store selection reasons.

Example:

```json
{
  "dish": "Lentil soup",
  "selection_reasons": [
    "matches vegetarian weekly target",
    "good winter dish",
    "not cooked in 35 days",
    "high rating"
  ]
}
```

### 3.4 Shopping List Generator

The app should generate shopping lists based on the meal plan.

The user should be able to configure the shopping window.

Examples:

- ingredients for tomorrow
- ingredients for the next 2 days
- ingredients for the next 3 days
- ingredients for the full week

The shopping list should:

- aggregate ingredients from multiple planned recipes
- group ingredients by category
- exclude pantry items if configured
- show which meals require each ingredient
- allow items to be checked off
- optionally persist generated shopping lists

### 3.5 Telegram Bot Reminder

The app should send a daily Telegram reminder with the ingredients needed for the coming days.

Example message:

```text
MealRoulette reminder
For the next 3 days you need:
Vegetables
- 4 tomatoes
- 2 onions
- 3 carrots
Protein
- 400 g chicken
- 2 cans tuna
Carbs
- 500 g pasta
- 250 g rice
Planned meals:
- Tuesday lunch: Tuna rice salad
- Tuesday dinner: Chicken curry
- Wednesday lunch: Lentil soup
```

Telegram reminder settings should include:

- enabled / disabled
- bot token
- chat ID
- daily reminder time
- shopping window in days
- include today: true / false
- include pantry items: true / false

### 3.6 Step-by-Step Cooking Viewer

The frontend should provide a cooking mode.

The user should be able to move through recipe steps one by one.

Each recipe step may contain:

- instruction
- duration
- optional timer
- temperature
- Thermomix metadata
- notes

Example UI:

```text
Step 3 / 8
Add the rice and stir for 2 minutes.
[Previous] [Start timer] [Next]
```

### 3.7 Ratings and History

The user should be able to rate dishes from 0 to 5 stars.

The app should track:

- when a dish was planned
- when a dish was actually cooked
- when a dish was skipped
- when leftovers were used
- user rating
- optional comments

Meal history is required for avoiding repetition and improving automatic planning.

### 3.8 LLM-Assisted Recipe Entry

The app may use an LLM API to help create recipe metadata.

The user can enter rough input such as:

```text
Tuna rice salad with tomato, corn, eggs and olives
```

The LLM may suggest:

- dish name
- description
- ingredients
- normalized ingredient candidates
- tags
- cooking steps
- seasonality
- difficulty
- preparation time
- cooking time
- Thermomix availability guess

LLM output must always be treated as a draft. The user must review and confirm before saving.

The LLM should not directly write trusted data into the database without user validation.

### 3.9 Access Control

The website may be exposed online, so the app must include access control.

Even though the data is not highly sensitive, the app has writable endpoints that must be protected to avoid:

- trolling
- spam
- deleted recipes
- corrupted ingredient data
- modified meal plans
- abused LLM calls
- modified Telegram settings
- broken backups or imports

The app should support:

- username/password login
- authenticated API access
- user roles
- protected write endpoints

Recommended roles:

```yaml
admin:
  - manage users
  - manage recipes
  - manage ingredients
  - manage tags
  - manage planning rules
  - manage Telegram settings
  - run import/export
  - use LLM enrichment
user:
  - view recipes
  - view plans
  - rate meals
  - mark cooked
  - skip meals
  - use leftovers
  - reroll meals
```

Optional extra protection can be provided through:

- Cloudflare Access
- Tailscale
- reverse proxy authentication
- VPN-only access

#### Future: Passkeys (WebAuthn)

After the username/password login flow and mobile UI are stable, the app may add optional passkey sign-in for iPhone and other devices.

Requirements and constraints:

- implement as an additional sign-in method, not a replacement for password login in v1
- use standard WebAuthn in the React web UI (`navigator.credentials`) so Safari on iPhone can use Face ID / Touch ID
- backend should verify challenges with a WebAuthn library and then issue the same JWT session model used today
- requires HTTPS and a stable domain name for `rpId`; raw local IP access is usually not suitable for passkeys
- self-hosted deployment should use TLS plus a real hostname, Tailscale hostname, or similar

This is a post-MVP security enhancement, not part of the initial MVP.

### 3.10 Backup, Export and Import

The app must support backup from the beginning.

Required backup features:

- full JSON export
- full JSON import
- PostgreSQL dump backup
- scheduled backups
- backup retention
- mounted backup folder in Docker
- restore procedure documentation

Backups should include:

- dishes
- recipes
- recipe steps
- ingredients
- ingredient aliases
- units
- tags
- ratings
- meal plans
- meal plan items
- planning rules
- Telegram settings, excluding secrets if desired
- app settings

## 4. Technical Stack

### 4.1 Backend

Preferred stack:

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL

### 4.2 Background Jobs

Initial recommendation:

- APScheduler

Use APScheduler for:

- Telegram daily reminders
- scheduled backups
- optional automatic meal plan generation

Avoid Celery in the first version unless distributed workers become necessary.

### 4.3 Frontend

The frontend should be responsive and usable on mobile and desktop.

Possible stacks:

- SvelteKit
- React + Vite
- Vue

Recommended simple option:

- React + Vite

or:

- SvelteKit

### 4.4 Database

Use:

- PostgreSQL

Avoid SQLite if the app is expected to support background jobs, concurrent API writes, scheduled tasks, and future integrations.

### 4.5 Deployment

The app should run with Docker Compose on a Raspberry Pi.

Required services:

- api
- worker
- frontend
- db

### 4.6 Testing

The project must include automated unit and integration tests from the first implementation phase onward.

#### Backend

- Use `pytest` as the test runner.
- Use `pytest-asyncio` for async FastAPI code.
- Use `httpx` for API integration tests against the FastAPI app.
- Use an isolated test database or transactional fixtures so tests do not mutate developer data.

Unit tests should cover:

- service-layer business logic
- ingredient normalization
- unit aggregation
- meal similarity scoring
- seasonality scoring
- scheduler constraints and scoring
- shopping-list generation
- backup/import validation

Integration tests should cover:

- API route behavior for endpoints added in each phase
- authentication and role enforcement on write endpoints
- database persistence for critical flows
- worker job entry points where practical

#### Frontend

- Use `Vitest` and React Testing Library for component and feature tests.
- Add smoke tests for authenticated navigation and critical forms.
- End-to-end browser tests are optional in MVP, but API integration tests are required.

#### Quality Gates

Tests must run automatically in these situations:

- on every commit through a pre-commit hook
- on every push through CI
- before merging feature work into the main branch
- manually during development through documented commands

The pre-commit hook should run the fast test subset by default:

- backend unit tests
- backend API integration tests
- frontend unit/smoke tests

CI may additionally run slower checks such as Docker Compose smoke tests and migration verification.

A phase is not complete until the tests for that phase pass locally and in CI.

## 5. High-Level Architecture

```text
Browser / Mobile Browser
        |
        v
Responsive Web UI
        |
        v
FastAPI Backend
        |
        v
PostgreSQL Database
        |
        +--> APScheduler Worker
        |
        +--> Telegram Bot API
        |
        +--> Optional LLM Provider
```

## 6. Docker Compose Structure

Example service layout:

```yaml
services:
  api:
    build: ./backend
    container_name: mealroulette-api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+psycopg://mealroulette:mealroulette@db:5432/mealroulette
    depends_on:
      - db
    volumes:
      - ./backups:/backups
  worker:
    build: ./backend
    container_name: mealroulette-worker
    command: python -m mealroulette.worker
    environment:
      DATABASE_URL: postgresql+psycopg://mealroulette:mealroulette@db:5432/mealroulette
    depends_on:
      - db
    volumes:
      - ./backups:/backups
  frontend:
    build: ./frontend
    container_name: mealroulette-ui
    ports:
      - "3000:3000"
    depends_on:
      - api
  db:
    image: postgres:16
    container_name: mealroulette-db
    environment:
      POSTGRES_USER: mealroulette
      POSTGRES_PASSWORD: mealroulette
      POSTGRES_DB: mealroulette
    volumes:
      - mealroulette-postgres-data:/var/lib/postgresql/data
volumes:
  mealroulette-postgres-data:
```

## 7. Data Model

### 7.0 Catalog implementation (v0.1)

This subsection describes what is **implemented today**. Later sections may describe planned behaviour for scheduling and future versions.

**Dish vs recipe**

| Layer | Owns |
| --- | --- |
| **Dish** | Meal concept: name, description, optional `image_url`, course (`starter` \| `main` \| `dessert`), status, food-profile tags, planning flags, seasonality, notes |
| **Recipe** | Preparation variant: variant name, servings, `recipe_type`, difficulty, prep/cook times, ingredients, steps, source URL, notes |

**Computed dish fields (API read, not edited on dish)**

- `default_prep_time_minutes`, `default_cook_time_minutes`, `default_difficulty` — from the **main** recipe (`is_main`; first recipe by default).
- `thermomix_possible` — `true` if any recipe has `recipe_type = thermomix`.

**Seasonality (UI and API write)**

- `seasonality_mode`: `all_year` or `seasonal`
- `preferred_months`: month numbers when mode is `seasonal`
- Legacy DB columns (`allowed_months`, `excluded_months`, `seasonality_strength`) exist but are cleared on save and not shown in the UI.

**Tags (seeded)**

See `backend/mealroulette/data/reference/tags.yaml` — families: `protein`, `carb`, `style`, `temperature`. No cuisine or dietary tags on dishes in v0.1 (dietary inference from ingredients is planned).

**Frontend (v0.1)**

- Login, dish card library, dish detail, dish edit, recipe view/edit with ingredients and steps.
- Not yet: dish search/filters, meal planning screens, shopping list, cooking mode, Telegram.

### 7.1 Users

Stores application users.

Fields:

- id
- username
- email
- password_hash
- role
- active
- created_at
- updated_at

Roles:

- admin
- user

### 7.2 Dishes

A dish is the abstract meal.

Examples:

- Salmon pasta
- Chicken curry
- Lentil soup

Fields (v0.1):

- id
- name
- description
- image_url (optional; card/detail show emoji placeholder by course if unset)
- course (`starter`, `main`, `dessert`)
- status (`draft`, `active`, `archived`)
- suitable_for_lunch, suitable_for_dinner, weekday_friendly, leftovers_possible, freezer_friendly, kids_friendly (nullable booleans)
- notes
- tag_ids (via dish_tags)
- meal_composition (`complete_meal`, `half`, `dessert`, `side`, …) — planner slot role; see [docs/features/meal-composition.md](docs/features/meal-composition.md)
- simple_dish_part (optional label when `meal_composition` is `half`)
- seasonality (optional; see §7.12)
- created_at, updated_at

Computed on read (from recipes):

- default_prep_time_minutes, default_cook_time_minutes, default_difficulty (main recipe)
- thermomix_possible (any thermomix recipe)

Legacy columns remain in the database but are not used in v0.1 UI/API writes: `default_servings`, `vegetable_level`, `dominant_protein`, `dominant_carb`, `serving_temperature`, stored default time/difficulty columns.

### 7.3 Recipes

A recipe is a concrete preparation variant of a dish.

Fields (v0.1):

- id
- dish_id
- variant_name
- description
- recipe_type (`standard`, `thermomix`, `other_appliance`)
- is_main (boolean; one per dish; first recipe defaults to main)
- is_thermomix (derived from recipe_type)
- source_url
- servings
- prep_time_minutes
- cook_time_minutes
- difficulty (`easy`, `medium`, `hard`)
- notes
- created_at
- updated_at

Examples:

```text
Dish: Spanish tortilla
Recipes:
  - Classic pan version
  - Thermomix version
```

### 7.4 Recipe Steps

Recipe instructions should be structured.

Fields:

- id
- recipe_id
- step_number
- instruction
- duration_seconds
- temperature
- timer_seconds
- is_thermomix_step
- metadata_json
- created_at
- updated_at

Example metadata_json for Thermomix:

```json
{
  "thermomix": {
    "temperature": "100°C",
    "speed": "2",
    "reverse_blade": true,
    "duration": "8 min"
  }
}
```

### 7.5 Ingredients

Ingredients must be normalized.

Fields:

- id
- canonical_name
- display_name
- category
- default_unit_id
- default_dimension
- pantry_item
- season_start_month
- season_end_month
- family_id (FK to `ingredient_families`; preferred taxonomy link)
- family (legacy string rollup key; dual-read during migration — see ADR 002)
- notes
- created_at
- updated_at

Food group membership is via `ingredient_families.food_group_id`, not a direct column on `ingredients`. Taxonomy tables and resolver semantics: [docs/features/taxonomy-resolver.md](docs/features/taxonomy-resolver.md).

Examples:

```text
canonical_name: tomato
display_name: Tomatoes
aliases: tomato, tomatoes, tomate, tomates, tomàquet, Tomaten
```

### 7.5.1 Taxonomy tables (v0.8+)

First-class reference tables seeded from YAML:

- `food_groups` — top-level browsing groups (e.g. vegetables, fish, dairy)
- `ingredient_families` — rollup keys for scheduler vectors and traits; FK to `food_groups`

### 7.6 Ingredient Aliases

Used to avoid duplicate ingredients.

Fields:

- id
- ingredient_id
- alias
- language
- created_at
- updated_at

Examples:

| Alias | Canonical ingredient |
| --- | --- |
| tomato | tomato |
| tomatoes | tomato |
| tomate | tomato |
| tomates | tomato |
| tomàquet | tomato |
| Tomaten | tomato |

When an unknown ingredient is added, the UI should ask whether to:

- create a new ingredient
- map it to an existing ingredient
- search existing ingredients

### 7.7 Units

Units should belong to a measurement dimension.

Supported dimensions:

- mass
- volume
- count

Fields:

- id
- name
- symbol
- dimension
- conversion_to_base
- created_at
- updated_at

Base units:

- mass: g
- volume: ml
- count: unit

Example units:

| Unit | Symbol | Dimension | Conversion to base |
| --- | --- | --- | --- |
| gram | g | mass | 1 |
| kilogram | kg | mass | 1000 |
| milliliter | ml | volume | 1 |
| liter | l | volume | 1000 |
| teaspoon | tsp | volume | 5 |
| tablespoon | tbsp | volume | 15 |
| unit | unit | count | 1 |
| clove | clove | count | 1 |
| can | can | count | 1 |
| bunch | bunch | count | 1 |

### 7.8 Ingredient-Specific Unit Conversions

Some conversions are ingredient-specific and approximate.

Examples:

- 1 onion ≈ 120 g
- 1 garlic clove ≈ 5 g
- 1 can tuna ≈ 140 g drained
- 1 egg ≈ 50 g

Fields:

- id
- ingredient_id
- from_unit_id
- to_unit_id
- factor
- confidence
- notes
- created_at
- updated_at

These conversions should be optional and clearly marked as approximate.

### 7.9 Recipe Ingredients

Links recipes to ingredients. Prefer linking ingredients to recipes, because recipe variants may have different ingredients.

Fields:

- id
- recipe_id
- ingredient_id
- quantity
- unit_id
- optional
- notes
- created_at
- updated_at

### 7.10 Tags

Use flexible tags instead of hardcoded one-hot columns.

Do not use fixed columns like:

- is_fish
- is_meat
- is_pasta
- is_potato

Use a tags table and a many-to-many relation.

Fields:

- id
- name
- family
- description
- created_at
- updated_at

Recommended tag families (v0.1 seed — see `backend/mealroulette/data/reference/tags.yaml`):

```yaml
protein:
  - none_vegetables
  - chicken
  - turkey
  - beef
  - pork
  - lamb
  - duck
  - fish
  - seafood
  - eggs
  - cheese_dairy
  - legumes
  - tofu_soy
  - mixed
  - other
carb:
  - pasta
  - rice
  - potato
  - sweet_potato
  - bread_dough_pastry
  - couscous_semolina
  - quinoa
  - noodles
  - legumes
  - other
style:
  - soup
  - stew
  - oven
  - gratin
  - curry
  - salad
  - tart_quiche
  - pasta_dish
  - rice_dish
  - bowl
  - wok
  - fried
  - dip_spread
temperature:
  - hot
  - cold
```

Planned for later (not in v0.1 seed): `dietary` (infer from recipe ingredients), `cuisine`, `effort`, `meal_slot` as tags.

### 7.11 Dish Tags

Many-to-many table.

Fields:

- dish_id
- tag_id

### 7.12 Seasonality

Seasonality should not be represented only as tags.

Use structured fields in `dish_seasonality`.

Fields (v0.1 UI and API):

- dish_id
- seasonality_mode (`all_year` or `seasonal`)
- preferred_months (used when mode is `seasonal`)

Legacy columns (`allowed_months`, `excluded_months`, `seasonality_strength`, modes `avoid` / `strict`) remain in the database for migration compatibility but are not used in v0.1.

Example all-year dish:

```json
{
  "seasonality_mode": "all_year",
  "preferred_months": []
}
```

Example summer dish:

```json
{
  "seasonality_mode": "seasonal",
  "preferred_months": [6, 7, 8, 9]
}
```

Important rule:

All-year does not mean "similar to all seasons".

All-year means seasonally neutral.

Planned scheduler behaviour (v0.5+): score by preferred months; `all_year` dishes score neutrally.

### 7.13 Ratings

Fields:

- id
- dish_id
- user_id
- rating
- comment
- created_at
- updated_at

Rating scale:

- 0 to 5

Future extension:

- ratings per household member
- child-specific ratings
- average household rating
- weighted personal preferences

### 7.14 Meal Plans

Represents a meal plan for a date range, usually a week.

Fields:

- id
- week_start_date
- status
- created_at
- updated_at

Statuses:

- draft
- active
- archived

### 7.15 Meal Plan Items

Represents one meal slot.

Fields:

- id
- meal_plan_id
- date
- meal_slot
- dish_id
- recipe_id
- status
- is_locked
- manually_selected
- skip_reason
- skip_comment
- leftover_source_item_id (optional; null = unknown / same dish)
  - Valid sources: prior meals with status `eaten` only (not `ate_leftovers`), within the last 7 days relative to the current meal date, same day or earlier. `ate_leftovers` meals do not become new sources. Full leftover inventory is deferred.
- selection_reasons_json
- created_at
- updated_at

Meal slots:

- lunch
- dinner

Statuses:

- planned
- eaten
- skipped
- ate_leftovers

Actions:

- mark eaten (ate as planned)
- skip
- ate leftovers
- roulette again
- lock
- unlock
- replace manually

### 7.16 Planning Rules

Stores scheduler configuration.

Fields:

- id
- name
- active
- rules_json
- created_at
- updated_at

Example:

```json
{
  "weekly_targets": {
    "fish": { "min": 1, "max": 2 },
    "meat": { "min": 2, "max": 4 },
    "vegetarian": { "min": 2, "max": 5 },
    "pasta": { "min": 1, "max": 3 },
    "rice": { "min": 1, "max": 3 },
    "soup": { "min": 0, "max": 3 }
  },
  "avoid_same_dish_within_days": 21,
  "avoid_similar_meals_within_days": 2,
  "similarity_threshold": 0.75,
  "prefer_seasonal": true,
  "prefer_high_rated": true,
  "max_cooking_time_weekday_dinner": 45,
  "allow_leftovers": true
}
```

### 7.17 Shopping Lists

Shopping lists can be generated dynamically or persisted.

Fields:

- id
- from_date
- to_date
- status
- created_at
- updated_at

Statuses:

- draft
- active
- completed
- archived

### 7.18 Shopping List Items

Fields:

- id
- shopping_list_id
- ingredient_id
- display_name
- quantity
- unit_id
- category
- checked
- source_meal_plan_item_ids_json
- created_at
- updated_at

### 7.19 Telegram Settings

Fields:

- id
- enabled
- bot_token_encrypted
- chat_id
- daily_reminder_time
- shopping_window_days
- include_today
- include_pantry_items
- group_by_category
- created_at
- updated_at

Secrets should not be exposed through normal API responses.

### 7.20 Backup Runs

Fields:

- id
- backup_type
- status
- file_path
- started_at
- finished_at
- error_message
- created_at

Backup types:

- json_export
- pg_dump

## 8. Ingredient Normalization Logic

Ingredient normalization is mandatory.

Without it, the database will degrade quickly.

Bad data examples:

- tomato
- tomatoes
- Tomaten
- tomate
- tomates
- tomàquet

All should map to one canonical ingredient where appropriate.

Recipe ingredient insertion flow:

1. User or LLM proposes ingredient name.
2. Backend searches ingredient aliases.
3. If exact alias match exists, use mapped canonical ingredient.
4. If no exact match exists, search similar canonical ingredients.
5. UI asks user to confirm: create new ingredient, map to existing ingredient, or add as alias.
6. Save only after confirmation.

## 9. Unit Aggregation Logic

Quantities should only be aggregated when compatible.

Example compatible aggregation:

```text
500 g pasta + 0.5 kg pasta = 1000 g pasta
```

Example incompatible aggregation:

```text
2 onions + 200 g onion
```

Should display as:

```text
Onion
- 2 units
- 200 g
```

Unless ingredient-specific conversion is configured.

Principle:

Do not invent fake precision.

## 10. Meal Similarity Logic

Meal similarity should be explainable and rule-based in the first version.

Do not use embeddings for the core scheduler in v1.

Similarity should be based on:

- shared protein tags
- shared carb tags
- shared style tags
- ingredient overlap
- seasonality similarity as a small component

Example formula (v0.5+ scheduler; cuisine removed — not used in v0.1 tags):

```text
similarity =
  0.40 * protein_similarity
+ 0.30 * carb_similarity
+ 0.20 * style_similarity
+ 0.05 * ingredient_similarity
+ 0.05 * seasonality_similarity
```

Seasonality should have low weight because two summer dishes are not necessarily similar.

### 10.1 Seasonality Similarity

Use Jaccard similarity on preferred_months, but treat all-year dishes as neutral.

Formula:

```python
def seasonality_similarity(a, b):
    if a.mode == "all_year" or b.mode == "all_year":
        return 0.0
    a_months = set(a.preferred_months)
    b_months = set(b.preferred_months)
    if not a_months or not b_months:
        return 0.0
    return len(a_months & b_months) / len(a_months | b_months)
```

Examples:

- summer vs summer/autumn = medium similarity
- summer vs winter = zero similarity
- all-year vs summer = neutral, not similar
- all-year vs all-year = neutral, not similar

## 11. Seasonality Planning Logic

For a target month, the scheduler should score dishes based on seasonality (planned v0.5+).

Example scoring (v0.1 seasonality model):

```text
if seasonality_mode == all_year:
    add small neutral score
elif month in preferred_months:
    add strong positive score
else:
    add small penalty or neutral score
```

Example July scores:

| Dish | Seasonality | July score |
| --- | --- | --- |
| Gazpacho | seasonal (summer months) | high |
| Pasta salad | seasonal (summer/autumn) | good |
| Carbonara | all_year | neutral |
| Lentil soup | seasonal (winter months) | low |

## 12. Scheduler Design

### 12.1 Scheduler Inputs

The scheduler receives:

- date range
- meal slots
- available dishes
- recipes
- tags
- ratings
- meal history
- seasonality
- planning rules
- locked meals
- skipped meals
- leftovers

### 12.2 Scheduler Output

The scheduler returns:

- meal plan items
- selected dishes
- selected recipes
- selection reasons
- plan score
- validation warnings

### 12.3 Hard Constraints

Hard constraints must not be violated.

Examples:

- do not modify locked meals
- do not use inactive dishes
- do not repeat same dish within configured days
- do not use lunch-only dish for dinner
- do not use excluded month dish if seasonality is strict
- do not exceed strict weekly maximums

### 12.4 Soft Constraints

Soft constraints guide scoring but may be violated if necessary.

Examples:

- prefer seasonal dishes
- prefer highly rated dishes
- prefer recipes not cooked recently
- prefer meeting weekly fish target
- avoid similar meals close together
- avoid heavy meals for weekday dinners
- prefer quick meals on weekdays

### 12.5 Suggested v1 Algorithm

1. Load target week.
2. Keep locked meal plan items unchanged.
3. Identify empty or regenerable meal slots.
4. For each candidate plan attempt:
   - fill each empty slot
   - filter dishes using hard constraints
   - score candidates using soft constraints
   - select using weighted randomness among top candidates
   - validate weekly targets
   - compute total plan score
5. Repeat N times.
6. Keep the best-scoring plan.
7. Store selection reasons.

Recommended first implementation:

Generate 50 candidate plans.

Keep the best one.

This is good enough for v1 and remains easy to debug.

### 12.6 Reroll Logic

The user can reroll one meal with "roulette again".

Reroll should:

1. Keep the same date and meal slot.
2. Exclude the current dish.
3. Respect locked status unless explicitly overridden.
4. Prefer dishes that improve the weekly plan.
5. Avoid highly similar alternatives if possible.
6. Replace only the selected meal.
7. Store new selection reasons.

## 13. API Specification

### 13.1 Authentication

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/refresh`
- `GET /api/auth/me`

### 13.2 Users

Admin-only endpoints:

- `GET /api/users`
- `POST /api/users`
- `GET /api/users/{user_id}`
- `PUT /api/users/{user_id}`
- `DELETE /api/users/{user_id}`

### 13.3 Dishes

- `GET /api/dishes`
- `POST /api/dishes`
- `GET /api/dishes/{dish_id}`
- `PUT /api/dishes/{dish_id}`
- `DELETE /api/dishes/{dish_id}`

### 13.4 Recipes

- `GET /api/dishes/{dish_id}/recipes`
- `POST /api/dishes/{dish_id}/recipes`
- `GET /api/recipes/{recipe_id}`
- `PUT /api/recipes/{recipe_id}`
- `DELETE /api/recipes/{recipe_id}`

### 13.5 Recipe Steps

- `GET /api/recipes/{recipe_id}/steps`
- `POST /api/recipes/{recipe_id}/steps`
- `PUT /api/recipe-steps/{step_id}`
- `DELETE /api/recipe-steps/{step_id}`

### 13.6 Ingredients

- `GET /api/ingredients`
- `POST /api/ingredients`
- `GET /api/ingredients/{ingredient_id}`
- `PUT /api/ingredients/{ingredient_id}`
- `DELETE /api/ingredients/{ingredient_id}`

### 13.7 Ingredient Aliases

- `GET /api/ingredients/{ingredient_id}/aliases`
- `POST /api/ingredients/{ingredient_id}/aliases`
- `DELETE /api/ingredient-aliases/{alias_id}`

### 13.8 Tags

- `GET /api/tags`
- `POST /api/tags`
- `GET /api/tags/{tag_id}`
- `PUT /api/tags/{tag_id}`
- `DELETE /api/tags/{tag_id}`

### 13.9 Ratings

- `POST /api/meal-plan-items/{item_id}/reset-status`
- `POST /api/meal-plan-items/{item_id}/rating`
- `GET /api/meal-plan-items/{item_id}/rating`

### 13.10 Meal Plans

- `GET /api/meal-plans/current`
- `GET /api/meal-plans/{week_start}`
- `POST /api/meal-plans`
- `POST /api/meal-plans/generate`
- `POST /api/meal-plans/{meal_plan_id}/regenerate`

### 13.11 Meal Plan Items

- `PUT /api/meal-plan-items/{item_id}`
- `POST /api/meal-plan-items/{item_id}/mark-eaten`
- `POST /api/meal-plan-items/{item_id}/skip`
- `POST /api/meal-plan-items/{item_id}/ate-leftovers`
- `POST /api/meal-plan-items/{item_id}/reroll`
- `POST /api/meal-plan-items/{item_id}/lock`
- `POST /api/meal-plan-items/{item_id}/unlock`

### 13.12 Shopping List

- `GET /api/shopping-list?from=YYYY-MM-DD&days=3`
- `POST /api/shopping-lists`
- `GET /api/shopping-lists/{shopping_list_id}`
- `PUT /api/shopping-list-items/{item_id}`
- `POST /api/shopping-lists/{shopping_list_id}/send-telegram`

### 13.13 Telegram

- `GET /api/telegram/settings`
- `PUT /api/telegram/settings`
- `POST /api/telegram/test`
- `POST /api/telegram/send-daily-reminder`

### 13.14 Planning Rules

- `GET /api/planning-rules`
- `PUT /api/planning-rules/{rule_id}`

### 13.15 Import / Export / Backup

- `GET /api/export/full`
- `POST /api/import/full`
- `POST /api/backups/run`
- `GET /api/backups`

### 13.16 LLM Assistant

- `POST /api/llm/enrich-dish`
- `POST /api/llm/suggest-tags`
- `POST /api/llm/suggest-ingredients`
- `POST /api/llm/normalize-ingredients`

All LLM endpoints must require authentication.

## 14. Frontend Specification

### 14.1 General Requirements

The frontend must be:

- mobile-first
- responsive
- fast
- simple
- usable on desktop and mobile
- protected behind login

### 14.2 Main Screens

#### Login

User enters:

- username/email
- password

#### Home / Today View

Shows:

- Today
- Lunch: planned dish
- Dinner: planned dish
- Tomorrow
- Lunch: planned dish
- Dinner: planned dish

Actions:

- view recipe
- mark cooked
- skip
- leftovers
- roulette again
- lock
- rate

#### Weekly Plan View

Calendar-style view.

Example:

| Day | Lunch | Dinner |
| --- | --- | --- |
| Monday | Salmon pasta | Vegetable soup |
| Tuesday | Chicken rice | Omelette |
| Wednesday | Lentil stew | Pasta salad |
| Thursday | Fish tacos | Tomato soup |
| Friday | Pizza | Salad |
| Saturday | Paella | Leftovers |
| Sunday | Roast chicken | Soup |

Actions:

- generate week
- regenerate week
- reroll one meal
- lock meal
- unlock meal
- replace manually
- mark cooked
- skip
- use leftovers

#### Dish Library

Searchable and filterable dish list (filters — planned; v0.1 has card grid only).

**Implemented in v0.1:** card grid with optional `image_url` or course emoji, course and difficulty from main recipe, link to dish detail.

Filters (planned):

- fish
- meat
- vegetarian
- pasta
- rice
- soup
- salad
- summer
- winter
- quick
- Thermomix
- kids-friendly
- high-rated
- recently cooked
- not cooked recently

#### Dish Detail

Shows:

- dish name
- description
- image or emoji
- classification summary (course, food profile tags, planning profile, seasonality)
- recipe variants
- notes

**Implemented in v0.1.** Not yet: rating, last cooked date, start cooking.

Actions (v0.1):

- edit dish
- add recipe variant
- view/edit recipes

Actions (planned):

- rate
- start cooking

#### Add / Edit Dish

**Implemented in v0.1 (manual mode only):**

- name, description, optional image URL
- course (starter, main, dessert)
- status
- food profile tags (protein, carb, style, temperature)
- planning profile (lunch/dinner suitability, weekday-friendly, kids-friendly, leftovers, freezer-friendly)
- seasonality (all year or seasonal + preferred months)
- notes

Recipe variants are edited on separate recipe routes after the dish exists.

Two modes (full spec):

- manual mode ✅ (v0.1)
- LLM-assisted mode (v0.6+)

Manual mode (legacy spec list — preparation lives on recipes in v0.1):

- name
- description
- tags
- seasonality
- notes
- recipe variants (ingredients, steps, times on recipe editor)

LLM-assisted mode:

- rough dish description
- generate draft
- review
- confirm
- save

#### Cooking Mode

Step-by-step recipe viewer.

Features:

- previous step
- next step
- timer
- show Thermomix metadata
- show ingredients
- keep screen readable on mobile

#### Shopping List

Shows ingredients for selected period.

Controls:

- from date
- number of days
- include pantry items
- group by category
- send to Telegram
- create persistent list

Shopping list item actions:

- check
- uncheck
- edit quantity
- delete item

#### Planning Rules

Configuration UI for:

- weekly targets
- avoid repetition window
- similarity threshold
- seasonality behavior
- max cooking time
- weekday preferences
- leftover behavior

#### Settings

Admin-only.

Settings:

- Telegram
- LLM provider
- backup
- users
- access control
- general app config

## 15. Telegram Reminder Logic

Daily reminder job:

1. Read Telegram settings.
2. If disabled, stop.
3. Determine date window:
   - today or tomorrow depending on include_today
   - next X days
4. Load planned meals in window.
5. Load recipe ingredients.
6. Normalize and aggregate ingredients.
7. Exclude pantry items if configured.
8. Group by category.
9. Format message.
10. Send through Telegram Bot API.
11. Log success or failure.

## 16. Backup Logic

Scheduled backup job:

1. Create JSON export.
2. Optionally run pg_dump.
3. Store files in `/backups`.
4. Record backup_run.
5. Delete backups older than retention policy.

Backup settings:

```json
{
  "backup_enabled": true,
  "backup_time": "03:00",
  "backup_retention_days": 30,
  "backup_path": "/backups",
  "include_json_export": true,
  "include_pg_dump": true
}
```

## 17. MVP Roadmap

### v0.1 - Foundation

- FastAPI backend
- PostgreSQL
- Docker Compose
- unit and integration test harness
- pre-commit hook and CI test workflow
- users/auth
- dishes, recipes, recipe steps, ingredients, ingredient aliases, units, tags, dish tags, seasonality
- dish library UI (login, card list, dish/recipe CRUD, ingredients, steps, tags)
- Alembic migrations through `010_dish_course_simplify`

### v0.2 - Manual Planning

- weekly plan view
- manual dish assignment
- meal plan items
- lock/unlock
- mark cooked
- skip
- leftovers
- meal history
- ratings

### v0.3 - Shopping List

- generate shopping list for next X days
- aggregate compatible units
- group by category
- exclude pantry items
- basic shopping list UI

### v0.4 - Telegram Reminders

- Telegram settings
- send test message
- daily scheduled reminder
- shopping window config
- manual send now

### v0.5 - Automatic Scheduler

- weekly plan generation
- weekly category targets
- seasonality scoring
- rating scoring
- avoid recent dishes
- similarity scoring
- roulette again
- selection reasons

### v0.6 - Catalog Keys & Computed Traits

- stable public keys for dishes and recipes
- ingredient food groups
- computed recipe traits
- taxonomy resolver

### v0.7 - Cooking Mode

- Today home
- step-by-step cooking mode
- step timers
- Telegram cooking alerts

### v0.8 - Taxonomy Hardening and Backup

- first-class food group and ingredient family tables
- computed-trait weekly target matching
- meal composition metadata
- full JSON export/import
- scheduled backups
- restore procedure documentation

### v0.9 - LLM-Assisted Entry

- LLM dish enrichment
- suggest ingredients
- suggest tags
- suggest steps
- suggest seasonality
- review before save

### v1.0 - Stable Home Version

- usable mobile UI
- stable API
- backup/restore
- auth and roles
- scheduler reliable enough for real use
- Telegram reminders
- recipe cooking mode

## 18. Non-Goals for v1

Do not build these initially:

- native mobile app
- advanced nutrition tracking
- macros/calories optimization
- barcode scanning
- inventory tracking
- complex multi-household permissions
- genetic algorithms
- vector database
- embedding-based scheduler
- automatic online recipe scraping
- full pantry management

These can come later, but they should not block the first usable version.

## 19. Design Principles

### 19.1 Keep the Data Clean

Ingredient normalization is more important than AI.

A bad ingredient database will make shopping lists useless.

### 19.2 Use Tags, Not Hardcoded Columns

Avoid rigid schema like:

- is_fish
- is_meat
- is_pasta

Use flexible tags and tag families.

### 19.3 Keep the Scheduler Explainable

The scheduler must explain why it selected a dish.

Avoid black-box logic in v1.

### 19.4 Treat LLM Output as Draft

The LLM may help with data entry, but the user must confirm before saving.

### 19.5 Avoid Fake Precision

Do not force everything into grams.

Use:

- mass
- volume
- count

Only aggregate compatible units.

### 19.6 All-Year Is Neutral

Do not treat all-year meals as similar to all seasonal meals.

All-year means seasonally neutral.

## 20. One-Sentence Description

MealRoulette is a self-hosted Python meal planning app that stores normalized recipes and ingredients, generates weekly lunch and dinner plans, creates shopping lists, sends Telegram reminders, and helps users cook through step-by-step recipe views.

## 21. Technical One-Liner

MealRoulette is an API-first, Dockerized FastAPI/PostgreSQL application with a responsive frontend, APScheduler worker, Telegram reminder integration, structured recipe data, ingredient normalization, tag-based classification, and an explainable rule-based meal scheduler.
