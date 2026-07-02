import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

import { fetchDishes, type Dish } from "../../api/catalog";
import { ApiError } from "../../api/client";
import { useAuth } from "../auth/AuthContext";

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
    <section className="card">
      <div className="row-between">
        <h2>Dish library</h2>
        {isAdmin ? (
          <Link to="/dishes/new" className="button">
            Add dish
          </Link>
        ) : null}
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
      <ul className="dish-list">
        {dishes.map((dish) => (
          <li key={dish.id}>
            <Link to={`/dishes/${dish.id}`}>
              <strong>{dish.name}</strong>
              {dish.description ? <span className="muted"> — {dish.description}</span> : null}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
