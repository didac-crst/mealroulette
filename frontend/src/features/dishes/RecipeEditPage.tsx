import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  addRecipeIngredient,
  confirmIngredient,
  createRecipe,
  createRecipeStep,
  deleteRecipe,
  deleteRecipeIngredient,
  deleteRecipeStep,
  fetchDish,
  fetchIngredients,
  fetchRecipe,
  fetchRecipeIngredients,
  fetchRecipeSteps,
  fetchRecipes,
  fetchTags,
  fetchUnits,
  resolveIngredient,
  updateRecipe,
  updateRecipeIngredient,
  updateRecipeStep,
  type Dish,
  type Ingredient,
  type Recipe,
  type RecipeIngredient,
  type RecipeStep,
  type Tag,
  type Unit,
} from "../../api/catalog";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { Button, Card, DisclosureSection, FormSection, FormStickyActions, PageShell } from "../../components/ui";
import { useFormSaveState } from "../../lib/useFormSaveState";
import { useAuth } from "../auth/AuthContext";
import { formatStepTimerLabel, stepTimerDurationSeconds, timerMinutesFromSeconds, timerSecondsFromMinutesInput } from "./recipeCooking";
import { RECIPE_TYPE_OPTIONS } from "./classification";
import { DIFFICULTY_OPTIONS } from "./constants";
import { DishInheritedContext } from "./DishClassificationSummary";

type RecipeForm = {
  variant_name: string;
  variant_description: string;
  servings: string;
  recipe_type: Recipe["recipe_type"];
  is_main: boolean;
  prep_time_minutes: string;
  cook_time_minutes: string;
  difficulty: string;
  source_url: string;
  notes: string;
};

const emptyRecipeForm: RecipeForm = {
  variant_name: "default",
  variant_description: "",
  servings: "",
  recipe_type: "standard",
  is_main: false,
  prep_time_minutes: "",
  cook_time_minutes: "",
  difficulty: "",
  source_url: "",
  notes: "",
};

export function RecipeEditPage() {
  const { dishId, recipeId } = useParams();
  const isNew = !recipeId;
  const dishIdNum = Number(dishId);
  const recipeIdNum = recipeId ? Number(recipeId) : null;
  const navigate = useNavigate();
  const { accessToken, isAdmin } = useAuth();
  const [dish, setDish] = useState<Dish | null>(null);
  const [tags, setTags] = useState<Tag[]>([]);
  const [form, setForm] = useState<RecipeForm>(emptyRecipeForm);
  const [steps, setSteps] = useState<RecipeStep[]>([]);
  const [ingredients, setIngredients] = useState<RecipeIngredient[]>([]);
  const [ingredientNames, setIngredientNames] = useState<Record<number, string>>({});
  const [units, setUnits] = useState<Unit[]>([]);
  const [allIngredients, setAllIngredients] = useState<Ingredient[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!isNew);
  const [submitting, setSubmitting] = useState(false);
  const [showAddStep, setShowAddStep] = useState(false);
  const [showAddIngredient, setShowAddIngredient] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [existingRecipeCount, setExistingRecipeCount] = useState(0);
  const { status: saveStatus, setBaseline } = useFormSaveState(form, { saving: submitting, error });

  const loadRecipeData = useCallback(async () => {
    if (!accessToken || !recipeIdNum) {
      return;
    }
    const [recipe, stepData, ingredientData, unitData, ingredientsCatalog] = await Promise.all([
      fetchRecipe(accessToken, recipeIdNum),
      fetchRecipeSteps(accessToken, recipeIdNum),
      fetchRecipeIngredients(accessToken, recipeIdNum),
      fetchUnits(accessToken),
      fetchIngredients(accessToken),
    ]);
    const names: Record<number, string> = {};
    for (const item of ingredientsCatalog) {
      names[item.id] = item.display_name;
    }
    setForm({
      variant_name: recipe.variant_name,
      variant_description: recipe.description ?? "",
      servings: recipe.servings?.toString() ?? "",
      recipe_type: recipe.recipe_type,
      is_main: recipe.is_main,
      prep_time_minutes: recipe.prep_time_minutes?.toString() ?? "",
      cook_time_minutes: recipe.cook_time_minutes?.toString() ?? "",
      difficulty: recipe.difficulty ?? "",
      source_url: recipe.source_url ?? "",
      notes: recipe.notes ?? "",
    });
    setSteps(stepData);
    setIngredients(ingredientData);
    setUnits(unitData);
    setAllIngredients(ingredientsCatalog);
    setIngredientNames(names);
    setBaseline({
      variant_name: recipe.variant_name,
      variant_description: recipe.description ?? "",
      servings: recipe.servings?.toString() ?? "",
      recipe_type: recipe.recipe_type,
      is_main: recipe.is_main,
      prep_time_minutes: recipe.prep_time_minutes?.toString() ?? "",
      cook_time_minutes: recipe.cook_time_minutes?.toString() ?? "",
      difficulty: recipe.difficulty ?? "",
      source_url: recipe.source_url ?? "",
      notes: recipe.notes ?? "",
    });
  }, [accessToken, recipeIdNum, setBaseline]);

  useEffect(() => {
    if (!isAdmin) {
      navigate(`/dishes/${dishId}`, { replace: true });
    }
  }, [dishId, isAdmin, navigate]);

  useEffect(() => {
    if (!accessToken || !dishIdNum) {
      return;
    }
    Promise.all([fetchDish(accessToken, dishIdNum), fetchTags(accessToken), fetchRecipes(accessToken, dishIdNum)])
      .then(([dishData, tagData, recipes]) => {
        setDish(dishData);
        setTags(tagData);
        setExistingRecipeCount(recipes.length);
        if (isNew && recipes.length === 0) {
          setForm((current) => ({ ...current, is_main: true }));
        }
      })
      .catch((err) => {
        setDish(null);
        setTags([]);
        setExistingRecipeCount(0);
        setError(err instanceof ApiError ? err.message : "Failed to load dish");
      });
  }, [accessToken, dishIdNum, isNew]);

  useEffect(() => {
    if (!accessToken || isNew) {
      if (accessToken && isNew) {
        void fetchUnits(accessToken).then(setUnits);
        void fetchIngredients(accessToken).then(setAllIngredients);
      }
      return;
    }
    let cancelled = false;
    setLoading(true);
    loadRecipeData()
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load recipe");
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
  }, [accessToken, isNew, loadRecipeData]);

  useEffect(() => {
    if (isNew) {
      setBaseline(emptyRecipeForm);
    }
  }, [isNew, setBaseline]);

  const ingredientOptions = useMemo(
    () => allIngredients.map((item) => item.display_name).sort((a, b) => a.localeCompare(b)),
    [allIngredients],
  );

  function recipePayload() {
    const payload = {
      variant_name: form.variant_name.trim(),
      description: form.variant_description || null,
      servings: form.servings ? Number(form.servings) : null,
      recipe_type: form.recipe_type,
      prep_time_minutes: form.prep_time_minutes ? Number(form.prep_time_minutes) : null,
      cook_time_minutes: form.cook_time_minutes ? Number(form.cook_time_minutes) : null,
      difficulty: form.difficulty ? (form.difficulty as Recipe["difficulty"]) : null,
      source_url: form.source_url || null,
      notes: form.notes || null,
    };
    if (!isNew || existingRecipeCount > 0) {
      return { ...payload, is_main: form.is_main };
    }
    return payload;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      if (isNew) {
        const created = await createRecipe(accessToken, dishIdNum, recipePayload());
        navigate(`/dishes/${dishIdNum}/recipes/${created.id}/edit`, { replace: true });
      } else if (recipeIdNum) {
        await updateRecipe(accessToken, recipeIdNum, recipePayload());
        navigate(`/dishes/${dishIdNum}/recipes/${recipeIdNum}`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save recipe");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteRecipe() {
    if (!accessToken || !recipeIdNum) {
      return;
    }
    setSubmitting(true);
    try {
      await deleteRecipe(accessToken, recipeIdNum);
      navigate(`/dishes/${dishIdNum}`, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete recipe");
    } finally {
      setSubmitting(false);
      setConfirmingDelete(false);
    }
  }

  if (loading) {
    return (
      <div className="catalog-edit-page">
        <PageShell title="Edit recipe" loading loadingMessage="Loading recipe…" />
      </div>
    );
  }

  return (
    <div className="catalog-edit-page">
      <PageShell
        title={isNew ? "New recipe variant" : `Edit ${form.variant_name}`}
        subtitle={dish?.name}
        breadcrumbLabels={{
          dishId: dish?.id ?? dishIdNum,
          dishName: dish?.name,
          recipeId: isNew ? undefined : Number(recipeId),
          recipeName: isNew ? undefined : form.variant_name,
        }}
        actions={
          <ButtonLink
            to={isNew ? `/dishes/${dishId}` : `/dishes/${dishId}/recipes/${recipeId}`}
            variant="secondary"
          >
            Cancel
          </ButtonLink>
        }
      />

      {dish ? <DishInheritedContext dish={dish} tags={tags} /> : null}

      <form onSubmit={handleSubmit} className="catalog-form">
        <FormSection title="Recipe basics">
          <div className="stack">
            <label>
              Variant name
              <input
                value={form.variant_name}
                onChange={(event) => setForm({ ...form, variant_name: event.target.value })}
                required
              />
            </label>
            <label>
              Servings
              <input
                type="number"
                min={1}
                value={form.servings}
                onChange={(event) => setForm({ ...form, servings: event.target.value })}
              />
            </label>
            <label>
              Recipe type
              <select
                value={form.recipe_type}
                onChange={(event) =>
                  setForm({ ...form, recipe_type: event.target.value as Recipe["recipe_type"] })
                }
              >
                {RECIPE_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            {isNew && existingRecipeCount === 0 ? (
              <p className="muted">This will be the main recipe and define dish defaults.</p>
            ) : (
              <label className="checkbox-pill">
                <input
                  type="checkbox"
                  checked={form.is_main}
                  onChange={(event) => setForm({ ...form, is_main: event.target.checked })}
                />
                Main recipe (defines dish difficulty and times)
              </label>
            )}
          </div>
        </FormSection>

        <DisclosureSection title="Advanced recipe settings">
          <div className="stack">
            <label>
              Variant description
              <textarea
                value={form.variant_description}
                onChange={(event) => setForm({ ...form, variant_description: event.target.value })}
                rows={2}
              />
            </label>
            <div className="grid-2">
              <label>
                Difficulty
                <select
                  value={form.difficulty}
                  onChange={(event) => setForm({ ...form, difficulty: event.target.value })}
                >
                  {DIFFICULTY_OPTIONS.map((option) => (
                    <option key={option.value || "unset"} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Prep time (min)
                <input
                  type="number"
                  min={0}
                  value={form.prep_time_minutes}
                  onChange={(event) => setForm({ ...form, prep_time_minutes: event.target.value })}
                />
              </label>
              <label>
                Cook time (min)
                <input
                  type="number"
                  min={0}
                  value={form.cook_time_minutes}
                  onChange={(event) => setForm({ ...form, cook_time_minutes: event.target.value })}
                />
              </label>
            </div>
            <label>
              Source URL
              <input
                value={form.source_url}
                onChange={(event) => setForm({ ...form, source_url: event.target.value })}
              />
            </label>
            <label>
              Recipe notes
              <textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} rows={2} />
            </label>
          </div>
        </DisclosureSection>

        <FormStickyActions saveStatus={saveStatus} saveErrorMessage={error}>
          <Button type="submit" loading={submitting}>
            Save recipe
          </Button>
          {!isNew ? (
            <Button type="button" variant="danger" onClick={() => setConfirmingDelete(true)} disabled={submitting}>
              Delete recipe
            </Button>
          ) : null}
        </FormStickyActions>
      </form>

      {isNew ? (
        <p className="muted">Save the recipe first to add ingredients and steps.</p>
      ) : accessToken && recipeIdNum ? (
        <div className="catalog-form">
          <FormSection title="Ingredients">
            <div className="ingredient-table stack">
              {ingredients.length === 0 ? <p className="muted">No ingredients yet.</p> : null}
              {ingredients.map((item) => (
                <IngredientEditorRow
                  key={item.id}
                  item={item}
                  ingredientName={ingredientNames[item.ingredient_id] ?? `ingredient #${item.ingredient_id}`}
                  units={units}
                  accessToken={accessToken}
                  onChanged={loadRecipeData}
                />
              ))}
            </div>
            {showAddIngredient ? (
              <AddIngredientEditor
                recipeId={recipeIdNum}
                accessToken={accessToken}
                units={units}
                ingredientOptions={ingredientOptions}
                onAdded={() => {
                  setShowAddIngredient(false);
                  void loadRecipeData();
                }}
                onCancel={() => setShowAddIngredient(false)}
              />
            ) : (
              <Button type="button" variant="secondary" onClick={() => setShowAddIngredient(true)}>
                + Add ingredient
              </Button>
            )}
          </FormSection>

          <FormSection title="Steps">
            <ol className="editable-list">
              {steps.map((step) => (
                <StepEditorRow
                  key={step.id}
                  step={step}
                  accessToken={accessToken}
                  onChanged={loadRecipeData}
                />
              ))}
            </ol>
            {showAddStep ? (
              <AddStepEditor
                recipeId={recipeIdNum}
                nextStep={steps.length + 1}
                accessToken={accessToken}
                onAdded={() => {
                  setShowAddStep(false);
                  void loadRecipeData();
                }}
                onCancel={() => setShowAddStep(false)}
              />
            ) : (
              <Button type="button" variant="secondary" onClick={() => setShowAddStep(true)}>
                + Add step
              </Button>
            )}
          </FormSection>
        </div>
      ) : null}

      {confirmingDelete ? (
        <Card className="confirm-panel stack">
          <p>Delete this recipe variant? This cannot be undone.</p>
          <div className="catalog-detail-actions">
            <Button type="button" variant="secondary" onClick={() => setConfirmingDelete(false)}>
              Cancel
            </Button>
            <Button type="button" variant="danger" onClick={() => void handleDeleteRecipe()}>
              Delete recipe
            </Button>
          </div>
        </Card>
      ) : null}
    </div>
  );
}

function StepEditorRow({
  step,
  accessToken,
  onChanged,
}: {
  step: RecipeStep;
  accessToken: string;
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [instruction, setInstruction] = useState(step.instruction);
  const [timerMinutes, setTimerMinutes] = useState(() => timerMinutesFromSeconds(step.timer_seconds));
  const [submitting, setSubmitting] = useState(false);

  async function handleSave() {
    if (!instruction.trim()) {
      return;
    }
    setSubmitting(true);
    try {
      await updateRecipeStep(accessToken, step.id, {
        instruction: instruction.trim(),
        timer_seconds: timerSecondsFromMinutesInput(timerMinutes),
      });
      setEditing(false);
      onChanged();
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete() {
    setSubmitting(true);
    try {
      await deleteRecipeStep(accessToken, step.id);
      onChanged();
    } finally {
      setSubmitting(false);
    }
  }

  const timerSeconds = stepTimerDurationSeconds(step);
  const timerLabel = timerSeconds != null ? formatStepTimerLabel(timerSeconds) : null;

  if (editing) {
    return (
      <li>
        <div className="stack">
          <label>
            Step {step.step_number}
            <textarea value={instruction} onChange={(event) => setInstruction(event.target.value)} rows={3} required />
          </label>
          <label>
            Timer (minutes, optional)
            <input
              type="number"
              min={1}
              step={1}
              inputMode="numeric"
              value={timerMinutes}
              onChange={(event) => setTimerMinutes(event.target.value)}
              placeholder="e.g. 5"
            />
          </label>
          <p className="muted">Leave empty if this step has no countdown timer in cooking mode.</p>
          <div className="row-actions">
            <button type="button" className="button" disabled={submitting} onClick={() => void handleSave()}>
              Save
            </button>
            <button type="button" className="button button-secondary" onClick={() => setEditing(false)}>
              Cancel
            </button>
          </div>
        </div>
      </li>
    );
  }

  return (
    <li className="list-item-row">
      <span>
        {step.step_number}. {step.instruction}
        {timerLabel ? <span className="muted"> · {timerLabel}</span> : null}
      </span>
      <div className="row-actions">
        <button type="button" className="button button-secondary" onClick={() => setEditing(true)}>
          Edit
        </button>
        <button type="button" className="button button-danger" onClick={() => void handleDelete()}>
          Delete
        </button>
      </div>
    </li>
  );
}

function AddStepEditor({
  recipeId,
  nextStep,
  accessToken,
  onAdded,
  onCancel,
}: {
  recipeId: number;
  nextStep: number;
  accessToken: string;
  onAdded: () => void;
  onCancel: () => void;
}) {
  const [instruction, setInstruction] = useState("");
  const [timerMinutes, setTimerMinutes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleAdd() {
    if (!instruction.trim()) {
      return;
    }
    setSubmitting(true);
    try {
      await createRecipeStep(accessToken, recipeId, {
        step_number: nextStep,
        instruction: instruction.trim(),
        timer_seconds: timerSecondsFromMinutesInput(timerMinutes),
      });
      onAdded();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="stack">
      <label>
        Step {nextStep}
        <textarea value={instruction} onChange={(event) => setInstruction(event.target.value)} rows={3} required />
      </label>
      <label>
        Timer (minutes, optional)
        <input
          type="number"
          min={1}
          step={1}
          inputMode="numeric"
          value={timerMinutes}
          onChange={(event) => setTimerMinutes(event.target.value)}
          placeholder="e.g. 5"
        />
      </label>
      <div className="row-actions">
        <button type="button" className="button" disabled={submitting} onClick={() => void handleAdd()}>
          Add step
        </button>
        <button type="button" className="button button-secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  );
}

function IngredientEditorRow({
  item,
  ingredientName,
  units,
  accessToken,
  onChanged,
}: {
  item: RecipeIngredient;
  ingredientName: string;
  units: Unit[];
  accessToken: string;
  onChanged: () => void;
}) {
  const unitSymbol = units.find((unit) => unit.id === item.unit_id)?.symbol;
  const [editing, setEditing] = useState(false);
  const [quantity, setQuantity] = useState(item.quantity ?? "");
  const [unitId, setUnitId] = useState<number | "">(item.unit_id ?? "");
  const [optional, setOptional] = useState(item.optional);
  const [submitting, setSubmitting] = useState(false);

  async function handleSave() {
    setSubmitting(true);
    try {
      await updateRecipeIngredient(accessToken, item.id, {
        quantity: quantity || null,
        unit_id: unitId === "" ? null : unitId,
        optional,
      });
      setEditing(false);
      onChanged();
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete() {
    setSubmitting(true);
    try {
      await deleteRecipeIngredient(accessToken, item.id);
      onChanged();
    } finally {
      setSubmitting(false);
    }
  }

  if (editing) {
    return (
      <div className="ingredient-row stack">
        <strong>{ingredientName}</strong>
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
        <label className="checkbox-pill">
          <input type="checkbox" checked={optional} onChange={(event) => setOptional(event.target.checked)} />
          Optional
        </label>
        <div className="row-actions">
          <button type="button" className="button" disabled={submitting} onClick={() => void handleSave()}>
            Save
          </button>
          <button type="button" className="button button-secondary" onClick={() => setEditing(false)}>
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="ingredient-row list-item-row">
      <span>
        <strong>{ingredientName}</strong>
        {item.quantity ? ` — ${item.quantity}${unitSymbol ? ` ${unitSymbol}` : ""}` : ""}
        {item.optional ? " (optional)" : ""}
      </span>
      <div className="row-actions">
        <button type="button" className="button button-secondary" onClick={() => setEditing(true)}>
          Edit
        </button>
        <button type="button" className="button button-danger" onClick={() => void handleDelete()}>
          Delete
        </button>
      </div>
    </div>
  );
}

function AddIngredientEditor({
  recipeId,
  accessToken,
  units,
  ingredientOptions,
  onAdded,
  onCancel,
}: {
  recipeId: number;
  accessToken: string;
  units: Unit[];
  ingredientOptions: string[];
  onAdded: () => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unitId, setUnitId] = useState<number | "">("");
  const [optional, setOptional] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function resolveOrCreateIngredient(proposedName: string): Promise<Ingredient> {
    const resolved = await resolveIngredient(accessToken, proposedName);
    if (resolved.status === "exact" && resolved.ingredient) {
      return resolved.ingredient;
    }
    if (resolved.status === "suggestions" && resolved.suggestions?.length) {
      const useSuggested = window.confirm(
        `No exact match for "${proposedName}". Use "${resolved.suggestions[0].display_name}" instead?`,
      );
      if (useSuggested) {
        return resolved.suggestions[0];
      }
    }
    const createNew = window.confirm(`Create new ingredient "${proposedName}"?`);
    if (!createNew) {
      throw new Error("Ingredient selection cancelled");
    }
    return confirmIngredient(accessToken, {
      action: "create",
      proposed_name: proposedName,
      display_name: proposedName,
    });
  }

  async function handleAdd() {
    if (!name.trim()) {
      return;
    }
    setSubmitting(true);
    setMessage(null);
    try {
      const ingredient = await resolveOrCreateIngredient(name.trim());
      await addRecipeIngredient(accessToken, recipeId, {
        ingredient_id: ingredient.id,
        quantity: quantity || null,
        unit_id: unitId === "" ? null : unitId,
        optional,
      });
      onAdded();
    } catch (err) {
      if (err instanceof Error && err.message === "Ingredient selection cancelled") {
        return;
      }
      setMessage(err instanceof ApiError ? err.message : err instanceof Error ? err.message : "Failed to add ingredient");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="ingredient-row stack">
      <label>
        Ingredient
        <input list="ingredient-options" value={name} onChange={(event) => setName(event.target.value)} required />
        <datalist id="ingredient-options">
          {ingredientOptions.map((option) => (
            <option key={option} value={option} />
          ))}
        </datalist>
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
      <label className="checkbox-pill">
        <input type="checkbox" checked={optional} onChange={(event) => setOptional(event.target.checked)} />
        Optional
      </label>
      {message ? <p className="error">{message}</p> : null}
      <div className="row-actions">
        <button type="button" className="button" disabled={submitting} onClick={() => void handleAdd()}>
          Add ingredient
        </button>
        <button type="button" className="button button-secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  );
}
