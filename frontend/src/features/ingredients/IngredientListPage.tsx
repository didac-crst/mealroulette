import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { fetchIngredients, fetchUnits, type Ingredient, type Unit } from "../../api/catalog";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
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
    <section className="card stack">
      <div className="row-between">
        <div>
          <h2>Ingredients</h2>
          <p className="muted">Canonical ingredient catalog with aliases and unit conversions.</p>
        </div>
        {isAdmin ? <ButtonLink to="/ingredients/new">Add ingredient</ButtonLink> : null}
      </div>

      <form
        className="row-between"
        onSubmit={(event) => {
          event.preventDefault();
          setQuery(search);
        }}
      >
        <label className="ingredient-search">
          Search
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Name, category, or alias match"
          />
        </label>
        <button type="submit" className="button button-secondary">
          Search
        </button>
      </form>

      {loading ? <p className="muted">Loading ingredients…</p> : null}
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      {!loading && !error && ingredients.length === 0 ? (
        <p className="muted">No ingredients found.{isAdmin ? " Add your first one." : ""}</p>
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
              <span>{ingredient.category ?? "—"}</span>
              <span>{unitSymbols.get(ingredient.preferred_shopping_unit_id ?? -1) ?? "—"}</span>
              <span>{ingredient.aggregation_strategy ?? "—"}</span>
            </Link>
          ))}
        </div>
      ) : null}
    </section>
  );
}
