import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { fetchIngredient, type IngredientDetail } from "../../api/catalog";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { Card, EmptyState, PageShell } from "../../components/ui";
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
      <div className="admin-page">
        <PageShell title="Ingredient" loading loadingMessage="Loading ingredient…" />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="admin-page">
        <EmptyState
          title="Ingredient not found"
          description={error ?? "This ingredient could not be loaded."}
          action={
            <ButtonLink to="/ingredients" variant="secondary">
              Back to list
            </ButtonLink>
          }
        />
      </div>
    );
  }

  return (
    <div className="admin-page">
      <PageShell
        title={detail.display_name}
        subtitle={detail.canonical_name}
        breadcrumbLabels={{ ingredientId: detail.id, ingredientName: detail.display_name }}
      />

      {detail.notes ? <p>{detail.notes}</p> : null}

      <Card density="comfortable">
        <p>
          Category: {detail.category ?? "—"} · Food group: {detail.food_group ?? "—"} · Family:{" "}
          {detail.family ?? "—"} · Strategy: {detail.aggregation_strategy ?? "—"}
        </p>
      </Card>

      <Card density="comfortable">
        <h2 className="catalog-section-title">Aliases</h2>
        {detail.aliases.length === 0 ? (
          <EmptyState title="No aliases" description="This ingredient has no alternate names." />
        ) : (
          <ul className="bulleted-list">
            {detail.aliases.map((alias) => (
              <li key={alias.id}>{alias.alias}</li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
