import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { fetchIngredients, fetchUnits, type Ingredient, type Unit } from "../../api/catalog";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { Button, Card, EmptyState, PageShell } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";

export function IngredientListPage() {
  const { accessToken, isAdmin } = useAuth();
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    fetchUnits(accessToken)
      .then(setUnits)
      .catch(() => setUnits([]));
  }, [accessToken]);

  const unitSymbols = useMemo(() => new Map(units.map((unit) => [unit.id, unit.symbol])), [units]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetchIngredients(accessToken, query)
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
        subtitle="Canonical ingredient catalog with aliases and unit conversions."
        loading={loading}
        loadingMessage="Loading ingredients…"
        actions={
          isAdmin ? (
            <div className="catalog-detail-actions">
              <ButtonLink to="/ingredients/taxonomy" variant="secondary">
                Taxonomy
              </ButtonLink>
              <ButtonLink to="/ingredients/new">Add ingredient</ButtonLink>
            </div>
          ) : undefined
        }
      >

      <Card density="comfortable" className="catalog-search-card">
        <form
          className="catalog-search-label"
          onSubmit={(event) => {
            event.preventDefault();
            setQuery(search);
          }}
        >
          <span>Search</span>
          <div className="target-add-row">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Name, category, or alias match"
            />
            <Button type="submit" variant="secondary">
              Search
            </Button>
          </div>
        </form>
      </Card>

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      {!loading && !error && ingredients.length === 0 ? (
        <EmptyState
          title="No ingredients found"
          description={isAdmin ? "Add your first ingredient to build the catalog." : "Try a different search."}
          action={isAdmin ? <ButtonLink to="/ingredients/new">Add ingredient</ButtonLink> : undefined}
        />
      ) : null}

      {!loading && !error && ingredients.length > 0 ? (
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
              to={isAdmin ? `/ingredients/${ingredient.id}/edit` : `/ingredients/${ingredient.id}`}
              className="ingredient-catalog-row"
            >
              <span>
                <strong>{ingredient.display_name}</strong>
                <span className="muted ingredient-canonical">{ingredient.canonical_name}</span>
              </span>
              <span>
                <span className="admin-mobile-label">Category</span>
                {ingredient.category ?? "—"}
              </span>
              <span>
                <span className="admin-mobile-label">Shopping unit</span>
                {unitSymbols.get(ingredient.preferred_shopping_unit_id ?? -1) ?? "—"}
              </span>
              <span>
                <span className="admin-mobile-label">Strategy</span>
                {ingredient.aggregation_strategy ?? "—"}
              </span>
            </Link>
          ))}
        </div>
      ) : null}
      </PageShell>
    </div>
  );
}
