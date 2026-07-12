import { useEffect, useState } from "react";

import { fetchRecipes, type Dish, type Recipe } from "../../api/catalog";
import type { MealPlanItem } from "../../api/planning";
import { MealSlotCard } from "./MealSlotCard";
import { canOpenCookMode, resolveCookRecipeId } from "./todayMeals";

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
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [recipesLoading, setRecipesLoading] = useState(false);

  useEffect(() => {
    if (!accessToken || !item.dish_id || !canOpenCookMode(item)) {
      setRecipes([]);
      setRecipesLoading(false);
      return;
    }
    let cancelled = false;
    setRecipesLoading(true);
    fetchRecipes(accessToken, item.dish_id)
      .then((recipeData) => {
        if (!cancelled) {
          setRecipes(recipeData);
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
  }, [accessToken, item.dish_id, item.status]);

  const cookRecipeId = canOpenCookMode(item) ? resolveCookRecipeId(item, recipes) : null;
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
      cookRecipeId={cookRecipeId}
      cookRecipesLoading={recipesLoading}
      reviewExpanded={reviewExpanded}
      onReviewToggle={() => setReviewOpen((open) => !open)}
      onChanged={onChanged}
      onError={onError}
    />
  );
}
