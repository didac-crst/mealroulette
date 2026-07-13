# MealRoulette MVP

## Document metadata

- **Purpose:** MVP goal and single acceptance test.
- **Authority:** Canonical for “what counts as MVP done”; product scope detail defers to [SPECS.md](../SPECS.md).
- **Status:** Living — acceptance test only; shipment status in [BACKLOG.md](BACKLOG.md).
- **Update when:** MVP acceptance criteria change.

---

## MVP goal

A self-hosted household can maintain a recipe catalog, plan lunch and dinner, generate shopping lists, receive Telegram reminders, cook from structured recipes, and recover data from backups. LLM assistance comes after the manual flow is reliable.

Full product scope: [SPECS.md](../SPECS.md).  
What is shipped and in progress: [BACKLOG.md](BACKLOG.md).

## MVP acceptance test

A user can log in from a phone, create several dishes with normalized ingredients, plan lunch and dinner for the next three days, generate a shopping list, receive or manually send the list through Telegram, cook a recipe with step timers, mark meals as eaten, rate them, and export a restorable JSON backup.

Restore: import into an **empty** database only — see [operations/restore.md](operations/restore.md).
