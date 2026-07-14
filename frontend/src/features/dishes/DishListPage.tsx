import { useEffect, useMemo, useState } from "react";

import { fetchDishes, fetchRecipes, type Dish } from "../../api/catalog";
import { ButtonLink } from "../../components/ButtonLink";
import { ApiError } from "../../api/client";
import { Card, ChoiceChip, EmptyState, PageShell } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";
import { DishCard } from "./DishCard";
import {
  availableCourseFilters,
  courseFilterLabel,
  filterDishesByCourse,
  type DishCourseFilter,
} from "./dishCatalogFilters";
import { filterDishesBySearch, normalizeDishSearchQuery } from "./dishSearch";

export function DishListPage() {
  const { accessToken, isAdmin } = useAuth();
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [recipeNamesByDishId, setRecipeNamesByDishId] = useState<Record<number, string[]>>({});
  const [search, setSearch] = useState("");
  const [courseFilter, setCourseFilter] = useState<DishCourseFilter>("all");
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

  const courseFilters = useMemo(() => availableCourseFilters(dishes), [dishes]);
  const dishesForFilters = useMemo(
    () => filterDishesByCourse(dishes, courseFilter),
    [courseFilter, dishes],
  );
  const filteredDishes = useMemo(
    () => filterDishesBySearch(dishesForFilters, search, recipeNamesByDishId),
    [dishesForFilters, recipeNamesByDishId, search],
  );
  const normalizedSearch = normalizeDishSearchQuery(search);
  const showingFilteredResults = normalizedSearch.length > 0 || courseFilter !== "all";
  const subtitle = loading
    ? undefined
    : `${dishes.length} dish${dishes.length === 1 ? "" : "es"}`;

  return (
    <div className="catalog-page">
      <PageShell
        title="Dishes"
        subtitle={subtitle}
        loading={loading}
        loadingMessage="Loading dishes…"
        actions={isAdmin ? <ButtonLink to="/dishes/new">Add dish</ButtonLink> : undefined}
      >
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : null}

        {!loading && !error ? (
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
            {courseFilters.length > 1 ? (
              <div className="catalog-filter-bar" role="group" aria-label="Filter by course">
                {courseFilters.map((filter) => (
                  <ChoiceChip
                    key={filter}
                    label={courseFilterLabel(filter)}
                    selected={courseFilter === filter}
                    onClick={() => setCourseFilter(filter)}
                  />
                ))}
              </div>
            ) : null}
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
            description="Add your first dish to start building your library."
            action={isAdmin ? <ButtonLink to="/dishes/new">Add dish</ButtonLink> : undefined}
          />
        ) : null}

        {!loading && !error && dishes.length > 0 && filteredDishes.length === 0 ? (
          <EmptyState
            title="No matches"
            description={
              <>
                No dishes match your filters. Try a different search or course filter.
              </>
            }
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
