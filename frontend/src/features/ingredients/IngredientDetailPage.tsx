import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { fetchIngredient, type IngredientDetail } from "../../api/catalog";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { useAuth } from "../auth/AuthContext";

export function IngredientDetailPage() {
  const { ingredientId } = useParams();
  const navigate = useNavigate();
  const { accessToken, isAdmin } = useAuth();
  const [detail, setDetail] = useState<IngredientDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken || !ingredientId || isAdmin) {
      if (isAdmin) {
        setLoading(false);
      }
      return;
    }
    let cancelled = false;
    fetchIngredient(accessToken, Number(ingredientId))
      .then((data) => {
        if (!cancelled) {
          setDetail(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load ingredient");
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
  }, [accessToken, ingredientId, isAdmin]);

  useEffect(() => {
    if (isAdmin && ingredientId) {
      navigate(`/ingredients/${ingredientId}/edit`, { replace: true });
    }
  }, [isAdmin, ingredientId, navigate]);

  if (loading) {
    return (
      <section className="card">
        <p className="muted">Loading ingredient…</p>
      </section>
    );
  }

  if (error || !detail) {
    return (
      <section className="card">
        <p className="error">{error ?? "Ingredient not found"}</p>
        <ButtonLink to="/ingredients">Back to list</ButtonLink>
      </section>
    );
  }

  return (
    <section className="card stack">
      <div className="row-between">
        <h2>{detail.display_name}</h2>
        <ButtonLink to="/ingredients" variant="secondary">
          Back
        </ButtonLink>
      </div>
      <p className="muted">{detail.canonical_name}</p>
      {detail.notes ? <p>{detail.notes}</p> : null}
      <p>
        Category: {detail.category ?? "—"} · Food group: {detail.food_group ?? "—"} · Family:{" "}
        {detail.family ?? "—"} · Strategy: {detail.aggregation_strategy ?? "—"}
      </p>
      <h3>Aliases</h3>
      <ul className="bulleted-list">
        {detail.aliases.map((alias) => (
          <li key={alias.id}>{alias.alias}</li>
        ))}
      </ul>
    </section>
  );
}
