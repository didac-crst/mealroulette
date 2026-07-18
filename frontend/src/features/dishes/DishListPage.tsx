import { useEffect, useMemo, useState } from "react";

import { fetchDishes, fetchRecipes, type Dish } from "../../api/catalog";
import { ButtonLink } from "../../components/ButtonLink";
import { ApiError } from "../../api/client";
import { Card, ChoiceChip, EmptyState, PageShell } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";
import { DishCard } from "./DishCard";
import {
  availableCatalogFilters,
  catalogFilterLabel,
  filterDishesByCatalog,
  type DishCatalogFilter,
} from "./dishCatalogFilters";
import { filterDishesBySearch, normalizeDishSearchQuery } from "./dishSearch";

export function DishListPage() {
  const { accessToken, isHouseholdAdmin } = useAuth();
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [recipeNamesByDishId, setRecipeNamesByDishId] = useState<Record<number, string[]>>({});
  const [search, setSearch] = useState("");
  const [catalogFilter, setCatalogFilter] = useState<DishCatalogFilter>("all");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetchDishes(accessToken)
      .then((data) => {
        if (!cancelled) {
          setDishes(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load dishes");
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
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken || dishes.length === 0) {
      setRecipeNamesByDishId({});
      return;
    }
    let cancelled = false;
    void Promise.all(
      dishes.map(async (dish) => {
        try {
          const recipes = await fetchRecipes(accessToken, dish.id);
          return [dish.id, recipes.map((recipe) => recipe.variant_name)] as const;
        } catch {
          return [dish.id, []] as const;
        }
      }),
    ).then((entries) => {
      if (!cancelled) {
        setRecipeNamesByDishId(Object.fromEntries(entries));
      }
    });
    return () => {
      cancelled = true;
    };
  }, [accessToken, dishes]);

  const catalogFilters = useMemo(() => availableCatalogFilters(dishes), [dishes]);
  const dishesForFilters = useMemo(
    () => filterDishesByCatalog(dishes, catalogFilter),
    [catalogFilter, dishes],
  );
  const filteredDishes = useMemo(
    () => filterDishesBySearch(dishesForFilters, search, recipeNamesByDishId),
    [dishesForFilters, recipeNamesByDishId, search],
  );
  const normalizedSearch = normalizeDishSearchQuery(search);
  const showingFilteredResults = normalizedSearch.length > 0 || catalogFilter !== "all";
  const subtitle = loading
    ? undefined
    : `${dishes.length} dish${dishes.length === 1 ? "" : "es"}`;

  const headerActions = (
    <div className="catalog-detail-actions">
      <ButtonLink to="/catalog" variant="secondary">
        Browse public catalog
      </ButtonLink>
      {isHouseholdAdmin ? <ButtonLink to="/dishes/new">Add dish</ButtonLink> : null}
    </div>
  );

  return (
    <div className="catalog-page">
      <PageShell
        title="Dishes"
        subtitle={subtitle}
        loading={loading}
        loadingMessage="Loading dishes…"
        actions={headerActions}
      >
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : null}

        {!loading && !error && dishes.length > 0 ? (
          <Card density="comfortable" className="catalog-search-card">
            <label className="catalog-search-label">
              Search dishes
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Dish or recipe name"
                autoComplete="off"
              />
            </label>
            <div className="catalog-filter-bar" role="group" aria-label="Filter by dish type">
              {catalogFilters.map((filter) => (
                <ChoiceChip
                  key={filter}
                  label={catalogFilterLabel(filter)}
                  selected={catalogFilter === filter}
                  onClick={() => setCatalogFilter(filter)}
                />
              ))}
            </div>
            <p className="muted catalog-search-meta">
              {showingFilteredResults
                ? `Showing ${filteredDishes.length} of ${dishes.length} dishes`
                : `${dishes.length} dish${dishes.length === 1 ? "" : "es"}`}
            </p>
          </Card>
        ) : null}

        {!loading && !error && dishes.length === 0 ? (
          <EmptyState
            title="No dishes yet"
            description="Browse the public catalog to adopt recipes, or add your first dish."
            action={
              <div className="catalog-detail-actions">
                <ButtonLink to="/catalog">Browse public catalog</ButtonLink>
                {isHouseholdAdmin ? (
                  <ButtonLink to="/dishes/new" variant="secondary">
                    Add dish
                  </ButtonLink>
                ) : null}
              </div>
            }
          />
        ) : null}

        {!loading && !error && dishes.length > 0 && filteredDishes.length === 0 ? (
          <EmptyState
            title="No matches"
            description="No dishes match your filters. Try a different search or dish type."
          />
        ) : null}

        {filteredDishes.length > 0 ? (
          <div className="dish-card-grid">
            {filteredDishes.map((dish) => (
              <DishCard key={dish.id} dish={dish} />
            ))}
          </div>
        ) : null}
      </PageShell>
    </div>
  );
}
