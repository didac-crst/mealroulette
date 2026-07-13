import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import type { Dish, Recipe } from "../../api/catalog";
import { fetchRecipes } from "../../api/catalog";
import { ApiError } from "../../api/client";
import { Button, DisclosureSection, ResponsiveActionGroup, ReviewOutcomeSelector, SearchSelect, StatusBadge } from "../../components/ui";
import { dishPlaceholderEmoji } from "../dishes/dishVisual";
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
  selectionReasonsList,
  showLeftoverSourcePicker,
  showLeftoverSourceSummary,
  showReviewExecutionActions,
  showReviewRating,
  showSkipSummary,
  showUndoStatus,
  swappableMeals,
} from "./planFormat";
import { mealStatusBadgeVariant } from "./mealStatusBadge";
import { canOpenCookMode } from "./todayMeals";
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
  const statusBadgeVariant = mealStatusBadgeVariant(item, mode);
  const showUndo = (mode === "review" || mode === "today") && showUndoStatus(item);
  const showTodayReviewPanel = mode !== "today" || reviewExpanded;
  const showReviewPanel =
    (mode === "review" && !isFuture) || (mode === "today" && showTodayReviewPanel);
  const actionBusy = busy || rouletteBusy;
  const swapTargets = swappableMeals(item, planItems);
  const showReroll = mode === "plan" && onReroll && canRerollMeal(item);
  const showSwap = mode === "plan" && onSwap && canSwapMeal(item);
  const dish = item.dish_id ? dishes.find((entry) => entry.id === item.dish_id) : undefined;
  const dishOptions = useMemo(
    () => dishes.map((entry) => ({ value: String(entry.id), label: entry.name })),
    [dishes],
  );
  const recipeOptions = useMemo(
    () =>
      recipes.map((recipe) => ({
        value: String(recipe.id),
        label: `${recipe.variant_name}${recipe.is_main ? " (main)" : ""}`,
      })),
    [recipes],
  );
  const selectionReasons = selectionReasonsList(item);
  const showLock = mode === "plan";

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
    mode === "today" ? "meal-hero-card" : "",
    isFuture && mode === "review" ? "meal-slot-card-future" : "",
    isReviewed ? "meal-slot-card-reviewed" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <article className={cardClass}>
      {mode === "today" ? (
        <div className="meal-hero-top">
          <div className="meal-hero-media" aria-hidden={!dish?.image_url}>
            {dish?.image_url ? (
              <img src={dish.image_url} alt="" className="meal-hero-image" />
            ) : (
              <span className="meal-hero-emoji">{dish ? dishPlaceholderEmoji(dish) : "🍽️"}</span>
            )}
          </div>
          <div className="meal-hero-content">
            <div className="meal-hero-heading">
              <p className="meal-slot-label">{formatSlotLabel(item.meal_slot)}</p>
              <StatusBadge variant={statusBadgeVariant}>{statusLabel}</StatusBadge>
            </div>
            {item.dish_id ? (
              <Link to={`/dishes/${item.dish_id}`} className="meal-hero-title">
                {item.dish_name}
              </Link>
            ) : (
              <p className="muted meal-slot-empty">No dish assigned</p>
            )}
            {item.recipe_variant_name ? (
              <p className="muted meal-hero-recipe">{item.recipe_variant_name}</p>
            ) : null}
          </div>
        </div>
      ) : (
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
            <StatusBadge variant={statusBadgeVariant}>{statusLabel}</StatusBadge>
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
      )}

      {mode === "today" && showUndo ? (
        <div className="meal-hero-undo">
          <button
            type="button"
            className="button button-undo"
            disabled={busy}
            onClick={() => void run(() => resetMealPlanItemStatus(accessToken, item.id))}
          >
            Undo status
          </button>
        </div>
      ) : null}

      {mode === "plan" ? (
        <>
          <label className="meal-slot-assign">
            <span className="muted">Assign dish</span>
            <SearchSelect
              ariaLabel="Assign dish"
              value={item.dish_id ? String(item.dish_id) : ""}
              options={dishOptions}
              disabled={busy || item.is_locked}
              placeholder="Search dishes…"
              onChange={(nextValue) => void handleDishChange(nextValue)}
            />
          </label>

          {item.dish_id && recipes.length > 0 ? (
            <label className="meal-slot-assign">
              <span className="muted">Recipe variant</span>
              <SearchSelect
                ariaLabel="Recipe variant"
                value={item.recipe_id ? String(item.recipe_id) : ""}
                options={recipeOptions}
                disabled={busy || item.is_locked}
                placeholder="Search recipes…"
                onChange={(nextValue) => void handleRecipeChange(nextValue)}
              />
            </label>
          ) : item.dish_id && recipes.length === 0 && recipesLoading ? (
            <p className="muted meal-slot-recipe">Loading recipes…</p>
          ) : item.dish_id && recipes.length === 0 && !busy ? (
            <p className="muted meal-slot-recipe">No recipe for this dish yet.</p>
          ) : null}

          {selectionReasons.length > 0 ? (
            <DisclosureSection title="Why this meal">
              <ul className="selection-reasons-list">
                {selectionReasons.map((reason, index) => (
                  <li key={`${index}-${reason}`}>{reason}</li>
                ))}
              </ul>
            </DisclosureSection>
          ) : null}

          <div className="meal-slot-plan-actions">
            {showReroll ? (
              <Button
                type="button"
                variant="roulette"
                size="sm"
                disabled={actionBusy}
                onClick={() => onReroll?.(item)}
              >
                Reroll
              </Button>
            ) : null}
            {showSwap ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="meal-slot-secondary-action"
                disabled={actionBusy}
                onClick={() => setSwapOpen(true)}
              >
                Swap
              </Button>
            ) : null}
            {showLock ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="meal-slot-secondary-action"
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
              </Button>
            ) : null}
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
        <ResponsiveActionGroup className="meal-hero-actions" stackOnMobile>
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
            <button type="button" className="button button-ghost" onClick={onReviewToggle}>
              {reviewExpanded ? "Hide review" : "Review"}
            </button>
          ) : null}
        </ResponsiveActionGroup>
      ) : null}

      {mode === "review" && isFuture ? (
        <p className="muted meal-slot-future-note">Future meal — review after it happens</p>
      ) : null}

      {showReviewPanel ? (
        <>
          {showReviewExecutionActions(item) && !skipFormOpen ? (
            <ReviewOutcomeSelector
              ariaLabel="How did this meal go?"
              options={[
                {
                  id: "ate",
                  title: "Ate as planned",
                  description: "Mark this meal as eaten.",
                  icon: "✓",
                  disabled: busy || !item.dish_id,
                  onSelect: () => void run(() => markMealPlanItemEaten(accessToken, item.id)),
                },
                {
                  id: "skipped",
                  title: "Skipped",
                  description: "Did not eat this meal.",
                  icon: "—",
                  disabled: busy,
                  onSelect: () => setSkipFormOpen(true),
                },
                {
                  id: "leftovers",
                  title: "Ate leftovers",
                  description: "Finished leftovers instead.",
                  icon: "↺",
                  disabled: busy,
                  onSelect: () => void run(() => markMealPlanItemAteLeftovers(accessToken, item.id)),
                },
              ]}
            />
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
