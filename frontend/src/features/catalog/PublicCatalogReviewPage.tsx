import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import * as catalogApi from "../../api/publicCatalog";
import type { PublicRecipePlatform } from "../../api/publicCatalog";
import { Button, Card, EmptyState, MetadataList, PageShell, StatusBadge, TechnicalValue } from "../../components/ui";
import type { StatusBadgeVariant } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";

export const RECIPE_REVIEW_PATH = "/catalog/review";

type SnapshotDish = {
  name?: string;
  description?: string | null;
  meal_composition?: string | null;
  simple_dish_part?: string | null;
  course?: string | null;
  suitable_for_lunch?: boolean | null;
  suitable_for_dinner?: boolean | null;
  weekday_friendly?: boolean | null;
  leftovers_possible?: boolean | null;
  freezer_friendly?: boolean | null;
  kids_friendly?: boolean | null;
  notes?: string | null;
};

type SnapshotRecipe = {
  variant_name?: string;
  description?: string | null;
  recipe_type?: string | null;
  servings?: number | null;
  prep_time_minutes?: number | null;
  cook_time_minutes?: number | null;
  difficulty?: string | null;
  source_url?: string | null;
  notes?: string | null;
  is_main?: boolean;
  is_thermomix?: boolean;
  thermomix_model?: string | null;
};

type SnapshotIngredient = {
  ingredient_display_name?: string;
  ingredient_canonical_name?: string;
  quantity?: string | null;
  unit_symbol?: string | null;
  unit_name?: string | null;
  optional?: boolean;
  notes?: string | null;
};

type SnapshotStep = {
  step_number?: number;
  instruction?: string;
  duration_seconds?: number | null;
  temperature?: string | null;
  timer_seconds?: number | null;
};

function statusVariant(status: PublicRecipePlatform["status"]): StatusBadgeVariant {
  switch (status) {
    case "public":
      return "success";
    case "rejected":
    case "withdrawn":
    case "delisted":
      return "danger";
    case "submitted":
      return "warning";
    default:
      return "default";
  }
}

function formatLabel(value: string | null | undefined): string {
  if (!value) {
    return "Not set";
  }
  return value.replace(/_/g, " ");
}

function formatFlag(value: boolean | null | undefined): string | null {
  if (value == null) {
    return null;
  }
  return value ? "Yes" : "No";
}

function snapshotSections(snapshot: Record<string, unknown> | null | undefined) {
  const dish = (snapshot?.dish ?? {}) as SnapshotDish;
  const recipe = (snapshot?.recipe ?? {}) as SnapshotRecipe;
  const ingredients = (snapshot?.ingredients as SnapshotIngredient[] | undefined) ?? [];
  const steps = (snapshot?.steps as SnapshotStep[] | undefined) ?? [];
  return { dish, recipe, ingredients, steps };
}

export function PublicCatalogReviewQueuePage() {
  const { accessToken } = useAuth();
  const [items, setItems] = useState<PublicRecipePlatform[]>([]);
  const [statusFilter, setStatusFilter] = useState("submitted");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    setLoading(true);
    catalogApi
      .listPlatformPublicRecipes(accessToken, statusFilter || undefined)
      .then((data) => {
        if (!cancelled) {
          setItems(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setItems([]);
          setError(err instanceof ApiError ? err.message : "Failed to load recipe review queue");
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
  }, [accessToken, statusFilter]);

  return (
    <div className="catalog-page">
      <PageShell
        title="Recipe review"
        subtitle="Inspect publication snapshots, then approve, reject, or delist."
        loading={loading}
        loadingMessage="Loading queue…"
      >
        <label className="form-field">
          <span>Status</span>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="submitted">Submitted</option>
            <option value="public">Public</option>
            <option value="rejected">Rejected</option>
            <option value="withdrawn">Withdrawn</option>
            <option value="delisted">Delisted</option>
            <option value="">All</option>
          </select>
        </label>
        {error ? <p className="form-error">{error}</p> : null}
        {!loading && items.length === 0 ? (
          <EmptyState title="No items" description="No publication requests match this filter." />
        ) : null}
        <ul className="catalog-list">
          {items.map((item) => (
            <li key={item.id}>
              <Link to={`${RECIPE_REVIEW_PATH}/${item.id}`} className="catalog-list-link">
                <strong>{item.title}</strong>
                <StatusBadge variant={statusVariant(item.status)}>{item.status}</StatusBadge>
                {item.description ? <span className="muted">{item.description}</span> : null}
              </Link>
            </li>
          ))}
        </ul>
      </PageShell>
    </div>
  );
}

export function PublicCatalogReviewDetailPage() {
  const { publicRecipeId } = useParams();
  const { accessToken } = useAuth();
  const [item, setItem] = useState<PublicRecipePlatform | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewNote, setReviewNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    if (!accessToken || !publicRecipeId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await catalogApi.getPlatformPublicRecipe(accessToken, publicRecipeId);
      setItem(data);
      setError(null);
    } catch (err) {
      setItem(null);
      setError(err instanceof ApiError ? err.message : "Failed to load publication request");
    } finally {
      setLoading(false);
    }
  }, [accessToken, publicRecipeId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runAction(action: "approve" | "reject" | "delist") {
    if (!accessToken || !publicRecipeId) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      if (action === "approve") {
        await catalogApi.approvePublicRecipe(accessToken, publicRecipeId, reviewNote || undefined);
      } else if (action === "reject") {
        await catalogApi.rejectPublicRecipe(accessToken, publicRecipeId, reviewNote);
      } else {
        await catalogApi.delistPublicRecipe(accessToken, publicRecipeId, reviewNote);
      }
      setReviewNote("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Review action failed");
    } finally {
      setSubmitting(false);
    }
  }

  function onApprove(event: FormEvent) {
    event.preventDefault();
    void runAction("approve");
  }

  if (loading) {
    return (
      <div className="catalog-page">
        <PageShell title="Recipe review" loading loadingMessage="Loading…" />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="catalog-page">
        <EmptyState
          title="Not found"
          description={error ?? "Publication request not found."}
          action={
            <Link to={RECIPE_REVIEW_PATH} className="button button-secondary">
              Back to queue
            </Link>
          }
        />
      </div>
    );
  }

  const { dish, recipe, ingredients, steps } = snapshotSections(item.snapshot);
  const dishTitle = dish.name || item.title;
  const dishDescription = dish.description ?? item.description;
  const orderedSteps = steps
    .slice()
    .sort((a, b) => (a.step_number ?? 0) - (b.step_number ?? 0));

  const dishMeta = [
    { label: "Meal composition", value: formatLabel(dish.meal_composition) },
    { label: "Simple dish part", value: formatLabel(dish.simple_dish_part) },
    { label: "Course", value: formatLabel(dish.course) },
    { label: "Suitable for lunch", value: formatFlag(dish.suitable_for_lunch) },
    { label: "Suitable for dinner", value: formatFlag(dish.suitable_for_dinner) },
    { label: "Weekday friendly", value: formatFlag(dish.weekday_friendly) },
    { label: "Leftovers possible", value: formatFlag(dish.leftovers_possible) },
    { label: "Freezer friendly", value: formatFlag(dish.freezer_friendly) },
    { label: "Kids friendly", value: formatFlag(dish.kids_friendly) },
  ].filter((row) => row.value != null) as { label: string; value: string }[];

  const recipeMeta = [
    { label: "Variant", value: recipe.variant_name || "Not set" },
    { label: "Recipe type", value: formatLabel(recipe.recipe_type) },
    { label: "Servings", value: recipe.servings != null ? String(recipe.servings) : "Not set" },
    {
      label: "Prep / cook",
      value:
        recipe.prep_time_minutes != null || recipe.cook_time_minutes != null
          ? `${recipe.prep_time_minutes ?? "—"} / ${recipe.cook_time_minutes ?? "—"} min`
          : "Not set",
    },
    { label: "Difficulty", value: formatLabel(recipe.difficulty) },
    { label: "Main recipe", value: formatFlag(recipe.is_main) ?? "Not set" },
    {
      label: "Thermomix",
      value: recipe.is_thermomix
        ? recipe.thermomix_model
          ? `Yes (${recipe.thermomix_model})`
          : "Yes"
        : formatFlag(recipe.is_thermomix) ?? "Not set",
    },
  ];

  return (
    <div className="catalog-page">
      <PageShell
        title={dishTitle}
        subtitle={
          <>
            <StatusBadge variant={statusVariant(item.status)}>{item.status}</StatusBadge>
            {item.latest_version ? (
              <span className="muted"> · Version {item.latest_version.version_number}</span>
            ) : null}
          </>
        }
        actions={
          <Link to={RECIPE_REVIEW_PATH} className="button button-secondary">
            Back to queue
          </Link>
        }
      >
        {error ? <p className="form-error">{error}</p> : null}

        <Card density="comfortable">
          <h2 className="catalog-section-title">Publication snapshot</h2>
          {dishDescription ? <p>{dishDescription}</p> : <p className="muted">No description.</p>}
          {recipe.description && recipe.description !== dishDescription ? (
            <p className="muted">Recipe: {recipe.description}</p>
          ) : null}
        </Card>

        <Card density="comfortable">
          <h2 className="catalog-section-title">Dish</h2>
          <MetadataList items={dishMeta} />
          {dish.notes ? <p className="muted">Notes: {dish.notes}</p> : null}
        </Card>

        <Card density="comfortable">
          <h2 className="catalog-section-title">Recipe</h2>
          <MetadataList items={recipeMeta} />
          {recipe.source_url ? (
            <p>
              <span className="muted">Source URL: </span>
              <a href={recipe.source_url} target="_blank" rel="noreferrer">
                {recipe.source_url}
              </a>
            </p>
          ) : null}
          {recipe.notes ? <p className="muted">Notes: {recipe.notes}</p> : null}
        </Card>

        <Card density="comfortable">
          <h2 className="catalog-section-title">Ingredients</h2>
          {ingredients.length === 0 ? (
            <p className="muted">No ingredients in this snapshot.</p>
          ) : (
            <ul>
              {ingredients.map((ingredient, index) => {
                const name =
                  ingredient.ingredient_display_name ||
                  ingredient.ingredient_canonical_name ||
                  "Ingredient";
                const qty = ingredient.quantity ? `${ingredient.quantity} ` : "";
                const unit = ingredient.unit_symbol
                  ? `${ingredient.unit_symbol} `
                  : ingredient.unit_name
                    ? `${ingredient.unit_name} `
                    : "";
                return (
                  <li key={`${name}-${index}`}>
                    {qty}
                    {unit}
                    {name}
                    {ingredient.optional ? " (optional)" : ""}
                    {ingredient.notes ? ` — ${ingredient.notes}` : ""}
                  </li>
                );
              })}
            </ul>
          )}
        </Card>

        <Card density="comfortable">
          <h2 className="catalog-section-title">Steps</h2>
          {orderedSteps.length === 0 ? (
            <p className="muted">No steps in this snapshot.</p>
          ) : (
            <ol>
              {orderedSteps.map((step, index) => (
                <li key={`${step.step_number ?? index}`}>
                  {step.instruction ?? "Step"}
                  {step.timer_seconds != null || step.duration_seconds != null || step.temperature ? (
                    <span className="muted">
                      {" "}
                      (
                      {[
                        step.temperature ? step.temperature : null,
                        step.timer_seconds != null ? `${step.timer_seconds}s timer` : null,
                        step.duration_seconds != null ? `${step.duration_seconds}s` : null,
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                      )
                    </span>
                  ) : null}
                </li>
              ))}
            </ol>
          )}
        </Card>

        <Card density="comfortable">
          <h2 className="catalog-section-title">Moderation</h2>
          {item.review_note ? <p className="muted">Previous note: {item.review_note}</p> : null}
          <label className="form-field">
            <span>Review note</span>
            <textarea
              value={reviewNote}
              onChange={(event) => setReviewNote(event.target.value)}
              rows={4}
              placeholder="Required for reject and delist"
            />
          </label>
          <div className="catalog-detail-actions">
            {item.status === "submitted" ? (
              <>
                <Button disabled={submitting} onClick={onApprove}>
                  Approve
                </Button>
                <Button
                  variant="secondary"
                  disabled={submitting || !reviewNote.trim()}
                  onClick={() => void runAction("reject")}
                >
                  Reject
                </Button>
              </>
            ) : null}
            {item.status === "public" ? (
              <Button
                variant="secondary"
                disabled={submitting || !reviewNote.trim()}
                onClick={() => void runAction("delist")}
              >
                Delist
              </Button>
            ) : null}
          </div>
        </Card>

        <Card density="comfortable">
          <h2 className="catalog-section-title">Technical metadata</h2>
          <TechnicalValue label="Public recipe id" value={item.id} />
          <TechnicalValue label="Originating household" value={item.originating_household_id} />
          <TechnicalValue label="Originating dish id" value={String(item.originating_dish_id)} />
          <TechnicalValue label="Originating recipe id" value={String(item.originating_recipe_id)} />
          <TechnicalValue label="Submitted by" value={item.submitted_by_user_id} />
          {item.reviewed_by_user_id ? (
            <TechnicalValue label="Reviewed by" value={item.reviewed_by_user_id} />
          ) : null}
          {item.latest_version ? (
            <TechnicalValue label="Latest version id" value={item.latest_version.id} />
          ) : null}
        </Card>
      </PageShell>
    </div>
  );
}
