import { useEffect, useState } from "react";

import { fetchDishes, type Dish } from "../../api/catalog";
import { ButtonLink } from "../../components/ButtonLink";
import { ApiError } from "../../api/client";
import { useAuth } from "../auth/AuthContext";
import { DishCard } from "./DishCard";

export function DishListPage() {
  const { accessToken, isAdmin } = useAuth();
  const [dishes, setDishes] = useState<Dish[]>([]);
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

  return (
    <section className="card dish-library">
      <div className="row-between">
        <h2>Dish library</h2>
        {isAdmin ? <ButtonLink to="/dishes/new">Add dish</ButtonLink> : null}
      </div>
      {loading ? <p className="muted">Loading dishes…</p> : null}
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {!loading && !error && dishes.length === 0 ? (
        <p className="muted">No dishes yet.{isAdmin ? " Add your first one." : ""}</p>
      ) : null}
      <div className="dish-card-grid">
        {dishes.map((dish) => (
          <DishCard key={dish.id} dish={dish} />
        ))}
      </div>
    </section>
  );
}
