# Cooking mode (Phase 10)

**Status:** Implemented on branch `phase-10/cooking-mode`  
**Target product version:** v1.0 (first slice; no backend changes)  
**Depends on:** v0.6.0 catalog keys, recipe steps, and recipe ingredients APIs

## Goal

Add a cooking-focused recipe view: a mobile-friendly, distraction-free mode for following recipe steps while cooking.

This phase must **not** change scheduler, weekly goals, taxonomy, shopping aggregation, recipe trait computation, or Telegram behaviour.

## User flow

### Today home (primary entry)

1. After login, user lands on **`/today`** — today's lunch and dinner from the current meal plan.
2. Each planned meal card offers **Cook** (when a recipe exists) and **Review** (inline: eaten / skipped / leftovers / rating).
3. **Cook** opens `/recipes/:recipeId/cook` using the assigned recipe or the dish main recipe.
4. **View full week** links to the existing Review tab for weekly catch-up.

### Cooking mode (from Today or recipe detail)

1. User opens cooking mode from **Today**, or from recipe detail in the dish library (`/dishes/:dishId/recipes/:recipeId`).
2. User reads the current step with large type; uses **Previous** / **Next** to move through steps.
3. Steps with a **timer** show **Start timer**; once started, the countdown **keeps running** if you move to another step (shown in a **Running timers** bar). When a timer finishes, the browser plays a **gentle repeating chime** (Web Audio + vibration on supported devices) and may show a **system notification** if permission was granted when you started the timer. Tap **Dismiss** to stop the alert; the timer stays at **0:00** with **Reset** only until you reset it for another run. Starting a timer also schedules a **Telegram alert** to all subscribed chats when it finishes (worker delivers even if the browser tab is closed).
4. User can expand **Ingredients** without losing the current step context.
5. User taps **Exit** to return to the recipe detail page.

Timer state is **local to the cooking session** (lost on refresh or leaving cooking mode). **Telegram alerts** are scheduled server-side when you start a timer and fire to all **subscribed** chats (see below).

## Scope — first implementation

| In scope | Out of scope |
| --- | --- |
| Read-only step navigation | Recipe editing |
| **Today home** with Cook + Review entry | Step-level ingredient mapping |
| Full recipe ingredient list | Voice / hands-free |
| Mobile-first layout | Scheduler integration |
| Step countdown timers (`timer_seconds` on steps) | Persistent cooking sessions (DB) |
| In-browser gentle timer chime + optional system notification | Per-user Telegram targeting |
| Telegram alert when timer ends (subscribers) | Per-user / household Telegram targeting |
| Existing catalog APIs only | Scheduler integration |
| | Shopping list changes |
| | “Cooked this” / rating flow |

## UI requirements

- **Mobile-first:** readable on phone; usable on desktop.
- **Current step:** large, high-contrast instruction text.
- **Step counter:** “Step 2 of 8” (or equivalent).
- **Navigation:** Previous / Next; disabled at first / last step.
- **Timers:** countdown with Start / Pause / Reset; started timers persist across step navigation in a **Running timers** bar.
- **Ingredients:** collapsible section (default collapsed on small screens) showing the full recipe ingredient list with quantities.
- **Header:** recipe + dish title; exit control always reachable.
- **Controls:** sticky footer bar for Previous / Next on narrow viewports.
- **Tone:** utilitarian cooking UI — not marketing/landing styling.

## Data assumptions

- **Steps:** `RecipeStep` rows via `GET /api/recipes/:id/steps`, ordered by `step_number`.
- **Timers:** optional `timer_seconds` per step (set in recipe edit as minutes). If absent, `duration_seconds` is used as a fallback label only.
- **Ingredients:** `RecipeIngredient` rows via `GET /api/recipes/:id/ingredients`; display names from the ingredient catalogue.
- **No step-level ingredients** in the schema today — show the full recipe ingredient list for every step.
- **No new backend models or migrations** unless persistent sessions are explicitly approved later.

## Routes and components

| Route | Component | Notes |
| --- | --- | --- |
| `/today` | `TodayPage` | Default home; today's lunch/dinner cards |
| `/recipes/:recipeId/cook` | `RecipeCookingPage` | Protected; loads recipe → dish → steps → ingredients |
| (existing) | `RecipeDetailPage` | Adds **Cook** link |

Pure helpers in `frontend/src/features/dishes/recipeCooking.ts` (step index bounds, sorting) are unit-tested separately from the page.

## Future (deferred)

### Telegram timer alerts (implemented)

When a cooking timer is **started**, the frontend calls `POST /api/cooking-timer-alerts` with `remaining_seconds`. The worker polls every 2 seconds and broadcasts to all **Telegram subscribers** when `fire_at` is reached:

```text
MealRoulette timer

Step 1 done — Timer Test Dish (Quick test)
```

Pause / reset / dismiss / exit cooking mode cancels the pending alert. Requires `TELEGRAM_BOT_TOKEN` and at least one `/subscribe`d chat; local countdown still works without Telegram.

**Later:** link `user_id` (and household members) to subscribers for targeted delivery.

### Other deferred items

- Persistent cooking sessions and resume-after-refresh.
- Thermomix step badges and appliance-specific layout.
- Step-level ingredient highlights.
- Voice controls and hands-free mode.
- Telegram / notification deep links into cooking mode.
- Post-cook “mark eaten” or rating shortcut.

## Acceptance criteria

- [x] User can open cooking mode from **Today** or recipe detail (**Cook** button).
- [x] **Today** shows today's meals with Cook and inline Review.
- [x] Default landing route is `/today`.
- [x] Cooking mode works on mobile and desktop layouts.
- [x] User can navigate steps sequentially (Previous / Next).
- [x] Started timers keep running when navigating to another step.
- [x] Starting a timer schedules a Telegram alert for subscribers (when configured).
- [x] User can view ingredients while on a step.
- [x] User can exit back to recipe detail.
- [x] Recipe detail and edit flows unchanged.
- [x] No new backend migrations beyond cooking timer alerts (`026`).
- [x] Backend tests still pass; frontend tests and build pass.

## Validation

```bash
make test-backend
cd frontend && npm test -- --run && npm run build
```

Manual: open a recipe with steps on a phone-sized viewport; walk through all steps; confirm ingredients panel and exit link.

## References

- [CURSOR_ROADMAP.md § Phase 10](CURSOR_ROADMAP.md#phase-10---cooking-mode)
- [BACKLOG.md](BACKLOG.md)
- Frontend: `RecipeDetailPage.tsx`, `RecipeCookingPage.tsx`, `AppRouter.tsx`
- API: `fetchRecipe`, `fetchRecipeSteps`, `fetchRecipeIngredients` in `frontend/src/api/catalog.ts`
