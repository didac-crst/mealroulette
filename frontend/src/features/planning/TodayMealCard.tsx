import { useEffect, useMemo, useState } from "react";

import { fetchRecipes, type Dish, type Recipe } from "../../api/catalog";
import type { MealPlanItem } from "../../api/planning";
import { MealSlotCard } from "./MealSlotCard";
import { buildCookOptions, canOpenCookMode, cookableDishIds } from "./todayMeals";

type Props = {
  item: MealPlanItem;
  dishes: Dish[];
  planItems: MealPlanItem[];
  leftoverSources: MealPlanItem[];
  sourceLookupItems: MealPlanItem[];
  accessToken: string;
  onChanged: (item: MealPlanItem) => void;
  onError: (message: string) => void;
};

export function TodayMealCard({
  item,
  dishes,
  planItems,
  leftoverSources,
  sourceLookupItems,
  accessToken,
  onChanged,
  onError,
}: Props) {
  const [reviewOpen, setReviewOpen] = useState(false);
  const [recipesByDishId, setRecipesByDishId] = useState<Map<number, Recipe[]>>(new Map());
  const [recipesLoading, setRecipesLoading] = useState(false);
  const dishIds = useMemo(
    () => (canOpenCookMode(item) ? cookableDishIds(item) : []),
    [item],
  );

  useEffect(() => {
    if (!accessToken || dishIds.length === 0) {
      setRecipesByDishId(new Map());
      setRecipesLoading(false);
      return;
    }
    let cancelled = false;
    setRecipesLoading(true);
    Promise.all(
      dishIds.map(async (dishId) => {
        const recipes = await fetchRecipes(accessToken, dishId);
        return [dishId, recipes] as const;
      }),
    )
      .then((entries) => {
        if (!cancelled) {
          setRecipesByDishId(new Map(entries));
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRecipesByDishId(new Map());
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
  }, [accessToken, dishIds]);

  const cookOptions = useMemo(
    () => (canOpenCookMode(item) ? buildCookOptions(item, recipesByDishId) : []),
    [item, recipesByDishId],
  );
  const reviewExpanded = reviewOpen || item.status !== "planned";

  return (
    <MealSlotCard
      item={item}
      dishes={dishes}
      planItems={planItems}
      leftoverSources={leftoverSources}
      sourceLookupItems={sourceLookupItems}
      accessToken={accessToken}
      mode="today"
      cookOptions={cookOptions}
      cookOptionsLoading={recipesLoading}
      reviewExpanded={reviewExpanded}
      onReviewToggle={() => setReviewOpen((open) => !open)}
      onChanged={onChanged}
      onError={onError}
    />
  );
}
