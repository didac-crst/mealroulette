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
import { useAuth } from "../auth/AuthContext";
import { RECIPE_TYPE_OPTIONS, formatOptionLabel } from "./classification";
import { DishInheritedContext } from "./DishClassificationSummary";
import {
  formatRecipeDifficulty,
  formatRecipeTime,
} from "./effectiveValues";

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
      <section className="card">
        <p className="muted">Loading recipe…</p>
      </section>
    );
  }

  if (error || !recipe || !dish) {
    return (
      <section className="card">
        <p className="error" role="alert">
          {error ?? "Recipe not found"}
        </p>
        <ButtonLink to={`/dishes/${dishId}`} variant="secondary">
          Back to dish
        </ButtonLink>
      </section>
    );
  }

  return (
    <section className="card stack">
      <div className="row-between">
        <div>
          <p className="muted">{dish.name}</p>
          <h2>
            {recipe.variant_name}
            {recipe.is_main ? <span className="muted"> · Main recipe</span> : null}
          </h2>
          {recipe.description ? <p>{recipe.description}</p> : null}
        </div>
        <div className="row-actions">
          <ButtonLink to={`/dishes/${dish.id}`} variant="secondary">
            Back to dish
          </ButtonLink>
          {isAdmin ? (
            <ButtonLink to={`/dishes/${dish.id}/recipes/${recipe.id}/edit`}>Edit recipe</ButtonLink>
          ) : null}
        </div>
      </div>

      {dish ? <DishInheritedContext dish={dish} tags={tags} /> : null}

      <div className="recipe-meta-summary">
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
        {recipe.description ? (
          <p>
            <span className="muted">Variant note: </span>
            {recipe.description}
          </p>
        ) : null}
      </div>

      <div>
        <h3 className="section-title">Ingredients</h3>
        {ingredients.length === 0 ? (
          <p className="muted">No ingredients yet.</p>
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
      </div>

      <div>
        <h3 className="section-title">Steps</h3>
        {steps.length === 0 ? (
          <p className="muted">No steps yet.</p>
        ) : (
          <ol className="editable-list">
            {steps.map((step) => (
              <li key={step.id}>
                {step.step_number}. {step.instruction}
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );
}
