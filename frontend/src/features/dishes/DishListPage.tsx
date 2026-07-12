import { useEffect, useState } from "react";

import { fetchDishes, fetchRecipes, type Dish, type Recipe } from "../../api/catalog";
import { ButtonLink } from "../../components/ButtonLink";
import { ApiError } from "../../api/client";
import { useAuth } from "../auth/AuthContext";
import { PlanForMealDialog } from "../planning/PlanForMealDialog";
import { DishCard } from "./DishCard";

export function DishListPage() {
  const { accessToken, isAdmin } = useAuth();
  const [dishes, setDishes] = useState<Dish[]>([]);
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
      <div className="dish-card-grid">
        {dishes.map((dish) => (
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
