# ADR 002 — Canonical taxonomy and computed scheduler targets before backup contract

**Status:** Accepted (July 2026)  
**Context:** Phase 11 was scoped as JSON backup/export/import. The current model mixes string taxonomy on `ingredients`, YAML-defined food groups/families, tag-based weekly targets, and computed recipe traits that are not yet authoritative for scheduling.

## Decision

Phase 11 is **taxonomy hardening first, then backup**:

1. Promote `food_groups` and `ingredient_families` to first-class database tables; migrate `ingredients` to FK-based family membership (additive migration, dual-read during transition).
2. Enforce canonical ingredient references for recipe ingredients; no silent creation of partial ingredients from free text.
3. Migrate weekly target matching (`fish`, `meat`, `pasta`, `rice`, `vegetarian`, …) from dish tags to computed traits / taxonomy, with temporary tag fallback for regression safety.
4. Keep explicit curated classifications for non-derivable concepts (e.g. `soup`) — do not infer them from ingredients.
5. Define the JSON backup format **after** the above model is stable, including taxonomy tables and referential integrity rules on import.

## Rationale

- Backup is a long-lived portable contract; exporting a transitional schema would lock in technical debt.
- Computed traits already exist (Phase 9) but scheduler still reads tags — aligning source of truth reduces drift between display, shopping, and planning.
- First-class taxonomy tables improve validation, admin UI, and import integrity checks.

## Consequences

- Phase 11 delivery order: taxonomy migrations and scheduler target migration → backup export/import implementation.
- [BACKUP_EXPORT_IMPORT.md](../BACKUP_EXPORT_IMPORT.md) must be updated as taxonomy tables land.
- Product decisions on vegetarian/vegan semantics, fish vs seafood, soup classification, and tag retirement remain **blocking** for final target rules and export shape.

## Alternatives considered

- **Backup first, migrate later:** rejected — would require export format versioning and migration of backups across taxonomy changes.
- **Drop tags immediately:** rejected — need compatibility fallback and explicit home for non-derivable classifications.

## References

- [PHASE11_HANDOFF.md](../PHASE11_HANDOFF.md)
- [ADR 001 — Ingredient taxonomy contract](001-ingredient-taxonomy-contract.md)
- [COMPUTED_TRAITS.md](../COMPUTED_TRAITS.md)
- [SCHEDULER.md](../SCHEDULER.md)
