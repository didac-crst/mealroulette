import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import * as catalogApi from "../../api/publicCatalog";
import type { PublicRecipeMember } from "../../api/publicCatalog";
import { ButtonLink } from "../../components/ButtonLink";
import { Button, Card, EmptyState, PageShell } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";

type SnapshotIngredient = {
  ingredient_display_name?: string;
  quantity?: string | null;
  unit_symbol?: string | null;
  optional?: boolean;
  notes?: string | null;
};

type SnapshotStep = {
  step_number?: number;
  instruction?: string;
};

export function PublicRecipeDetailPage() {
  const { publicRecipeId } = useParams();
  const navigate = useNavigate();
  const { accessToken, hasHousehold } = useAuth();
  const [item, setItem] = useState<PublicRecipeMember | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [adopting, setAdopting] = useState(false);

  const load = useCallback(async () => {
    if (!accessToken || !publicRecipeId || !hasHousehold) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await catalogApi.getPublicRecipe(accessToken, publicRecipeId);
      setItem(data);
      setError(null);
    } catch (err) {
      setItem(null);
      setError(err instanceof ApiError ? err.message : "Failed to load public recipe");
    } finally {
      setLoading(false);
    }
  }, [accessToken, hasHousehold, publicRecipeId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleAdopt() {
    if (!accessToken || !publicRecipeId) {
      return;
    }
    setAdopting(true);
    setError(null);
    try {
      const result = await catalogApi.adoptPublicRecipe(accessToken, publicRecipeId);
      navigate(`/dishes/${result.dish_id}/recipes/${result.recipe_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to adopt recipe");
    } finally {
      setAdopting(false);
    }
  }

  if (loading) {
    return (
      <div className="catalog-page">
        <PageShell title="Public recipe" loading loadingMessage="Loading recipe…" />
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="catalog-page">
        <EmptyState
          title="Public recipe not found"
          description={error ?? "This recipe is not available in the catalog."}
          action={
            <ButtonLink to="/catalog" variant="secondary">
              Back to catalog
            </ButtonLink>
          }
        />
      </div>
    );
  }

  const ingredients = (item.snapshot.ingredients as SnapshotIngredient[] | undefined) ?? [];
  const steps = (item.snapshot.steps as SnapshotStep[] | undefined) ?? [];

  return (
    <div className="catalog-page">
      <PageShell
        title={item.title}
        subtitle={item.description ?? "Public catalog recipe"}
        actions={
          <div className="catalog-detail-actions">
            <ButtonLink to="/catalog" variant="secondary">
              Back
            </ButtonLink>
            <Button onClick={() => void handleAdopt()} disabled={adopting}>
              {adopting ? "Adopting…" : "Adopt into household"}
            </Button>
          </div>
        }
      />

      {error ? <p className="form-error">{error}</p> : null}

      <Card density="comfortable">
        <p className="muted">Version {item.current_version.version_number}</p>
      </Card>

      <Card density="comfortable">
        <h2 className="catalog-section-title">Ingredients</h2>
        {ingredients.length === 0 ? (
          <p className="muted">No ingredients in this snapshot.</p>
        ) : (
          <ul>
            {ingredients.map((ingredient, index) => (
              <li key={`${ingredient.ingredient_display_name ?? "ingredient"}-${index}`}>
                {ingredient.quantity ? `${ingredient.quantity} ` : ""}
                {ingredient.unit_symbol ? `${ingredient.unit_symbol} ` : ""}
                {ingredient.ingredient_display_name ?? "Ingredient"}
                {ingredient.optional ? " (optional)" : ""}
                {ingredient.notes ? ` — ${ingredient.notes}` : ""}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card density="comfortable">
        <h2 className="catalog-section-title">Steps</h2>
        {steps.length === 0 ? (
          <p className="muted">No steps in this snapshot.</p>
        ) : (
          <ol>
            {steps
              .slice()
              .sort((a, b) => (a.step_number ?? 0) - (b.step_number ?? 0))
              .map((step, index) => (
                <li key={`${step.step_number ?? index}`}>
                  {step.instruction ?? "Step"}
                </li>
              ))}
          </ol>
        )}
      </Card>
    </div>
  );
}
