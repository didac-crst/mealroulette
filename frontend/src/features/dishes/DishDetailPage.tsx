import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  deleteDish,
  fetchDish,
  fetchRecipeIngredients,
  fetchRecipes,
  fetchRecipeSteps,
  fetchTags,
  type Dish,
  type Recipe,
  type Tag,
} from "../../api/catalog";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { Button, Card, EmptyState, OverflowMenu, PageShell, ResponsiveActionGroup } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";
import { formatRecipeDifficulty, formatRecipeTime } from "./effectiveValues";
import { DishClassificationSummary } from "./DishClassificationSummary";
import { dishPlaceholderEmoji } from "./dishVisual";
import { PlanForMealDialog } from "../planning/PlanForMealDialog";

type RecipeSummary = {
  recipe: Recipe;
  stepCount: number;
  ingredientCount: number;
};

export function DishDetailPage() {
  const { dishId } = useParams();
  const id = Number(dishId);
  const hasValidId = dishId !== undefined && Number.isFinite(id) && id > 0;
  const navigate = useNavigate();
  const { accessToken, isAdmin } = useAuth();
  const [dish, setDish] = useState<Dish | null>(null);
  const [tags, setTags] = useState<Tag[]>([]);
  const [recipeSummaries, setRecipeSummaries] = useState<RecipeSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [planDialogOpen, setPlanDialogOpen] = useState(false);

  const load = useCallback(async () => {
    if (!accessToken || !hasValidId) {
      return;
    }
    setLoading(true);
    try {
      const [dishData, tagData, recipes] = await Promise.all([
        fetchDish(accessToken, id),
        fetchTags(accessToken),
        fetchRecipes(accessToken, id),
      ]);
      const summaries = await Promise.all(
        recipes.map(async (recipe) => {
          const [steps, ingredients] = await Promise.all([
            fetchRecipeSteps(accessToken, recipe.id),
            fetchRecipeIngredients(accessToken, recipe.id),
          ]);
          return { recipe, stepCount: steps.length, ingredientCount: ingredients.length };
        }),
      );
      setDish(dishData);
      setTags(tagData);
      setRecipeSummaries(summaries);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load dish");
    } finally {
      setLoading(false);
    }
  }, [accessToken, hasValidId, id]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    if (!hasValidId) {
      setError("Invalid dish");
      setLoading(false);
      return;
    }
    void load();
  }, [accessToken, hasValidId, load]);

  async function handleDelete() {
    if (!accessToken) {
      return;
    }
    setDeleting(true);
    setError(null);
    try {
      await deleteDish(accessToken, id);
      navigate("/dishes", { replace: true });
    } catch (err) {
      setConfirmingDelete(false);
      setError(err instanceof ApiError ? err.message : "Failed to delete dish");
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="catalog-page">
        <PageShell title="Dish" loading loadingMessage="Loading dish…" />
      </div>
    );
  }

  if (error || !dish) {
    return (
      <div className="catalog-page">
        <EmptyState
          title="Dish not found"
          description={error ?? "This dish could not be loaded."}
          action={
            <ButtonLink to="/dishes" variant="secondary">
              Back to dishes
            </ButtonLink>
          }
        />
      </div>
    );
  }

  return (
    <div className="catalog-page">
      <PageShell
        title={dish.name}
        subtitle={dish.description ?? undefined}
        breadcrumbLabels={{ dishId: dish.id, dishName: dish.name }}
      />
      <Card density="comfortable" className="catalog-detail-hero">
        <div className="catalog-detail-intro">
          <div className="catalog-detail-media" aria-hidden={!dish.image_url}>
            {dish.image_url ? (
              <img src={dish.image_url} alt="" className="catalog-detail-image" />
            ) : (
              <span className="catalog-detail-emoji">{dishPlaceholderEmoji(dish)}</span>
            )}
          </div>
          <div>
            <p className="muted">Public key: {dish.public_key}</p>
          </div>
        </div>
        <ResponsiveActionGroup className="catalog-detail-actions" stackOnMobile>
          <Button type="button" onClick={() => setPlanDialogOpen(true)}>
            Plan for…
          </Button>
          {isAdmin ? (
            <ButtonLink to={`/dishes/${dish.id}/edit`} variant="ghost">
              Edit dish
            </ButtonLink>
          ) : null}
          {isAdmin ? (
            <OverflowMenu
              ariaLabel="Dish admin actions"
              items={[
                {
                  id: "add-recipe",
                  label: "Add recipe",
                  onClick: () => navigate(`/dishes/${dish.id}/recipes/new`),
                },
                {
                  id: "delete",
                  label: "Delete dish",
                  variant: "danger",
                  disabled: deleting,
                  onClick: () => setConfirmingDelete(true),
                },
              ]}
            />
          ) : null}
        </ResponsiveActionGroup>
      </Card>

      {confirmingDelete ? (
        <Card className="confirm-panel" role="alertdialog" aria-labelledby="delete-dish-title">
          <p id="delete-dish-title">
            Are you sure you want to delete <strong>{dish.name}</strong>? This cannot be undone.
          </p>
          <div className="catalog-detail-actions">
            <Button type="button" variant="secondary" onClick={() => setConfirmingDelete(false)} disabled={deleting}>
              Cancel
            </Button>
            <Button type="button" variant="danger" onClick={() => void handleDelete()} loading={deleting}>
              Yes, delete dish
            </Button>
          </div>
        </Card>
      ) : null}

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      <DishClassificationSummary dish={dish} tags={tags} />

      <Card density="comfortable">
        <h2 className="catalog-section-title">Recipe variants</h2>
        {recipeSummaries.length === 0 ? (
          <EmptyState
            title="No recipe variants yet"
            description="Add a recipe variant to cook or plan this dish."
            action={
              isAdmin ? (
                <ButtonLink to={`/dishes/${dish.id}/recipes/new`}>Add recipe</ButtonLink>
              ) : undefined
            }
          />
        ) : (
          <ul className="catalog-recipe-list">
            {recipeSummaries.map(({ recipe, stepCount, ingredientCount }) => {
              const incomplete = stepCount === 0 || ingredientCount === 0;
              const meta = [
                recipe.is_main ? "Main recipe" : null,
                recipe.servings ? `${recipe.servings} servings` : "Servings not set",
                formatRecipeDifficulty(recipe),
                formatRecipeTime(recipe),
                `${stepCount} steps`,
                `${ingredientCount} ingredients`,
              ]
                .filter(Boolean)
                .join(" · ");
              return (
                <li key={recipe.id} className="catalog-recipe-card">
                  <Link to={`/dishes/${dish.id}/recipes/${recipe.id}`} className="catalog-recipe-card-link">
                    <p className="catalog-recipe-card-title">{recipe.variant_name}</p>
                    <p className="catalog-recipe-card-meta muted">
                      {incomplete ? `Incomplete recipe · ${meta}` : meta}
                    </p>
                  </Link>
                  {isAdmin ? (
                    <OverflowMenu
                      ariaLabel={`Actions for ${recipe.variant_name}`}
                      items={[
                        {
                          id: "edit",
                          label: "Edit recipe",
                          onClick: () => navigate(`/dishes/${dish.id}/recipes/${recipe.id}/edit`),
                        },
                      ]}
                    />
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </Card>

      {accessToken ? (
        <PlanForMealDialog
          open={planDialogOpen}
          dishId={dish.id}
          dishName={dish.name}
          recipes={recipeSummaries.map((summary) => summary.recipe)}
          accessToken={accessToken}
          onClose={() => setPlanDialogOpen(false)}
        />
      ) : null}
    </div>
  );
}
