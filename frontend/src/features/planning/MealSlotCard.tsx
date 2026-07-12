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
  canRerollMeal,
  canSwapMeal,
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
  swappableMeals,
} from "./planFormat";
import { canOpenCookMode } from "./todayMeals";
import { SelectionReasons } from "./SelectionReasons";
import { StarRating } from "./StarRating";
import { SwapSlotDialog } from "./SwapSlotDialog";

type Props = {
  item: MealPlanItem;
  dishes: Dish[];
  planItems?: MealPlanItem[];
  leftoverSources: MealPlanItem[];
  sourceLookupItems?: MealPlanItem[];
  accessToken: string;
  mode: "plan" | "review" | "today";
  rouletteBusy?: boolean;
  cookRecipeId?: number | null;
  cookRecipesLoading?: boolean;
  reviewExpanded?: boolean;
  onReviewToggle?: () => void;
  onChanged: (item: MealPlanItem) => void;
  onError: (message: string) => void;
  onReroll?: (item: MealPlanItem) => void;
  onSwap?: (source: MealPlanItem, targetItemId: number) => void;
};

export function MealSlotCard({
  item,
  dishes,
  planItems = [],
  leftoverSources,
  sourceLookupItems,
  accessToken,
  mode,
  rouletteBusy = false,
  cookRecipeId = null,
  cookRecipesLoading = false,
  reviewExpanded = true,
  onReviewToggle,
  onChanged,
  onError,
  onReroll,
  onSwap,
}: Props) {
  const [busy, setBusy] = useState(false);
  const [swapOpen, setSwapOpen] = useState(false);
  const [rating, setRating] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [skipReason, setSkipReason] = useState(item.skip_reason ?? "");
  const [skipComment, setSkipComment] = useState(item.skip_comment ?? "");
  const [skipFormOpen, setSkipFormOpen] = useState(false);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [recipesLoading, setRecipesLoading] = useState(false);
  const [leftoverSourceId, setLeftoverSourceId] = useState(
    item.leftover_source_item_id ? String(item.leftover_source_item_id) : "",
  );
  const [ratingMessage, setRatingMessage] = useState<string | null>(null);

  const isFuture = isFutureMealDate(item.date);
  const sourceItems = sourceLookupItems ?? leftoverSources;
  const isReviewed = (mode === "review" || mode === "today") && item.status !== "planned";
  const statusLabel = mode === "review" || mode === "today" ? formatReviewStatus(item) : formatStatus(item.status);
  const statusClass =
    mode === "review" || mode === "today" ? reviewStatusClassName(item) : statusClassName(item.status);
  const showUndo = (mode === "review" || mode === "today") && showUndoStatus(item);
  const showTodayReviewPanel = mode !== "today" || reviewExpanded;
  const showReviewPanel =
    (mode === "review" && !isFuture) || (mode === "today" && showTodayReviewPanel);
  const actionBusy = busy || rouletteBusy;
  const swapTargets = swappableMeals(item, planItems);
  const showReroll = mode === "plan" && onReroll && canRerollMeal(item);
  const showSwap = mode === "plan" && onSwap && canSwapMeal(item);

  useEffect(() => {
    if (mode !== "plan" || !item.dish_id) {
      setRecipes([]);
      setRecipesLoading(false);
      return;
    }
    let cancelled = false;
    setRecipesLoading(true);
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
      })
      .finally(() => {
        if (!cancelled) {
          setRecipesLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, item.dish_id, mode]);

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

  async function saveLeftoverSource(value: string) {
    const previous = leftoverSourceId;
    setLeftoverSourceId(value);
    setBusy(true);
    try {
      const updated = await updateMealPlanItem(accessToken, item.id, {
        leftover_source_item_id: value ? Number(value) : null,
      });
      onChanged(updated);
    } catch (err) {
      setLeftoverSourceId(previous);
      onError(err instanceof ApiError ? err.message : "Failed to save leftover source");
    } finally {
      setBusy(false);
    }
  }

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
                <option value="">—</option>
                {recipes.map((recipe) => (
                  <option key={recipe.id} value={recipe.id}>
                    {recipe.variant_name}
                    {recipe.is_main ? " (main)" : ""}
                  </option>
                ))}
              </select>
            </label>
          ) : item.dish_id && recipes.length === 0 && recipesLoading ? (
            <p className="muted meal-slot-recipe">Loading recipes…</p>
          ) : item.dish_id && recipes.length === 0 && !busy ? (
            <p className="muted meal-slot-recipe">No recipe for this dish yet.</p>
          ) : null}

          <SelectionReasons item={item} />

          <div className="meal-slot-actions">
            {showReroll ? (
              <button
                type="button"
                className="button button-secondary"
                disabled={actionBusy}
                onClick={() => onReroll?.(item)}
              >
                Reroll
              </button>
            ) : null}
            {showSwap ? (
              <button
                type="button"
                className="button button-secondary"
                disabled={actionBusy}
                onClick={() => setSwapOpen(true)}
              >
                Swap
              </button>
            ) : null}
            <button
              type="button"
              className="button button-secondary"
              disabled={actionBusy || (!item.is_locked && !item.dish_id)}
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
          {swapOpen && onSwap ? (
            <SwapSlotDialog
              item={item}
              targets={swapTargets}
              busy={actionBusy}
              onClose={() => setSwapOpen(false)}
              onConfirm={(targetItemId) => {
                setSwapOpen(false);
                onSwap(item, targetItemId);
              }}
            />
          ) : null}
        </>
      ) : null}

      {mode === "today" && (item.dish_id || showReviewExecutionActions(item)) ? (
        <div className="meal-slot-actions meal-slot-actions-primary today-meal-primary-actions">
          {item.dish_id ? (
            canOpenCookMode(item) ? (
              cookRecipeId ? (
                <Link to={`/recipes/${cookRecipeId}/cook`} className="button">
                  Cook
                </Link>
              ) : cookRecipesLoading ? (
                <button type="button" className="button" disabled>
                  Cook
                </button>
              ) : (
                <span className="muted">No recipe to cook</span>
              )
            ) : (
              <span className="muted">Leftovers — no cooking steps</span>
            )
          ) : null}
          {showReviewExecutionActions(item) && onReviewToggle ? (
            <button type="button" className="button button-secondary" onClick={onReviewToggle}>
              {reviewExpanded ? "Hide review" : "Review"}
            </button>
          ) : null}
        </div>
      ) : null}

      {mode === "review" && isFuture ? (
        <p className="muted meal-slot-future-note">Future meal — review after it happens</p>
      ) : null}

      {showReviewPanel ? (
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
                    void saveLeftoverSource(event.target.value);
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
                onClick={() => void saveLeftoverSource(leftoverSourceId)}
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
