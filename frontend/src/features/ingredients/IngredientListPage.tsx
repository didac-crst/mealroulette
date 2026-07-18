import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { fetchIngredients, fetchUnits, type Ingredient, type Unit } from "../../api/catalog";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { Card, EmptyState, PageShell } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";
import { formatAggregationStrategy, formatCatalogLabel } from "./aggregationStrategy";

const SEARCH_DEBOUNCE_MS = 200;

export function IngredientListPage() {
  const { accessToken, isPlatformAdmin, isHouseholdAdmin, hasHousehold } = useAuth();
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const canBrowseTaxonomy = isPlatformAdmin || isHouseholdAdmin;

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    fetchUnits(accessToken)
      .then(setUnits)
      .catch(() => setUnits([]));
  }, [accessToken]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setQuery(search.trim());
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(handle);
  }, [search]);

  const unitSymbols = useMemo(() => new Map(units.map((unit) => [unit.id, unit.symbol])), [units]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetchIngredients(accessToken, query || undefined)
      .then((data) => {
        if (!cancelled) {
          setIngredients(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load ingredients");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, query]);

  return (
    <div className="admin-page">
      <PageShell
        title="Ingredients"
        subtitle={
          isPlatformAdmin
            ? "Canonical ingredient catalog with aliases, conversions, and proposal review."
            : "Browse available ingredients and propose missing catalog entries."
        }
        loading={loading && ingredients.length === 0}
        loadingMessage="Loading ingredients…"
        actions={
          <div className="catalog-detail-actions">
            {hasHousehold ? (
              <ButtonLink to="/ingredients/proposals" variant="secondary">
                Ingredient proposals
              </ButtonLink>
            ) : null}
            {canBrowseTaxonomy ? (
              <ButtonLink to="/ingredients/taxonomy" variant="secondary">
                Taxonomy
              </ButtonLink>
            ) : null}
            {isPlatformAdmin ? (
              <>
                <ButtonLink to="/ingredients/proposal-review" variant="secondary">
                  Proposal review
                </ButtonLink>
                <ButtonLink to="/ingredients/new">Add ingredient</ButtonLink>
              </>
            ) : null}
          </div>
        }
      >
        <Card density="comfortable" className="catalog-search-card">
          <label className="catalog-search-label">
            Search ingredients
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Name, category, or alias match"
              autoComplete="off"
            />
          </label>
          <p className="muted catalog-search-meta">
            {query
              ? `Showing ${ingredients.length} match${ingredients.length === 1 ? "" : "es"}`
              : `${ingredients.length} ingredient${ingredients.length === 1 ? "" : "s"}`}
          </p>
        </Card>

        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : null}

        {!loading && !error && ingredients.length === 0 ? (
          <EmptyState
            title="No ingredients found"
            description={
              query
                ? "Try a different search."
                : isPlatformAdmin
                  ? "Add your first ingredient to build the catalog."
                  : "No ingredients are available yet."
            }
            action={!query && isPlatformAdmin ? <ButtonLink to="/ingredients/new">Add ingredient</ButtonLink> : undefined}
          />
        ) : null}

        {!error && ingredients.length > 0 ? (
          <div className="ingredient-catalog-table">
            <div className="ingredient-catalog-header">
              <span>Name</span>
              <span>Category</span>
              <span>Shopping unit</span>
              <span>Strategy</span>
            </div>
            {ingredients.map((ingredient) => (
              <Link
                key={ingredient.id}
                to={isPlatformAdmin ? `/ingredients/${ingredient.id}/edit` : `/ingredients/${ingredient.id}`}
                className="ingredient-catalog-row"
              >
                <span>
                  <strong>{ingredient.display_name}</strong>
                  <span className="muted ingredient-canonical">{ingredient.canonical_name}</span>
                </span>
                <span>
                  <span className="admin-mobile-label">Category</span>
                  {formatCatalogLabel(ingredient.category)}
                </span>
                <span>
                  <span className="admin-mobile-label">Shopping unit</span>
                  {unitSymbols.get(ingredient.preferred_shopping_unit_id ?? -1) ?? "—"}
                </span>
                <span>
                  <span className="admin-mobile-label">Strategy</span>
                  {formatAggregationStrategy(ingredient.aggregation_strategy)}
                </span>
              </Link>
            ))}
          </div>
        ) : null}
      </PageShell>
    </div>
  );
}
