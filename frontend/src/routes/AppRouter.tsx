import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "../app/AppLayout";
import { AuthProvider } from "../features/auth/AuthContext";
import { LoginPage } from "../features/auth/LoginPage";
import { DishDetailPage } from "../features/dishes/DishDetailPage";
import { DishEditPage } from "../features/dishes/DishEditPage";
import { DishListPage } from "../features/dishes/DishListPage";
import { RecipeDetailPage } from "../features/dishes/RecipeDetailPage";
import { RecipeEditPage } from "../features/dishes/RecipeEditPage";
import { IngredientDetailPage } from "../features/ingredients/IngredientDetailPage";
import { IngredientEditPage } from "../features/ingredients/IngredientEditPage";
import { IngredientListPage } from "../features/ingredients/IngredientListPage";
import { PlanWeekPage } from "../features/planning/PlanWeekPage";
import { ReviewWeekPage } from "../features/planning/ReviewWeekPage";
import { ShoppingPage } from "../features/shopping/ShoppingPage";
import { TelegramSettingsPage } from "../features/settings/TelegramSettingsPage";
import { SchedulerSettingsPage } from "../features/settings/SchedulerSettingsPage";
import { AdminSettingsPage } from "../features/settings/AdminSettingsPage";
import { PlanningTargetsPage } from "../features/settings/PlanningTargetsPage";
import { ProtectedRoute } from "./ProtectedRoute";

export function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route index element={<Navigate to="/review" replace />} />
              <Route path="plan" element={<PlanWeekPage />} />
              <Route path="review" element={<ReviewWeekPage />} />
              <Route path="shopping" element={<ShoppingPage />} />
              <Route path="dishes" element={<DishListPage />} />
              <Route path="dishes/new" element={<DishEditPage />} />
              <Route path="dishes/:dishId" element={<DishDetailPage />} />
              <Route path="dishes/:dishId/edit" element={<DishEditPage />} />
              <Route path="dishes/:dishId/recipes/new" element={<RecipeEditPage />} />
              <Route path="dishes/:dishId/recipes/:recipeId" element={<RecipeDetailPage />} />
              <Route path="dishes/:dishId/recipes/:recipeId/edit" element={<RecipeEditPage />} />
              <Route path="ingredients" element={<IngredientListPage />} />
              <Route path="ingredients/new" element={<IngredientEditPage />} />
              <Route path="ingredients/:ingredientId" element={<IngredientDetailPage />} />
              <Route path="ingredients/:ingredientId/edit" element={<IngredientEditPage />} />
              <Route path="settings" element={<AdminSettingsPage />} />
              <Route path="settings/targets" element={<PlanningTargetsPage />} />
              <Route path="settings/telegram" element={<TelegramSettingsPage />} />
              <Route path="settings/scheduler" element={<SchedulerSettingsPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/review" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
