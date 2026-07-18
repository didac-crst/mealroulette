import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";

/** Platform admins and household members may browse the global ingredient catalog. */
export function IngredientCatalogRoute() {
  const { user, loading, isPlatformAdmin, hasHousehold } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <main className="app-shell">
        <p className="muted">Loading session…</p>
      </main>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!isPlatformAdmin && !hasHousehold) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
