import { useEffect, useMemo, useState } from "react";

import { fetchDishes, fetchRecipes, type Dish, type Recipe } from "../../api/catalog";
import { ButtonLink } from "../../components/ButtonLink";
import { ApiError } from "../../api/client";
import { useAuth } from "../auth/AuthContext";
import { PlanForMealDialog } from "../planning/PlanForMealDialog";
import { DishCard } from "./DishCard";
import { filterDishesBySearch, normalizeDishSearchQuery } from "./dishSearch";

export function DishListPage() {
  const { accessToken, isAdmin } = useAuth();
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [recipeNamesByDishId, setRecipeNamesByDishId] = useState<Record<number, string[]>>({});
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [planDish, setPlanDish] = useState<Dish | null>(null);
  const [planRecipes, setPlanRecipes] = useState<Recipe[]>([]);
  const [planLoading, setPlanLoading] = useState(false);

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

  const filteredDishes = useMemo(
    () => filterDishesBySearch(dishes, search, recipeNamesByDishId),
    [dishes, recipeNamesByDishId, search],
  );
  const normalizedSearch = normalizeDishSearchQuery(search);
  const showingFilteredResults = normalizedSearch.length > 0;

  async function openPlanDialog(dish: Dish) {
    if (!accessToken) {
      return;
    }
    setPlanLoading(true);
    setPlanDish(dish);
    setPlanRecipes([]);
    try {
      const recipes = await fetchRecipes(accessToken, dish.id);
      setPlanRecipes(recipes);
    } catch (err) {
      setPlanDish(null);
      setError(err instanceof ApiError ? err.message : "Failed to load recipes");
    } finally {
      setPlanLoading(false);
    }
  }

  return (
    <section className="card dish-library">
      <div className="row-between">
        <h2>Dish library</h2>
        {isAdmin ? <ButtonLink to="/dishes/new">Add dish</ButtonLink> : null}
      </div>
      {loading ? <p className="muted">Loading dishes…</p> : null}
      {planLoading ? <p className="muted">Loading planner…</p> : null}
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {!loading && !error ? (
        <>
          <label className="dish-search">
            Search dishes
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Dish or recipe name"
              autoComplete="off"
            />
          </label>
          <p className="muted dish-search-meta">
            {showingFilteredResults
              ? `Showing ${filteredDishes.length} of ${dishes.length} dishes`
              : `${dishes.length} dish${dishes.length === 1 ? "" : "es"}`}
          </p>
        </>
      ) : null}
      {!loading && !error && dishes.length > 0 && filteredDishes.length === 0 ? (
        <p className="muted">No dishes match &ldquo;{search.trim()}&rdquo;.</p>
      ) : null}
      <div className="dish-card-grid">
        {filteredDishes.map((dish) => (
          <DishCard key={dish.id} dish={dish} onPlan={(target) => void openPlanDialog(target)} />
        ))}
      </div>
      {accessToken && planDish ? (
        <PlanForMealDialog
          open
          dishId={planDish.id}
          dishName={planDish.name}
          recipes={planRecipes}
          accessToken={accessToken}
          onClose={() => setPlanDish(null)}
        />
      ) : null}
    </section>
  );
}
