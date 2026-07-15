import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  createDish,
  fetchDish,
  fetchTags,
  updateDish,
  type Dish,
  type DishInput,
  type SeasonalityInput,
  type Tag,
} from "../../api/catalog";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { Button, DisclosureSection, FormSection, FormStickyActions, PageShell } from "../../components/ui";
import { useFormSaveState } from "../../lib/useFormSaveState";
import { useAuth } from "../auth/AuthContext";
import {
  MEAL_COMPOSITION_OPTIONS,
  MONTH_OPTIONS,
  SEASONALITY_MODE_OPTIONS,
  SIMPLE_DISH_PART_OPTIONS,
  STATUS_OPTIONS,
  STYLE_OPTIONS,
  curatedDishTagIds,
  findTagId,
} from "./classification";
import { InferredTraitsSummary } from "./InferredTraitsSummary";

const emptySeasonality: SeasonalityInput = {
  seasonality_mode: "all_year",
  preferred_months: [],
};

const emptyForm: DishInput = {
  name: "",
  description: "",
  image_url: "",
  course: null,
  meal_composition: "main_dish",
  simple_dish_part: null,
  status: "active",
  suitable_for_lunch: null,
  suitable_for_dinner: null,
  weekday_friendly: null,
  leftovers_possible: null,
  freezer_friendly: null,
  kids_friendly: null,
  notes: "",
  tag_ids: [],
  seasonality: emptySeasonality,
};

function dishToForm(dish: Dish): DishInput {
  return {
    name: dish.name,
    description: dish.description,
    image_url: dish.image_url ?? "",
    course: dish.course,
    meal_composition: dish.meal_composition,
    simple_dish_part: dish.simple_dish_part,
    status: dish.status,
    suitable_for_lunch: dish.suitable_for_lunch,
    suitable_for_dinner: dish.suitable_for_dinner,
    weekday_friendly: dish.weekday_friendly,
    leftovers_possible: dish.leftovers_possible,
    freezer_friendly: dish.freezer_friendly,
    kids_friendly: dish.kids_friendly,
    notes: dish.notes,
    tag_ids: dish.tag_ids,
    seasonality: dish.seasonality
      ? {
          seasonality_mode: dish.seasonality.seasonality_mode,
          preferred_months: dish.seasonality.preferred_months,
        }
      : emptySeasonality,
  };
}

function deriveCourse(
  mealComposition: DishInput["meal_composition"],
  existing: Dish["course"] | null | undefined,
): Dish["course"] | null {
  if (mealComposition === "dessert") {
    return "dessert";
  }
  if (existing === "starter") {
    return "starter";
  }
  return "main";
}

function toggleFamilyTag(tagIds: number[], tags: Tag[], family: string, name: string): number[] {
  const tagId = findTagId(tags, family, name);
  if (!tagId) {
    return tagIds;
  }
  const selected = new Set(tagIds);
  if (selected.has(tagId)) {
    selected.delete(tagId);
  } else {
    selected.add(tagId);
  }
  return [...selected];
}

function MultiSelectPills({
  options,
  family,
  tags,
  selectedIds,
  onChange,
}: {
  options: ReadonlyArray<{ value: string; label: string }>;
  family: string;
  tags: Tag[];
  selectedIds: number[];
  onChange: (next: number[]) => void;
}) {
  return (
    <div className="tag-grid">
      {options.map((option) => {
        const tagId = findTagId(tags, family, option.value);
        if (!tagId) {
          return null;
        }
        return (
          <label key={option.value} className="checkbox-pill">
            <input
              type="checkbox"
              checked={selectedIds.includes(tagId)}
              onChange={() => onChange(toggleFamilyTag(selectedIds, tags, family, option.value))}
            />
            {option.label}
          </label>
        );
      })}
    </div>
  );
}

function MonthPicker({
  label,
  selected,
  onChange,
}: {
  label: string;
  selected: number[];
  onChange: (months: number[]) => void;
}) {
  return (
    <fieldset>
      <legend>{label}</legend>
      <div className="tag-grid">
        {MONTH_OPTIONS.map((month) => (
          <label key={month.value} className="checkbox-pill">
            <input
              type="checkbox"
              checked={selected.includes(month.value)}
              onChange={() => {
                const next = new Set(selected);
                if (next.has(month.value)) {
                  next.delete(month.value);
                } else {
                  next.add(month.value);
                }
                onChange([...next].sort((a, b) => a - b));
              }}
            />
            {month.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function DishEditPage() {
  const { dishId } = useParams();
  const isNew = !dishId;
  const navigate = useNavigate();
  const { accessToken, isHouseholdAdmin } = useAuth();
  const [form, setForm] = useState<DishInput>(emptyForm);
  const [dish, setDish] = useState<Dish | null>(null);
  const [tags, setTags] = useState<Tag[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!isNew);
  const [submitting, setSubmitting] = useState(false);
  const { status: saveStatus, setBaseline } = useFormSaveState(form, { saving: submitting, error });

  useEffect(() => {
    if (isNew) {
      setBaseline(emptyForm);
    }
  }, [isNew, setBaseline]);

  useEffect(() => {
    if (dish) {
      setBaseline(dishToForm(dish));
    }
  }, [dish, setBaseline]);

  useEffect(() => {
    if (!isHouseholdAdmin) {
      navigate("/dishes", { replace: true });
    }
  }, [isHouseholdAdmin, navigate]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    fetchTags(accessToken)
      .then(setTags)
      .catch(() => setTags([]));
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken || isNew || !dishId) {
      return;
    }
    let cancelled = false;
    fetchDish(accessToken, Number(dishId))
      .then((loaded) => {
        if (!cancelled) {
          setDish(loaded);
          setForm(dishToForm(loaded));
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load dish");
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
  }, [accessToken, dishId, isNew]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const payload: DishInput = {
        ...form,
        description: form.description || null,
        image_url: form.image_url || null,
        notes: form.notes || null,
        course: deriveCourse(form.meal_composition, dish?.course),
        meal_composition: form.meal_composition ?? "main_dish",
        simple_dish_part:
          form.meal_composition === "simple_dish" ? form.simple_dish_part ?? null : null,
        tag_ids: curatedDishTagIds(form.tag_ids ?? [], tags),
        seasonality: {
          seasonality_mode: form.seasonality?.seasonality_mode ?? "all_year",
          preferred_months:
            form.seasonality?.seasonality_mode === "seasonal"
              ? (form.seasonality?.preferred_months ?? [])
              : [],
        },
      };
      if (isNew) {
        const created = await createDish(accessToken, payload);
        navigate(`/dishes/${created.id}`);
      } else {
        await updateDish(accessToken, Number(dishId), payload);
        navigate(`/dishes/${dishId}`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save dish");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="catalog-edit-page">
        <PageShell title="Edit dish" loading loadingMessage="Loading dish…" />
      </div>
    );
  }

  return (
    <div className="catalog-edit-page">
      <PageShell
        title={isNew ? "New dish" : "Edit dish"}
        breadcrumbLabels={
          isNew
            ? undefined
            : { dishId: dish?.id ?? Number(dishId), dishName: dish?.name ?? form.name }
        }
        actions={
          <ButtonLink to={isNew ? "/dishes" : `/dishes/${dishId}`} variant="secondary">
            Cancel
          </ButtonLink>
        }
      />
      <form onSubmit={handleSubmit} className="catalog-form">
        <FormSection title="Basic info">
          <div className="stack">
            <label>
              Name
              <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
            </label>
            <label>
              Description
              <textarea
                value={form.description ?? ""}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                rows={3}
              />
            </label>
            <label>
              Image URL
              <input
                type="url"
                value={form.image_url ?? ""}
                onChange={(event) => setForm({ ...form, image_url: event.target.value })}
                placeholder="Optional link to a dish photo"
              />
            </label>
            <div className="grid-2">
              <label>
                Meal composition
                <select
                  value={form.meal_composition ?? "main_dish"}
                  onChange={(event) => {
                    const meal_composition = event.target.value as Dish["meal_composition"];
                    setForm({
                      ...form,
                      meal_composition,
                      simple_dish_part:
                        meal_composition === "simple_dish" ? form.simple_dish_part : null,
                    });
                  }}
                >
                  {MEAL_COMPOSITION_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Status
                <select
                  value={form.status ?? "active"}
                  onChange={(event) =>
                    setForm({ ...form, status: event.target.value as Dish["status"] })
                  }
                >
                  {STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {form.meal_composition === "simple_dish" ? (
              <label>
                Simple dish part
                <select
                  value={form.simple_dish_part ?? ""}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      simple_dish_part: (event.target.value || null) as Dish["simple_dish_part"],
                    })
                  }
                  required
                >
                  <option value="" disabled>
                    Select part…
                  </option>
                  {SIMPLE_DISH_PART_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <p className="muted field-hint">
              Controls planner slots: one main dish, or two simple dishes (centerpiece + side).
              Desserts are manual-only.
            </p>
          </div>
        </FormSection>

        <div className="catalog-form-disclosure-stack">
          <DisclosureSection title="Planning & style">
            <div className="stack">
              <FormSection
                title="Curated style (optional)"
                description="Only for styles the planner cannot infer from ingredients, such as soup."
              >
                <MultiSelectPills
                  options={STYLE_OPTIONS}
                  family="style"
                  tags={tags}
                  selectedIds={form.tag_ids ?? []}
                  onChange={(tag_ids) => setForm({ ...form, tag_ids })}
                />
              </FormSection>

              <FormSection title="Planning profile">
                <div className="stack">
                  <div className="tag-grid">
                    <label className="checkbox-pill">
                      <input
                        type="checkbox"
                        checked={form.suitable_for_lunch === true}
                        onChange={(event) =>
                          setForm({ ...form, suitable_for_lunch: event.target.checked ? true : null })
                        }
                      />
                      Suitable for lunch
                    </label>
                    <label className="checkbox-pill">
                      <input
                        type="checkbox"
                        checked={form.suitable_for_dinner === true}
                        onChange={(event) =>
                          setForm({ ...form, suitable_for_dinner: event.target.checked ? true : null })
                        }
                      />
                      Suitable for dinner
                    </label>
                    <label className="checkbox-pill">
                      <input
                        type="checkbox"
                        checked={form.weekday_friendly === true}
                        onChange={(event) =>
                          setForm({ ...form, weekday_friendly: event.target.checked ? true : null })
                        }
                      />
                      Weekday-friendly
                    </label>
                    <label className="checkbox-pill">
                      <input
                        type="checkbox"
                        checked={form.leftovers_possible === true}
                        onChange={(event) =>
                          setForm({ ...form, leftovers_possible: event.target.checked ? true : null })
                        }
                      />
                      Leftovers possible
                    </label>
                    <label className="checkbox-pill">
                      <input
                        type="checkbox"
                        checked={form.kids_friendly === true}
                        onChange={(event) =>
                          setForm({ ...form, kids_friendly: event.target.checked ? true : null })
                        }
                      />
                      Kids-friendly
                    </label>
                  </div>
                  <label>
                    Freezer-friendly
                    <select
                      value={form.freezer_friendly === null ? "" : form.freezer_friendly ? "yes" : "no"}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          freezer_friendly:
                            event.target.value === "" ? null : event.target.value === "yes",
                        })
                      }
                    >
                      <option value="">Unknown</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </label>
                </div>
              </FormSection>

              <FormSection title="Seasonality">
                <div className="stack">
                  <label>
                    Mode
                    <select
                      value={form.seasonality?.seasonality_mode ?? "all_year"}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          seasonality: {
                            seasonality_mode: event.target.value,
                            preferred_months:
                              event.target.value === "seasonal"
                                ? (form.seasonality?.preferred_months ?? [])
                                : [],
                          },
                        })
                      }
                    >
                      {SEASONALITY_MODE_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  {form.seasonality?.seasonality_mode === "seasonal" ? (
                    <MonthPicker
                      label="Preferred months"
                      selected={form.seasonality?.preferred_months ?? []}
                      onChange={(preferred_months) =>
                        setForm({ ...form, seasonality: { seasonality_mode: "seasonal", preferred_months } })
                      }
                    />
                  ) : null}
                </div>
              </FormSection>
            </div>
          </DisclosureSection>

          {!isNew ? (
            <DisclosureSection title="Inferred from main recipe">
              <InferredTraitsSummary traits={dish?.computed_traits_json} />
            </DisclosureSection>
          ) : null}
        </div>

        <FormStickyActions saveStatus={saveStatus} saveErrorMessage={error}>
          <Button type="submit" loading={submitting}>
            Save dish
          </Button>
        </FormStickyActions>
      </form>
    </div>
  );
}
