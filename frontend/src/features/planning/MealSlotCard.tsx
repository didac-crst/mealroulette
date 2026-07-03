import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import type { Dish, Recipe } from "../../api/catalog";
import { fetchRecipes } from "../../api/catalog";
import { ApiError } from "../../api/client";
import {
  fetchMealRating,
  lockMealPlanItem,
  markMealPlanItemAteLeftovers,
  markMealPlanItemEaten,
  resetMealPlanItemStatus,
  skipMealPlanItem,
  unlockMealPlanItem,
  updateMealPlanItem,
  upsertMealRating,
  type MealPlanItem,
} from "../../api/planning";
import {
  formatLeftoverSourceOption,
  formatReviewStatus,
  formatSlotLabel,
  formatStatus,
  isFutureMealDate,
  leftoverSourceLabel,
  reviewStatusClassName,
  showLeftoverSourcePicker,
  showLeftoverSourceSummary,
  showReviewExecutionActions,
  showReviewRating,
  showSkipSummary,
  showUndoStatus,
  statusClassName,
} from "./planFormat";
import { StarRating } from "./StarRating";

type Props = {
  item: MealPlanItem;
  dishes: Dish[];
  leftoverSources: MealPlanItem[];
  sourceLookupItems?: MealPlanItem[];
  accessToken: string;
  mode: "plan" | "review";
  onChanged: (item: MealPlanItem) => void;
  onError: (message: string) => void;
};

export function MealSlotCard({
  item,
  dishes,
  leftoverSources,
  sourceLookupItems,
  accessToken,
  mode,
  onChanged,
  onError,
}: Props) {
  const [busy, setBusy] = useState(false);
  const [rating, setRating] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [skipReason, setSkipReason] = useState(item.skip_reason ?? "");
  const [skipComment, setSkipComment] = useState(item.skip_comment ?? "");
  const [skipFormOpen, setSkipFormOpen] = useState(false);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [leftoverSourceId, setLeftoverSourceId] = useState(
    item.leftover_source_item_id ? String(item.leftover_source_item_id) : "",
  );
  const [ratingMessage, setRatingMessage] = useState<string | null>(null);

  const isFuture = isFutureMealDate(item.date);
  const sourceItems = sourceLookupItems ?? leftoverSources;
  const isReviewed = mode === "review" && item.status !== "planned";
  const statusLabel = mode === "review" ? formatReviewStatus(item) : formatStatus(item.status);
  const statusClass = mode === "review" ? reviewStatusClassName(item) : statusClassName(item.status);
  const showUndo = mode === "review" && showUndoStatus(item);

  useEffect(() => {
    if (!item.dish_id) {
      setRecipes([]);
      return;
    }
    let cancelled = false;
    fetchRecipes(accessToken, item.dish_id)
      .then((data) => {
        if (!cancelled) {
          setRecipes(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRecipes([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, item.dish_id]);

  useEffect(() => {
    if (!showReviewRating(item)) {
      return;
    }
    let cancelled = false;
    fetchMealRating(accessToken, item.id)
      .then((existing) => {
        if (cancelled) {
          return;
        }
        setRating(existing?.rating ?? null);
        setComment(existing?.comment ?? "");
      })
      .catch(() => {
        if (!cancelled) {
          setRating(null);
          setComment("");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, item.id, item.status]);

  useEffect(() => {
    setLeftoverSourceId(item.leftover_source_item_id ? String(item.leftover_source_item_id) : "");
    setSkipReason(item.skip_reason ?? "");
    setSkipComment(item.skip_comment ?? "");
  }, [item.leftover_source_item_id, item.skip_reason, item.skip_comment]);

  useEffect(() => {
    setSkipFormOpen(false);
  }, [item.status]);

  async function run(action: () => Promise<MealPlanItem>) {
    setBusy(true);
    try {
      const updated = await action();
      onChanged(updated);
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleDishChange(dishId: string) {
    if (dishId === "") {
      await run(() => updateMealPlanItem(accessToken, item.id, { dish_id: null }));
      return;
    }
    await run(() => updateMealPlanItem(accessToken, item.id, { dish_id: Number(dishId) }));
  }

  async function handleRecipeChange(recipeId: string) {
    if (!item.dish_id) {
      return;
    }
    await run(() =>
      updateMealPlanItem(accessToken, item.id, {
        dish_id: item.dish_id,
        recipe_id: recipeId === "" ? null : Number(recipeId),
      }),
    );
  }

  const cardClass = [
    "meal-slot-card",
    isFuture && mode === "review" ? "meal-slot-card-future" : "",
    isReviewed ? "meal-slot-card-reviewed" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <article className={cardClass}>
      <div className="meal-slot-header">
        <div>
          <p className="meal-slot-label">{formatSlotLabel(item.meal_slot)}</p>
          {item.dish_id ? (
            <Link to={`/dishes/${item.dish_id}`} className="meal-slot-dish">
              {item.dish_name}
            </Link>
          ) : (
            <p className="muted meal-slot-empty">No dish assigned</p>
          )}
          {item.recipe_variant_name && !(mode === "plan" && item.dish_id && recipes.length > 0) ? (
            <p className="muted meal-slot-recipe">{item.recipe_variant_name}</p>
          ) : null}
        </div>
        <div className="meal-slot-header-aside">
          <span className={statusClass}>{statusLabel}</span>
          {showUndo ? (
            <button
              type="button"
              className="button button-undo"
              disabled={busy}
              onClick={() => void run(() => resetMealPlanItemStatus(accessToken, item.id))}
            >
              Undo status
            </button>
          ) : null}
        </div>
      </div>

      {mode === "plan" ? (
        <>
          <label className="meal-slot-assign">
            <span className="muted">Assign dish</span>
            <select
              value={item.dish_id ?? ""}
              disabled={busy || item.is_locked}
              onChange={(event) => void handleDishChange(event.target.value)}
            >
              <option value="">—</option>
              {dishes.map((dish) => (
                <option key={dish.id} value={dish.id}>
                  {dish.name}
                </option>
              ))}
            </select>
          </label>

          {item.dish_id && recipes.length > 0 ? (
            <label className="meal-slot-assign">
              <span className="muted">Recipe variant</span>
              <select
                value={item.recipe_id ?? ""}
                disabled={busy || item.is_locked}
                onChange={(event) => void handleRecipeChange(event.target.value)}
              >
                {recipes.map((recipe) => (
                  <option key={recipe.id} value={recipe.id}>
                    {recipe.variant_name}
                    {recipe.is_main ? " (main)" : ""}
                  </option>
                ))}
              </select>
            </label>
          ) : item.dish_id && recipes.length === 0 && !busy ? (
            <p className="muted meal-slot-recipe">No recipe for this dish yet.</p>
          ) : null}

          <div className="meal-slot-actions">
            <button
              type="button"
              className="button button-secondary"
              disabled={busy || (!item.is_locked && !item.dish_id)}
              onClick={() =>
                void run(() =>
                  item.is_locked
                    ? unlockMealPlanItem(accessToken, item.id)
                    : lockMealPlanItem(accessToken, item.id),
                )
              }
            >
              {item.is_locked ? "Unlock" : "Lock"}
            </button>
          </div>
        </>
      ) : null}

      {mode === "review" && isFuture ? (
        <p className="muted meal-slot-future-note">Future meal — review after it happens</p>
      ) : null}

      {mode === "review" && !isFuture ? (
        <>
          {showReviewExecutionActions(item) && !skipFormOpen ? (
            <div className="meal-slot-actions meal-slot-actions-primary">
              <button
                type="button"
                className="button button-secondary"
                disabled={busy || !item.dish_id}
                onClick={() => void run(() => markMealPlanItemEaten(accessToken, item.id))}
              >
                Ate as planned
              </button>
              <button
                type="button"
                className="button button-secondary"
                disabled={busy}
                onClick={() => setSkipFormOpen(true)}
              >
                Skipped
              </button>
              <button
                type="button"
                className="button button-secondary"
                disabled={busy}
                onClick={() => void run(() => markMealPlanItemAteLeftovers(accessToken, item.id))}
              >
                Ate leftovers
              </button>
            </div>
          ) : null}

          {showReviewExecutionActions(item) && skipFormOpen ? (
            <div className="meal-slot-review-panel stack">
              <p className="section-title">Mark as skipped</p>
              <label>
                Skip reason (optional)
                <input value={skipReason} onChange={(event) => setSkipReason(event.target.value)} />
              </label>
              <label>
                Skip comment (optional)
                <input value={skipComment} onChange={(event) => setSkipComment(event.target.value)} />
              </label>
              <div className="meal-slot-actions meal-slot-actions-primary">
                <button
                  type="button"
                  className="button"
                  disabled={busy}
                  onClick={() =>
                    void run(() =>
                      skipMealPlanItem(
                        accessToken,
                        item.id,
                        skipReason || undefined,
                        skipComment || undefined,
                      ),
                    )
                  }
                >
                  Save skip
                </button>
                <button
                  type="button"
                  className="button button-secondary"
                  disabled={busy}
                  onClick={() => {
                    setSkipFormOpen(false);
                    setSkipReason("");
                    setSkipComment("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : null}

          {showLeftoverSourcePicker(item) ? (
            <div className="meal-slot-review-panel stack">
              <p className="section-title">What did you eat?</p>
              <label className="meal-slot-assign">
                <span className="muted">Leftover from</span>
                <select
                  value={leftoverSourceId}
                  disabled={busy}
                  onChange={(event) => {
                    const value = event.target.value;
                    setLeftoverSourceId(value);
                    void run(() =>
                      updateMealPlanItem(accessToken, item.id, {
                        leftover_source_item_id: value ? Number(value) : null,
                      }),
                    );
                  }}
                >
                  <option value="">Unknown / same dish</option>
                  {leftoverSources.length > 0 ? (
                    <optgroup label="Recent eaten meals">
                      {leftoverSources.map((source) => (
                        <option key={source.id} value={source.id}>
                          {formatLeftoverSourceOption(source)}
                        </option>
                      ))}
                    </optgroup>
                  ) : null}
                </select>
              </label>
              <button
                type="button"
                className="button"
                disabled={busy}
                onClick={() =>
                  void run(() =>
                    updateMealPlanItem(accessToken, item.id, {
                      leftover_source_item_id: leftoverSourceId ? Number(leftoverSourceId) : null,
                    }),
                  )
                }
              >
                Done
              </button>
            </div>
          ) : null}

          {showLeftoverSourceSummary(item) ? (
            <p className="muted">
              Leftover from: {leftoverSourceLabel(item, sourceItems) ?? "Unknown / same dish"}
            </p>
          ) : null}

          {showSkipSummary(item) ? (
            <p className="muted">
              {item.skip_reason ? `Skip reason: ${item.skip_reason}` : "Skipped"}
              {item.skip_comment ? ` — ${item.skip_comment}` : ""}
            </p>
          ) : null}

          {showReviewRating(item) && item.dish_id ? (
            <div className="meal-slot-review-panel stack">
              <p className="section-title">Rate this meal</p>
              <StarRating value={rating} disabled={busy} onChange={setRating} />
              <label>
                Comment
                <input value={comment} onChange={(event) => setComment(event.target.value)} />
              </label>
              <button
                type="button"
                className="button"
                disabled={busy || rating === null}
                onClick={() => {
                  if (rating === null) {
                    return;
                  }
                  setBusy(true);
                  setRatingMessage(null);
                  upsertMealRating(accessToken, item.id, { rating, comment: comment || null })
                    .then((result) => {
                      setRatingMessage("Rating saved");
                      onChanged(result.item);
                    })
                    .catch((err) =>
                      onError(err instanceof ApiError ? err.message : "Failed to save rating"),
                    )
                    .finally(() => setBusy(false));
                }}
              >
                Save rating
              </button>
              {ratingMessage ? <p className="muted">{ratingMessage}</p> : null}
            </div>
          ) : null}
        </>
      ) : null}
    </article>
  );
}
