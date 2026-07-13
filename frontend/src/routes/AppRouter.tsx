import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "../app/AppShell";
import { AuthProvider } from "../features/auth/AuthContext";
import { LoginPage } from "../features/auth/LoginPage";
import { DishDetailPage } from "../features/dishes/DishDetailPage";
import { DishEditPage } from "../features/dishes/DishEditPage";
import { DishListPage } from "../features/dishes/DishListPage";
import { RecipeCookingPage } from "../features/dishes/RecipeCookingPage";
import { RecipeDetailPage } from "../features/dishes/RecipeDetailPage";
import { RecipeEditPage } from "../features/dishes/RecipeEditPage";
import { IngredientTaxonomyPage } from "../features/ingredients/IngredientTaxonomyPage";
import { IngredientDetailPage } from "../features/ingredients/IngredientDetailPage";
import { IngredientEditPage } from "../features/ingredients/IngredientEditPage";
import { IngredientListPage } from "../features/ingredients/IngredientListPage";
import { PlanWeekPage } from "../features/planning/PlanWeekPage";
import { ReviewWeekPage } from "../features/planning/ReviewWeekPage";
import { TodayPage } from "../features/planning/TodayPage";
import { ShoppingPage } from "../features/shopping/ShoppingPage";
import { BackupSettingsPage } from "../features/settings/BackupSettingsPage";
import { TelegramSettingsPage } from "../features/settings/TelegramSettingsPage";
import { SchedulerSettingsPage } from "../features/settings/SchedulerSettingsPage";
import { AdminSettingsPage } from "../features/settings/AdminSettingsPage";
import { PlanningTargetsPage } from "../features/settings/PlanningTargetsPage";
import { ProtectedRoute } from "./ProtectedRoute";
import { AdminRoute } from "./AdminRoute";

export function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route index element={<Navigate to="/today" replace />} />
              <Route path="today" element={<TodayPage />} />
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
              <Route path="recipes/:recipeId/cook" element={<RecipeCookingPage />} />
              <Route path="ingredients" element={<IngredientListPage />} />
              <Route path="ingredients/taxonomy" element={<IngredientTaxonomyPage />} />
              <Route path="ingredients/new" element={<IngredientEditPage />} />
              <Route path="ingredients/:ingredientId" element={<IngredientDetailPage />} />
              <Route path="ingredients/:ingredientId/edit" element={<IngredientEditPage />} />
              <Route element={<AdminRoute />}>
                <Route path="settings" element={<AdminSettingsPage />} />
                <Route path="settings/targets" element={<PlanningTargetsPage />} />
                <Route path="settings/telegram" element={<TelegramSettingsPage />} />
                <Route path="settings/backups" element={<BackupSettingsPage />} />
                <Route path="settings/scheduler" element={<SchedulerSettingsPage />} />
              </Route>
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/today" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
