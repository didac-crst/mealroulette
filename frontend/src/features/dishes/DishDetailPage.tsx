import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  addRecipeIngredient,
  confirmIngredient,
  createRecipe,
  createRecipeStep,
  fetchDish,
  fetchIngredients,
  fetchRecipeIngredients,
  fetchRecipes,
  fetchRecipeSteps,
  fetchTags,
  fetchUnits,
  resolveIngredient,
  type Dish,
  type Ingredient,
  type Recipe,
  type RecipeIngredient,
  type RecipeStep,
  type Tag,
  type Unit,
} from "../../api/catalog";
import { ApiError } from "../../api/client";
import { useAuth } from "../auth/AuthContext";

export function DishDetailPage() {
  const { dishId } = useParams();
  const id = Number(dishId);
  const { accessToken, isAdmin } = useAuth();
  const [dish, setDish] = useState<Dish | null>(null);
  const [tags, setTags] = useState<Tag[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!accessToken || !id) {
      return;
    }
    setLoading(true);
    try {
      const [dishData, tagData, recipeData] = await Promise.all([
        fetchDish(accessToken, id),
        fetchTags(accessToken),
        fetchRecipes(accessToken, id),
      ]);
      setDish(dishData);
      setTags(tagData);
      setRecipes(recipeData);
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
        <Link to="/dishes">Back to dishes</Link>
      </section>
    );
  }

  const dishTags = tags.filter((tag) => dish.tag_ids.includes(tag.id));

  return (
    <section className="card stack">
      <div className="row-between">
        <div>
          <h2>{dish.name}</h2>
          {dish.description ? <p>{dish.description}</p> : null}
        </div>
        <div className="row-actions">
          <Link to="/dishes">Back</Link>
          {isAdmin ? <Link to={`/dishes/${dish.id}/edit`}>Edit</Link> : null}
        </div>
      </div>
      {dishTags.length > 0 ? (
        <p>
          <span className="muted">Tags: </span>
          {dishTags.map((tag) => `${tag.family}/${tag.name}`).join(", ")}
        </p>
      ) : null}
      {accessToken
        ? recipes.map((recipe) => (
            <RecipePanel
              key={recipe.id}
              recipe={recipe}
              accessToken={accessToken}
              isAdmin={isAdmin}
              onChanged={load}
            />
          ))
        : null}
      {isAdmin && accessToken ? (
        <AddRecipeForm dishId={dish.id} accessToken={accessToken} onCreated={load} />
      ) : null}
    </section>
  );
}

function RecipePanel({
  recipe,
  accessToken,
  isAdmin,
  onChanged,
}: {
  recipe: Recipe;
  accessToken: string;
  isAdmin: boolean;
  onChanged: () => void;
}) {
  const [steps, setSteps] = useState<RecipeStep[]>([]);
  const [ingredients, setIngredients] = useState<RecipeIngredient[]>([]);
  const [ingredientNames, setIngredientNames] = useState<Record<number, string>>({});
  const [units, setUnits] = useState<Unit[]>([]);

  const loadRecipe = useCallback(async () => {
    const [stepData, ingredientData, unitData, allIngredients] = await Promise.all([
      fetchRecipeSteps(accessToken, recipe.id),
      fetchRecipeIngredients(accessToken, recipe.id),
      fetchUnits(accessToken),
      fetchIngredients(accessToken),
    ]);
    setSteps(stepData);
    setIngredients(ingredientData);
    setUnits(unitData);
    const names: Record<number, string> = {};
    for (const item of allIngredients) {
      names[item.id] = item.display_name;
    }
    setIngredientNames(names);
  }, [accessToken, recipe.id]);

  useEffect(() => {
    void loadRecipe();
  }, [loadRecipe]);

  return (
    <div className="subcard stack">
      <h3>{recipe.variant_name}</h3>
      {recipe.description ? <p className="muted">{recipe.description}</p> : null}
      <div>
        <h4>Steps</h4>
        <ol>
          {steps.map((step) => (
            <li key={step.id}>
              {step.instruction}
            </li>
          ))}
        </ol>
        {isAdmin ? (
          <AddStepForm
            recipeId={recipe.id}
            nextStep={steps.length + 1}
            accessToken={accessToken}
            onCreated={() => {
              void loadRecipe();
              onChanged();
            }}
          />
        ) : null}
      </div>
      <div>
        <h4>Ingredients</h4>
        <ul>
          {ingredients.map((item) => (
            <li key={item.id}>
              {ingredientNames[item.ingredient_id] ?? `ingredient #${item.ingredient_id}`}
              {item.quantity
                ? ` — ${item.quantity}${units.find((u) => u.id === item.unit_id)?.symbol ? ` ${units.find((u) => u.id === item.unit_id)?.symbol}` : ""}`
                : ""}
            </li>
          ))}
        </ul>
        {isAdmin ? (
          <AddIngredientForm
            recipeId={recipe.id}
            accessToken={accessToken}
            units={units}
            onAdded={() => {
              void loadRecipe();
              onChanged();
            }}
          />
        ) : null}
      </div>
    </div>
  );
}

function AddRecipeForm({
  dishId,
  accessToken,
  onCreated,
}: {
  dishId: number;
  accessToken: string;
  onCreated: () => void;
}) {
  const [variantName, setVariantName] = useState("default");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await createRecipe(accessToken, dishId, { variant_name: variantName });
      setVariantName("default");
      onCreated();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="inline-form">
      <label>
        New recipe variant
        <input value={variantName} onChange={(event) => setVariantName(event.target.value)} required />
      </label>
      <button type="submit" disabled={submitting}>
        Add recipe
      </button>
    </form>
  );
}

function AddStepForm({
  recipeId,
  nextStep,
  accessToken,
  onCreated,
}: {
  recipeId: number;
  nextStep: number;
  accessToken: string;
  onCreated: () => void;
}) {
  const [instruction, setInstruction] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await createRecipeStep(accessToken, recipeId, {
        step_number: nextStep,
        instruction,
      });
      setInstruction("");
      onCreated();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="inline-form">
      <label>
        Step {nextStep}
        <input
          value={instruction}
          onChange={(event) => setInstruction(event.target.value)}
          placeholder="Instruction"
          required
        />
      </label>
      <button type="submit" disabled={submitting}>
        Add step
      </button>
    </form>
  );
}

function AddIngredientForm({
  recipeId,
  accessToken,
  units,
  onAdded,
}: {
  recipeId: number;
  accessToken: string;
  units: Unit[];
  onAdded: () => void;
}) {
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unitId, setUnitId] = useState<number | "">("");
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function resolveOrCreateIngredient(proposedName: string): Promise<Ingredient> {
    const resolved = await resolveIngredient(accessToken, proposedName);
    if (resolved.status === "exact" && resolved.ingredient) {
      return resolved.ingredient;
    }
    return confirmIngredient(accessToken, {
      action: "create",
      proposed_name: proposedName,
      display_name: proposedName,
    });
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      const ingredient = await resolveOrCreateIngredient(name.trim());
      await addRecipeIngredient(accessToken, recipeId, {
        ingredient_id: ingredient.id,
        quantity: quantity || null,
        unit_id: unitId === "" ? null : unitId,
      });
      setName("");
      setQuantity("");
      setUnitId("");
      onAdded();
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Failed to add ingredient");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="inline-form stack">
      <label>
        Ingredient
        <input value={name} onChange={(event) => setName(event.target.value)} required />
      </label>
      <div className="grid-2">
        <label>
          Quantity
          <input value={quantity} onChange={(event) => setQuantity(event.target.value)} />
        </label>
        <label>
          Unit
          <select value={unitId} onChange={(event) => setUnitId(event.target.value ? Number(event.target.value) : "")}>
            <option value="">—</option>
            {units.map((unit) => (
              <option key={unit.id} value={unit.id}>
                {unit.symbol}
              </option>
            ))}
          </select>
        </label>
      </div>
      {message ? <p className="error">{message}</p> : null}
      <button type="submit" disabled={submitting}>
        Add ingredient
      </button>
    </form>
  );
}
