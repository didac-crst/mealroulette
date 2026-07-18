import { BrowserRouter, Navigate, Route, Routes, useParams } from "react-router-dom";

import { AppShell } from "../app/AppShell";
import { AuthProvider } from "../features/auth/AuthContext";
import { JoinPage } from "../features/auth/JoinPage";
import { LoginPage } from "../features/auth/LoginPage";
import { SignupPage } from "../features/auth/SignupPage";
import { DishDetailPage } from "../features/dishes/DishDetailPage";
import { DishEditPage } from "../features/dishes/DishEditPage";
import { DishListPage } from "../features/dishes/DishListPage";
import { RecipeCookingPage } from "../features/dishes/RecipeCookingPage";
import { RecipeDetailPage } from "../features/dishes/RecipeDetailPage";
import { RecipeEditPage } from "../features/dishes/RecipeEditPage";
import { PublicCatalogPage } from "../features/catalog/PublicCatalogPage";
import { PublicRecipeDetailPage } from "../features/catalog/PublicRecipeDetailPage";
import { HouseholdPublicationRequestsPage } from "../features/catalog/HouseholdPublicationRequestsPage";
import {
  PublicCatalogReviewDetailPage,
  PublicCatalogReviewQueuePage,
} from "../features/catalog/PublicCatalogReviewPage";
import { IngredientTaxonomyPage } from "../features/ingredients/IngredientTaxonomyPage";
import { IngredientDetailPage } from "../features/ingredients/IngredientDetailPage";
import { IngredientEditPage } from "../features/ingredients/IngredientEditPage";
import { IngredientListPage } from "../features/ingredients/IngredientListPage";
import { MyIngredientProposalsPage } from "../features/ingredients/MyIngredientProposalsPage";
import {
  IngredientProposalReviewDetailPage,
  IngredientProposalReviewQueuePage,
} from "../features/ingredients/IngredientProposalReviewPage";
import { PlanWeekPage } from "../features/planning/PlanWeekPage";
import { ReviewWeekPage } from "../features/planning/ReviewWeekPage";
import { TodayPage } from "../features/planning/TodayPage";
import { ShoppingPage } from "../features/shopping/ShoppingPage";
import { BackupSettingsPage } from "../features/settings/BackupSettingsPage";
import { PersonalTelegramSettingsPage } from "../features/settings/PersonalTelegramSettingsPage";
import { SchedulerSettingsPage } from "../features/settings/SchedulerSettingsPage";
import { AdminSettingsPage } from "../features/settings/AdminSettingsPage";
import { HouseholdMembersPage } from "../features/settings/HouseholdMembersPage";
import { PasswordSettingsPage } from "../features/settings/PasswordSettingsPage";
import { PlanningTargetsPage } from "../features/settings/PlanningTargetsPage";
import { ProtectedRoute } from "./ProtectedRoute";
import { AdminRoute } from "./AdminRoute";
import { HomeRedirect } from "./HomeRedirect";
import { HouseholdAdminRoute } from "./HouseholdAdminRoute";
import { HouseholdMemberRoute } from "./HouseholdMemberRoute";
import { IngredientCatalogRoute } from "./IngredientCatalogRoute";

function LegacyProposalReviewRedirect() {
  const { proposalId } = useParams();
  return <Navigate to={`/ingredients/proposal-review/${proposalId}`} replace />;
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/join" element={<JoinPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route index element={<HomeRedirect />} />
              <Route element={<IngredientCatalogRoute />}>
                <Route path="ingredients" element={<IngredientListPage />} />
                <Route path="ingredients/taxonomy" element={<IngredientTaxonomyPage />} />
                <Route path="ingredients/proposals" element={<MyIngredientProposalsPage />} />
                <Route path="ingredients/:ingredientId" element={<IngredientDetailPage />} />
              </Route>
              <Route element={<AdminRoute />}>
                <Route path="ingredients/new" element={<IngredientEditPage />} />
                <Route path="ingredients/:ingredientId/edit" element={<IngredientEditPage />} />
                <Route path="ingredients/proposal-review" element={<IngredientProposalReviewQueuePage />} />
                <Route
                  path="ingredients/proposal-review/:proposalId"
                  element={<IngredientProposalReviewDetailPage />}
                />
                <Route path="catalog/review" element={<PublicCatalogReviewQueuePage />} />
                <Route path="catalog/review/:publicRecipeId" element={<PublicCatalogReviewDetailPage />} />
                <Route path="settings/backups" element={<BackupSettingsPage />} />
                <Route
                  path="settings/ingredient-proposals"
                  element={<Navigate to="/ingredients/proposal-review" replace />}
                />
                <Route
                  path="settings/ingredient-proposals/:proposalId"
                  element={<LegacyProposalReviewRedirect />}
                />
              </Route>
              <Route path="settings" element={<AdminSettingsPage />} />
              <Route path="settings/telegram" element={<PersonalTelegramSettingsPage />} />
              <Route path="settings/password" element={<PasswordSettingsPage />} />
              <Route
                path="settings/my-ingredient-proposals"
                element={<Navigate to="/ingredients/proposals" replace />}
              />
              <Route element={<HouseholdMemberRoute />}>
                <Route path="today" element={<TodayPage />} />
                <Route path="plan" element={<PlanWeekPage />} />
                <Route path="review" element={<ReviewWeekPage />} />
                <Route path="shopping" element={<ShoppingPage />} />
                <Route path="dishes" element={<DishListPage />} />
                <Route path="dishes/:dishId" element={<DishDetailPage />} />
                <Route path="dishes/:dishId/recipes/:recipeId" element={<RecipeDetailPage />} />
                <Route path="recipes/:recipeId/cook" element={<RecipeCookingPage />} />
                <Route path="catalog" element={<PublicCatalogPage />} />
                <Route path="catalog/recipes/:publicRecipeId" element={<PublicRecipeDetailPage />} />
                <Route element={<HouseholdAdminRoute />}>
                  <Route path="dishes/new" element={<DishEditPage />} />
                  <Route path="dishes/:dishId/edit" element={<DishEditPage />} />
                  <Route path="dishes/:dishId/recipes/new" element={<RecipeEditPage />} />
                  <Route path="dishes/:dishId/recipes/:recipeId/edit" element={<RecipeEditPage />} />
                  <Route path="catalog/requests" element={<HouseholdPublicationRequestsPage />} />
                </Route>
              </Route>
              <Route element={<HouseholdAdminRoute />}>
                <Route path="settings/members" element={<HouseholdMembersPage />} />
                <Route path="settings/targets" element={<PlanningTargetsPage />} />
                <Route path="settings/scheduler" element={<SchedulerSettingsPage />} />
              </Route>
            </Route>
          </Route>
          <Route path="*" element={<HomeRedirect />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
