import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

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
import { useAuth } from "../auth/AuthContext";
import { formatRecipeDifficulty, formatRecipeTime } from "./effectiveValues";
import { DishClassificationSummary } from "./DishClassificationSummary";
import { dishPlaceholderEmoji } from "./dishVisual";

type RecipeSummary = {
  recipe: Recipe;
  stepCount: number;
  ingredientCount: number;
};

export function DishDetailPage() {
  const { dishId } = useParams();
  const id = Number(dishId);
  const navigate = useNavigate();
  const { accessToken, isAdmin } = useAuth();
  const [dish, setDish] = useState<Dish | null>(null);
  const [tags, setTags] = useState<Tag[]>([]);
  const [recipeSummaries, setRecipeSummaries] = useState<RecipeSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    if (!accessToken || !id) {
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
  }, [accessToken, id]);

  useEffect(() => {
    void load();
  }, [load]);

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
      <section className="card">
        <p className="muted">Loading dish…</p>
      </section>
    );
  }

  if (error || !dish) {
    return (
      <section className="card">
        <p className="error" role="alert">
          {error ?? "Dish not found"}
        </p>
        <ButtonLink to="/dishes" variant="secondary">
          Back to dishes
        </ButtonLink>
      </section>
    );
  }

  return (
    <section className="card stack">
      <div className="row-between dish-detail-header">
        <div className="dish-detail-intro">
          <div className="dish-detail-media" aria-hidden={!dish.image_url}>
            {dish.image_url ? (
              <img src={dish.image_url} alt="" className="dish-detail-image" />
            ) : (
              <span className="dish-detail-emoji">{dishPlaceholderEmoji(dish)}</span>
            )}
          </div>
          <div>
            <h2>{dish.name}</h2>
            {dish.description ? <p>{dish.description}</p> : null}
          </div>
        </div>
        <div className="row-actions">
          <ButtonLink to="/dishes" variant="secondary">
            Back
          </ButtonLink>
          {isAdmin ? <ButtonLink to={`/dishes/${dish.id}/edit`}>Edit dish</ButtonLink> : null}
          {isAdmin ? (
            <ButtonLink to={`/dishes/${dish.id}/recipes/new`}>Add recipe</ButtonLink>
          ) : null}
          {isAdmin ? (
            <button
              type="button"
              className="button button-danger"
              onClick={() => setConfirmingDelete(true)}
              disabled={confirmingDelete || deleting}
            >
              Delete
            </button>
          ) : null}
        </div>
      </div>

      {confirmingDelete ? (
        <div className="confirm-panel" role="alertdialog" aria-labelledby="delete-dish-title">
          <p id="delete-dish-title">
            Are you sure you want to delete <strong>{dish.name}</strong>? This cannot be undone.
          </p>
          <div className="row-actions">
            <button
              type="button"
              className="button button-secondary"
              onClick={() => setConfirmingDelete(false)}
              disabled={deleting}
            >
              Cancel
            </button>
            <button type="button" className="button button-danger" onClick={() => void handleDelete()} disabled={deleting}>
              {deleting ? "Deleting…" : "Yes, delete dish"}
            </button>
          </div>
        </div>
      ) : null}

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      <DishClassificationSummary dish={dish} tags={tags} />

      <div className="stack">
        <h3 className="section-title">Recipe variants</h3>
        {recipeSummaries.length === 0 ? (
          <p className="muted">No recipe variants yet.</p>
        ) : (
          <ul className="recipe-card-list">
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
                <li key={recipe.id} className="recipe-card">
                  <div>
                    <strong>{recipe.variant_name}</strong>
                    <p className="muted">
                      {incomplete ? `Incomplete recipe · ${meta}` : meta}
                    </p>
                  </div>
                  <div className="row-actions">
                    <ButtonLink to={`/dishes/${dish.id}/recipes/${recipe.id}`} variant="secondary">
                      View
                    </ButtonLink>
                    {isAdmin ? (
                      <ButtonLink to={`/dishes/${dish.id}/recipes/${recipe.id}/edit`}>Edit</ButtonLink>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
