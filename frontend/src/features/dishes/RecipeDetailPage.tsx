import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  fetchDish,
  fetchIngredients,
  fetchRecipe,
  fetchRecipeIngredients,
  fetchRecipeSteps,
  fetchTags,
  fetchUnits,
  type Dish,
  type Recipe,
  type RecipeIngredient,
  type RecipeStep,
  type Tag,
  type Unit,
} from "../../api/catalog";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { Card, EmptyState, PageShell } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";
import { RECIPE_TYPE_OPTIONS, formatOptionLabel } from "./classification";
import { DishInheritedContext } from "./DishClassificationSummary";
import {
  formatRecipeDifficulty,
  formatRecipeTime,
} from "./effectiveValues";
import { formatComputedTraits } from "./computedTraits";
import { formatStepTimerLabel, stepTimerDurationSeconds } from "./recipeCooking";

export function RecipeDetailPage() {
  const { dishId, recipeId } = useParams();
  const dishIdNum = Number(dishId);
  const recipeIdNum = Number(recipeId);
  const { accessToken, isAdmin } = useAuth();
  const [dish, setDish] = useState<Dish | null>(null);
  const [tags, setTags] = useState<Tag[]>([]);
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [steps, setSteps] = useState<RecipeStep[]>([]);
  const [ingredients, setIngredients] = useState<RecipeIngredient[]>([]);
  const [ingredientNames, setIngredientNames] = useState<Record<number, string>>({});
  const [units, setUnits] = useState<Unit[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!accessToken || !dishIdNum || !recipeIdNum) {
      return;
    }
    setLoading(true);
    try {
      const [dishData, tagData, recipeData, stepData, ingredientData, unitData, allIngredients] = await Promise.all([
        fetchDish(accessToken, dishIdNum),
        fetchTags(accessToken),
        fetchRecipe(accessToken, recipeIdNum),
        fetchRecipeSteps(accessToken, recipeIdNum),
        fetchRecipeIngredients(accessToken, recipeIdNum),
        fetchUnits(accessToken),
        fetchIngredients(accessToken),
      ]);
      const names: Record<number, string> = {};
      for (const item of allIngredients) {
        names[item.id] = item.display_name;
      }
      setDish(dishData);
      setTags(tagData);
      setRecipe(recipeData);
      setSteps(stepData);
      setIngredients(ingredientData);
      setUnits(unitData);
      setIngredientNames(names);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load recipe");
    } finally {
      setLoading(false);
    }
  }, [accessToken, dishIdNum, recipeIdNum]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <div className="catalog-page">
        <PageShell title="Recipe" loading loadingMessage="Loading recipe…" />
      </div>
    );
  }

  if (error || !recipe || !dish) {
    return (
      <div className="catalog-page">
        <EmptyState
          title="Recipe not found"
          description={error ?? "This recipe could not be loaded."}
          action={
            <ButtonLink to={`/dishes/${dishId}`} variant="secondary">
              Back to dish
            </ButtonLink>
          }
        />
      </div>
    );
  }

  const subtitleParts = [
    dish.name,
    recipe.is_main ? "Main recipe" : null,
    `Key: ${recipe.public_key}`,
  ].filter(Boolean);

  return (
    <div className="catalog-page">
      <PageShell
        title={recipe.variant_name}
        breadcrumbLabels={{
          dishId: dish.id,
          dishName: dish.name,
          recipeId: recipe.id,
          recipeName: recipe.variant_name,
        }}
        subtitle={
          <>
            <span>{subtitleParts.join(" · ")}</span>
            {recipe.description ? <span>{recipe.description}</span> : null}
            {recipe.computed_traits_json ? (
              <span className="muted">Traits: {formatComputedTraits(recipe.computed_traits_json)}</span>
            ) : null}
          </>
        }
        actions={
          <div className="catalog-detail-actions">
            <ButtonLink to={`/recipes/${recipe.id}/cook`}>Cook</ButtonLink>
            {isAdmin ? (
              <ButtonLink to={`/dishes/${dish.id}/recipes/${recipe.id}/edit`}>Edit recipe</ButtonLink>
            ) : null}
          </div>
        }
      />

      {dish ? <DishInheritedContext dish={dish} tags={tags} /> : null}

      <Card density="comfortable">
        <div className="catalog-recipe-meta-grid">
          <p>
            <span className="muted">Servings: </span>
            {recipe.servings ?? "Not set"}
          </p>
          <p>
            <span className="muted">Recipe type: </span>
            {formatOptionLabel(RECIPE_TYPE_OPTIONS, recipe.recipe_type)}
          </p>
          <p>
            <span className="muted">Difficulty: </span>
            {formatRecipeDifficulty(recipe)}
          </p>
          <p>
            <span className="muted">Prep / cook: </span>
            {formatRecipeTime(recipe)}
          </p>
        </div>
      </Card>

      <Card density="comfortable">
        <h2 className="catalog-section-title">Ingredients</h2>
        {ingredients.length === 0 ? (
          <EmptyState title="No ingredients yet" description="Add ingredients when editing this recipe." />
        ) : (
          <ul className="editable-list">
            {ingredients.map((item) => {
              const unitSymbol = units.find((unit) => unit.id === item.unit_id)?.symbol;
              return (
                <li key={item.id}>
                  {ingredientNames[item.ingredient_id] ?? `ingredient #${item.ingredient_id}`}
                  {item.quantity ? ` — ${item.quantity}${unitSymbol ? ` ${unitSymbol}` : ""}` : ""}
                  {item.optional ? " (optional)" : ""}
                </li>
              );
            })}
          </ul>
        )}
      </Card>

      <Card density="comfortable">
        <h2 className="catalog-section-title">Steps</h2>
        {steps.length === 0 ? (
          <EmptyState title="No steps yet" description="Add cooking steps when editing this recipe." />
        ) : (
          <ol className="editable-list">
            {steps.map((step) => {
              const timerSeconds = stepTimerDurationSeconds(step);
              return (
                <li key={step.id}>
                  {step.step_number}. {step.instruction}
                  {timerSeconds ? <span className="muted"> · {formatStepTimerLabel(timerSeconds)}</span> : null}
                </li>
              );
            })}
          </ol>
        )}
      </Card>
    </div>
  );
}
