import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "../app/AppLayout";
import { AuthProvider } from "../features/auth/AuthContext";
import { LoginPage } from "../features/auth/LoginPage";
import { DishDetailPage } from "../features/dishes/DishDetailPage";
import { DishEditPage } from "../features/dishes/DishEditPage";
import { DishListPage } from "../features/dishes/DishListPage";
import { ProtectedRoute } from "./ProtectedRoute";

export function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route index element={<Navigate to="/dishes" replace />} />
              <Route path="dishes" element={<DishListPage />} />
              <Route path="dishes/new" element={<DishEditPage />} />
              <Route path="dishes/:dishId" element={<DishDetailPage />} />
              <Route path="dishes/:dishId/edit" element={<DishEditPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/dishes" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
