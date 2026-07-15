# UI/UX Design System

## Document metadata

- **Purpose:** Visual, interaction, responsive, accessibility, and component standards for the MealRoulette web frontend.
- **Authority:** Canonical for **look, feel, and interaction patterns**; product workflows and API semantics defer to [SPECS.md](../../SPECS.md) §14 and feature specs. Screen *behaviour* must not change without explicit product approval.
- **Status:** Living — design-system migration in progress (`ui-ux/design-system-reconciliation`).
- **Update when:** Tokens, navigation, shared components, or screen-level visual standards change.

**Source proposal:** human-reviewed `MEALROULETTE_UI_UX_SPEC.md` (July 2026), adapted to repository authority rules below.

---

## Approved decisions (human owner)

These are fixed for this migration unless explicitly revisited:

| Decision | Rule |
| --- | --- |
| Overall direction | Warm, clean, modern **consumer** meal app — not admin dashboard |
| Teal | Normal progress: primary actions, selected nav, links, focus |
| Orange | Roulette / generation / discovery actions |
| Green | Completed / success / eaten / checked |
| Red | Destructive / error |
| Layout | Mobile-first; bottom navigation on small screens; desktop sidebar direction |
| Approach | Incremental **design-system migration** — not a one-shot visual rewrite |
| Product semantics | Unchanged unless explicitly approved |
| Logo variants | Four official variants are a **design requirement**; they do **not** block the first token/shell pass |

---

## Product context

MealRoulette is a self-hosted household meal planner. Daily-use surfaces must feel like a contemporary consumer app (calm, practical, lightly playful via mascot), not an analytics or enterprise admin product.

Core workflows (unchanged in scope):

| Workflow | Route(s) today |
| --- | --- |
| Today | `/today` |
| Plan | `/plan` |
| Review | `/review` |
| Shopping | `/shopping` |
| Dishes | `/dishes`, detail/edit/recipe routes |
| Cooking | `/recipes/:recipeId/cook` |
| Admin / settings | `/settings/*`, `/ingredients/*` (admin) |

---

## Design direction

### Personality

Practical, calm, reliable, friendly, lightly playful, modern, household-oriented. The cooking-robot logo carries playfulness; surrounding UI stays restrained.

### Visual language

Combine:

- spacing discipline of a modern SaaS UI
- soft cards and generous whitespace (banking-app calm)
- image-led food presentation where useful
- brand teal, green, orange, and dark navy from the logo

### Avoid

Generic Bootstrap admin panels, dense analytics dashboards, delivery-marketplace chrome, casino/gambling styling, childish cartoon UI, unrelated templates per screen.

### Surface balance (heuristic)

On ordinary screens: ~75–85% neutral surfaces, ~10–15% teal accents, ~3–6% green, ~2–5% orange emphasis. Strong brand colour is a minority.

---

## Brand and logo

### Variants (requirement — asset work tracked separately)

| Variant | Use |
| --- | --- |
| **Full** | Login, onboarding, large brand surfaces |
| **Compact** | Desktop sidebar, compact headers |
| **App icon** | Favicon, PWA, small contexts |
| **Monochrome** | Masks, print, accessibility fallbacks |

Do not scale the full detailed logo below ~40 px. Repo assets (`/logo-header.png`, `/logo-header.webp`) are 512×512 source marks for crisp display at login and sidebar sizes.

### Minimum sizes

| Context | Target |
| --- | ---: |
| Login mobile | 144–176 px |
| Login desktop | 176–220 px |
| Sidebar compact mark | 56–64 px |
| Header compact mark | 40–64 px |

### Backgrounds

Prefer white, warm off-white, pale teal, or subtle teal/orange radial gradient behind the logo. Avoid busy photography or saturated fields behind the mark.

### Mascot usage

Allowed: login, empty states, successful generation, “all caught up” review, backup success, future LLM draft ready. Not allowed: every card, every button, destructive dialogs, decorative noise in the same viewport.

---

## Token system

Introduce tokens in `frontend/src/styles/app.css` (or split token file imported by `app.css` later). Map existing hard-coded values gradually; do not fork per-page colours.

### Colour semantics

```css
/* Core interaction rule */
/* teal   = normal progress */
/* orange = roulette / generation */
/* green  = completed / success */
/* red    = destructive / error */
```

**Initial brand palette** (validate against vector logo when available):

```css
:root {
  --brand-teal-800: #05756f;
  --brand-teal-700: #078b82;
  --brand-teal-600: #0aa095;
  --brand-teal-500: #12b9a5;
  --brand-teal-200: #bceee7;
  --brand-teal-100: #dff7f3;
  --brand-teal-50: #f1fbf9;

  --brand-green-600: #67b524;
  --brand-green-500: #75c62f;
  --brand-green-100: #edf8df;

  --brand-orange-600: #eb6810;
  --brand-orange-500: #ff7b1a;
  --brand-orange-100: #fff0e2;

  --ink-950: #032532;
  --ink-900: #062c3c;
  --ink-700: #36515c;
  --ink-500: #6d7f86;

  --surface-page: #f7faf9;
  --surface-card: #ffffff;
  --surface-muted: #f1f5f4;

  --border-subtle: #dce7e5;
  --border-strong: #b9cac7;

  --success-600: #4f9b20;
  --warning-600: #c97800;
  --danger-600: #c93f3f;
  --info-600: #257a92;
}
```

**Current drift:** `app.css` uses blue `#0f609b` for links, tabs, and primary buttons. Migration replaces these with teal tokens without changing click targets or routes.

### Typography

Font stack: **Inter** (already in use) with system fallback.

| Role | Mobile | Desktop |
| --- | ---: | ---: |
| Page title | 26–30 px | 30–36 px |
| Section title | 20–22 px | 22–24 px |
| Card title | 17–19 px | 18–20 px |
| Body | 15–16 px | 15–16 px |
| Secondary | 13–14 px | 13–14 px |

Rules: no body text below 14 px; no thin weights for critical info; no all-caps headings; labels must wrap for i18n.

### Spacing and radii

8 px-oriented scale: `4, 8, 12, 16, 24, 32, 40, 48, 64`.

Radii: `8` inputs, `12` buttons, `16` cards, `20–24` hero/dialog/login, `pill` chips and statuses.

Cards: white surface, subtle 1 px border, minimal shadow. Strong elevation only for dialogs, dropdowns, bottom sheets.

### Layout breakpoints

```css
--bp-sm: 480px;
--bp-md: 768px;
--bp-lg: 1024px;
--bp-xl: 1280px;
```

Content max widths: login form 420–480 px; edit forms 720–840 px; detail 800–960 px; planning workspace up to 1440 px.

### Motion

Restrained: 120–300 ms for sheets/dialogs; brief playful transition for roulette actions only. Respect `prefers-reduced-motion`.

### Dark mode

Out of scope until a dark-compatible logo exists. Light mode is first-class.

---

## Navigation

### Target information architecture

Primary (frequency-ordered):

1. **Today**
2. **Plan**
3. **Review**
4. **Shopping**
5. **Dishes**
6. **More** (admin: ingredients, taxonomy, scheduler, Telegram, backups, users, household settings)

### Mobile bottom navigation

- Maximum **five** primary tabs visible; spec recommends `Today | Plan | Review | Shopping | More`.
- Icon + label (not icon-only).
- Active item: teal. Inactive: muted grey.
- Optional orange dot for pending review.
- Respect `safe-area-inset-bottom`.

**Current state (`AppLayout.tsx`):** bottom bar shows six items for admins (`Today`, `Plan`, `Review`, `List`, `Dishes`, `More`). Non-admins omit `More`. Label `List` should become **Shopping**. Reconcile **Dishes** vs **More** in shell phase (product decision: keep Dishes as fifth tab and move admin-only entries under More, or collapse Dishes into More on mobile — default: **keep Dishes** for household users, use **More** only for admin/settings).

### Desktop

- **Target:** persistent left sidebar (240–272 px expanded), not top header link row.
- Structure: compact logo + product name → primary nav → separator → admin/settings → account/logout at bottom.
- Selected item: pale teal background, dark teal label (not a heavy solid block).

**Current state:** top header with horizontal `NavButtonLink` row at `≥768px`; no sidebar. `app-main` max-width 960 px.

### Page headers

Standard anatomy:

```text
Page title
Optional contextual subtitle (date, week, counts)
Primary page action
Optional secondary actions
```

Examples: `Today — Monday, 13 July`; `Review — 4 meals need review`. Do not repeat `MealRoulette` as the page H1 inside the app shell.

---

## Buttons and action hierarchy

### Sizes (shared)

| Size | Height |
| --- | ---: |
| Small | 36 px |
| Medium | 44 px |
| Large | 48–52 px |

### Variants

| Variant | Colour | Examples |
| --- | --- | --- |
| **Primary** | Teal | Sign in, Save, Cook, Confirm review |
| **Roulette** | Orange | Generate week, Reroll, Suggest another |
| **Secondary** | Neutral outline | View recipe, Cancel, Lock |
| **Ghost** | Text only | Edit, Undo, See details |
| **Destructive** | Red | Delete, restore over data |

Rules:

- One dominant primary action per section.
- Secondary card actions → overflow menu where crowded.
- Destructive actions separated from routine actions.
- Undo preferred over confirm for safe reversible actions (e.g. reroll with undo).
- Never hide essential actions behind hover-only on touch devices.

**Current state:** global `button` / `.button` / `.button-secondary` / `.button-danger` in CSS; no `Button` React primitive; roulette actions use default primary blue styling.

---

## Forms, cards, and layout

### Forms

- Field height 44–48 px; labels above inputs; errors below field.
- Group large editors (dish/recipe) into `FormSection` cards: Basic info → Planning profile → Variants → Ingredients → Steps → Seasonality → Advanced.
- Show save state: unsaved, saving, success, failure. Long mobile forms: sticky action bar.

### Cards

Standard anatomy: optional image → title → metadata → body → primary action → overflow.

| Variant | Use |
| --- | --- |
| **Comfortable** | Today, mobile, dish library |
| **Compact** | Desktop plan grid, admin lists |

Meal cards: slot label, dish name, recipe meta, status badge, primary actions (`Cook`, `Review`, `View recipe`). Scheduler reasons under **Why this meal?** — not always visible.

Dish cards: image or fallback, name, short meta, ≤3 badges, time/difficulty, whole-card click target.

### Admin / settings

May be denser but must share tokens, typography, buttons, cards, and nav chrome — not a separate dashboard theme.

---

## Status vocabulary

Use one canonical label per state. Align frontend copy with this table during migration (internal API enums unchanged).

| Meaning | User-facing label |
| --- | --- |
| Future planned slot | Planned |
| Today/past planned, not reviewed | Needs review |
| Eaten as planned | Ate as planned |
| Ate leftovers | Ate leftovers |
| Skipped | Skipped |
| `is_locked` | Locked |
| `manually_selected` | Chosen manually |
| Automatic selection | Selected by roulette |

**Current alignment:** review actions already use “Ate as planned” / “Skipped”; continue audit during screen migrations.

---

## Screen-level guidance

High-level targets per cluster. **Behaviour and API contracts stay as implemented**; this section governs layout, hierarchy, and visual polish only.

### Login

Large full logo, welcome copy, full-width Sign in on mobile, form max 420–480 px. Not an enterprise admin portal.

### Today (highest polish priority)

Order: date context → lunch → dinner → pending reviews → shopping summary. Primary actions: Cook, Review, View recipe.

### Plan

Desktop: week grid when width allows. Mobile: vertical by day, today first, sticky week selector, secondary actions in sheet. Actions: assign, reroll (orange), lock, swap, reasons, recipe — not all visible at once.

### Review

Distinct from Plan. Outcomes: Ate as planned, Ate leftovers, Skipped; rating after relevant outcome. Future meals read-only.

### Shopping

One-handed: large check targets, grouped categories, sticky progress, checked items collapse or move to completed section.

### Cooking mode

Simplified chrome: step number, large instruction, timer, Previous/Next. Hide full nav complexity. High contrast, large controls, reduced-motion support.

### Dish library / detail / edit

Image-led grid; search accessible; filters in bottom sheet on mobile. Detail: hero, variants, traits summary, Plan / View recipe. Edit: progressive disclosure; taxonomy internals not at same level as basic fields.

### Administration

Ingredients, taxonomy, scheduler, Telegram, backups, users — card or structured rows on mobile instead of forced tables.

---

## Accessibility baseline

Minimum bar (WCAG AA oriented):

- Body text contrast; status not colour-only (badge text or icon).
- Visible keyboard focus; icon buttons have accessible names.
- Dialog focus trap and restore; no disabled browser zoom.
- Touch targets ≥ 44 × 44 px; safe-area insets on mobile.
- `prefers-reduced-motion` honoured.

---

## Shared components (target library)

Create under `frontend/src/components/` (or `components/ui/`) **before** rewriting every screen. First slice (phase 1): **tokens + Button + Card + PageHeader + StatusBadge + FormSection + EmptyState**.

Full target set (phased):

```text
AppShell, DesktopSidebar, MobileBottomNav,
PageHeader, SectionHeader, Card, MealCard, DishCard, StatusBadge,
Button, IconButton, TextField, TextArea, Select, Checkbox, RadioGroup,
SegmentedControl, Tabs, DropdownMenu, BottomSheet, Dialog, Toast,
EmptyState, Skeleton, FormSection, StickyActionBar, FilterBar, SearchField
```

Feature pages must not duplicate button/card styles when a shared primitive exists.

**Current state:** `ButtonLink`, `NavButtonLink`, `HealthStatus`; most UI is CSS classes in `app.css` (~1.5k lines) with feature-specific overrides.

---

## Current gaps (summary)

| Area | Today | Target |
| --- | --- | --- |
| Colour | Blue primary `#0f609b` | Teal primary; orange roulette; green success |
| Tokens | Ad hoc CSS values | CSS custom properties |
| Desktop nav | Left sidebar with teal active links | Done (phase 2) |
| Mobile tabs | Icon + label; “Shopping”; ≤5 tabs | Done (phase 2) |
| Login logo | 72 px header asset | 144–220 px full logo when asset exists |
| Components | CSS classes | Shared React primitives |
| Page headers | Inconsistent per page | `PageHeader` pattern |
| `app.css` size | Monolithic | Tokens + primitives first; split later if needed |

---

## Migration plan

Incremental, reviewable PR slices on `ui-ux/design-system-reconciliation`. **No backend API changes.** **No test removal.** Run `cd frontend && npm test -- --run && npm run build` each slice.

### Phase 1 — Foundations

**Goal:** Tokens and first primitives without route or behaviour changes.

Deliverables:

- [x] CSS design tokens in `frontend/src/styles/tokens.css` (imported before `app.css`).
- [x] `Button` with variants: primary, roulette, secondary, ghost, destructive; sizes sm/md/lg; loading state.
- [x] `Card`, `PageHeader`, `StatusBadge`, `FormSection`, `EmptyState` (`frontend/src/components/ui/`).
- [x] Token-backed global styles in `components.css`; legacy `.button` classes mapped to primitives.
- [x] Initial adoption: login `Button`, plan **Generate week** (`roulette` variant); teal replaces blue primary in global CSS.
- [x] Unit tests for `Button` and `StatusBadge`.

**Explicitly not in phase 1:** full screen rewrites, sidebar, logo asset production.

### Phase 2 — App shell

**Goal:** Same routes; improved navigation chrome and login branding.

Deliverables:

- [x] `AppShell` with `DesktopSidebar` and `MobileBottomNav` (`frontend/src/app/`).
- [x] Mobile bottom nav: icon + label, teal active state, safe areas; **Shopping** label; five tabs for all users (Dishes retained; admin **Settings** in mobile top bar, not a sixth tab).
- [x] Desktop sidebar (256px; collapsed option deferred).
- [x] Login branding: larger logo (`BrandLogo` login variant), welcome copy, pale teal gradient background (full-logo asset still tracked).
- [x] Authenticated views no longer show “MealRoulette” as the main H1 in a top header; page titles stay on each screen.

### Phase 3 — Core daily workflows

**Goal:** Consumer polish on highest-traffic screens.

Order:

1. Today (`TodayPage`, `TodayMealCard`)
2. Plan (`PlanWeekPage`, `MealSlotCard`, roulette toolbar)
3. Review (`ReviewWeekPage`)
4. Shopping (`ShoppingPage`)
5. Cooking mode (`RecipeCookingPage` — simplified chrome)

Deliverables:

- [x] `PageHeader`, `PageLoadingState`, `EmptyState`, `StatusBadge` adopted on daily workflow pages.
- [x] Canonical status copy (`Needs review`, `Ate as planned`) in `planFormat.ts`.
- [x] Meal cards use `StatusBadge`; plan **Reroll** uses orange `Button`.
- [x] Shopping: progress header, large check rows, empty state.
- [x] Cooking mode: hides app chrome on `/recipes/:id/cook`, large controls, sticky footer.
- [x] Review attention dot on mobile nav via `useReviewAttentionCount`.
- [x] Tests updated (`55` passing).

Per screen: comfortable cards, `PageHeader`, status badges, empty/loading states, action hierarchy, tests for changed interactions.

### Phase 4 — Catalog workflows

- [x] Dish list / `DishCard` grid
- [x] Dish detail / recipe detail
- [x] Dish and recipe edit forms (`FormSection`, sticky save bar on mobile)
- [x] `catalog-workflows.css`, `FormStickyActions`
- [x] Tests updated; `npm test -- --run` and `npm run build` pass

### Phase 5 — Admin / settings

- [x] `AdminSettingsPage`, ingredients, taxonomy, scheduler, Telegram, backups, planning targets
- [x] Same tokens and components; compact density allowed; mobile card layouts for tables
- [x] `admin-workflows.css`, updated `SettingsPageShell`
- [x] Tests updated; `npm test -- --run` and `npm run build` pass

### Phase 6 — Quality (ongoing / final pass)

- [x] Keyboard navigation audit — skip link, dialog focus trap, form/control focus rings
- [x] Translation-length smoke (EN + German long-label fixtures in tests)
- [x] Accessibility pass on migrated screens — `quality.css`, `useDialogA11y`, `SkipToContent`
- [x] `useDialogA11y.test.ts`, `longLabels.test.tsx` (Phase 7 primitives), `AppShell` skip-link test
- [x] `npm run test:visual` Playwright gate @ 375 + 1440 (optional locally; recommended before Phase 7 sign-off)
- [x] `npm test -- --run` and `npm run build` pass
- Visual regression optional (not required for first merge)

---

## Definition of done (per migrated screen)

- Works at 375, 768, 1024, 1440 px without horizontal page scroll
- Uses shared `Button` / `Card` / `PageHeader` where applicable
- Semantic colours from tokens (teal / orange / green / red)
- Loading and empty states present where applicable
- Touch targets and focus states meet baseline
- Canonical status vocabulary
- `npm test -- --run` and `npm run build` pass
- No product behaviour change without approval

---

## Phase 7 — Consumer interaction refinement

Distinct from the structural migration (Phases 1–6). Goal: interaction-first, warm consumer meal app — not restyled CRUD.

### Slice status

| Slice | Scope | Status |
|-------|--------|--------|
| 0 | `Breadcrumb`, `PageShell`, `SegmentedControl`, `Switch`, `ChoiceCard`, `ResponsiveActionGroup`, nav icons (bowl + cog), `interaction-primitives.css` | Done |
| 1 | Global breadcrumbs on all routes; shopping category labels + segmented duration + pantry switch; remove `shopping-preset-active` token drift; `SettingsPageShell` refactor | Done |
| 2 | Today hero meal cards; shopping config demoted behind disclosure | Done |
| 3 | `WeekNavigator`; plan `SearchSelect` + overflow; review `ChoiceCard` outcomes; `PlanForMeal` bottom sheet | Done |
| 4 | Dish grid click-first; detail action hierarchy | Done |
| 5 | `SettingsTile` landing; admin toggles → `Switch`; scheduler `WeekdayPicker`; `NumberStepper` on admin numeric fields | Done |
| 6 | Progressive disclosure on edit forms; `FormSaveStatus` | Done |
| 7 | Screenshot QA @ 375 + 1440; German long-label pass | Done |

**Slice 7 deliverables**

- `npm run test:visual` — Playwright overflow checks + screenshots at 375px and 1440px for Today, Plan, Review, Shopping, Dishes, Settings, Ingredients (mocked API; no backend required)
- `longLabels.test.tsx` — expanded German long-label smoke for Phase 7 primitives (`Breadcrumb`, `ChoiceCard`, `SegmentedControl`, `DisclosureSection`, `FormSaveStatus`, `SettingsTile`, `PageShell`)
- Screenshots written to `frontend/e2e/test-results/` per run (review locally; not committed)

### Phase 7 acceptance (when all slices complete)

- No raw category keys in shopping UI
- Breadcrumbs on every in-app route; ad-hoc “← Back” links removed where superseded
- High-traffic workflows use segmented controls, switches, and choice cards instead of raw form controls where specified
- Mobile @ 375px: no horizontal overflow on main routes
- Screenshot sign-off at 375px and 1440px for Today, Plan, Review, Shopping, Dishes, Settings, Ingredients

---

## Phase 8 — Visual reconciliation

Screen-by-screen visual and interaction polish after Phase 7. Presentation-only; no API or stored-value changes.

### Slice status

| Slice | Scope | Status |
|-------|--------|--------|
| 1 | Page shell (Plan/Review/Shopping titles off cards), Cook overflow fix, sidebar Sign out, `WeekNavigator` v2, central `formatQuantity` | Done |
| 2 | Plan Reroll/Swap/Lock action group, `DisclosureSection` upgrade, `ReviewOutcomeSelector`, `ShoppingListItemRow`, homogeneous `WeekdayPicker` | Done |
| 3 | `MetadataList`, dish detail actions, recipe basics/inheritance, `CookingIngredientList` | Done |
| 4 | Weekly targets, scheduler timezone/week labels, Telegram reminder presets, backups task layout, ingredients editor disclosures | Done |

**Phase 8 deliverables**

- Shared formatters: `formatQuantity`, `formatQuantityWithUnit`, `timezones.ts` presets
- New UI primitives: `NavigationAction`, `MetadataList`, `ReviewOutcomeSelector`, `TimezoneSelect`
- Removed global `overflow-x: clip` masking once Cook/Today action layout was fixed
- `npm test -- --run`, `npm run build`, and `npm run test:visual:ci` pass

---

## Out of scope

- New product features (LLM, localization implementation, composable meals logic)
- Backend API or data model changes
- Dark mode until assets exist
- Native mobile app
- Perfect four-variant logo delivery in phase 1 (tracked requirement only)
- Replacing every `app.css` rule in one PR

---

## Related documents

- [SPECS.md §14](../../SPECS.md#14-frontend-specification) — product screen requirements
- [cooking-mode.md](cooking-mode.md) — cooking flow behaviour
- [localization.md](localization.md) — future i18n constraints on layout
- [docs/README.md](../README.md) — documentation map

---

## One-line brief

> Design MealRoulette as a warm, mobile-first household meal app: off-white surfaces, teal progress, orange roulette, green success, navy text, soft rounded cards, strong food imagery, prominent login logo, and the same hierarchy on mobile and desktop.
