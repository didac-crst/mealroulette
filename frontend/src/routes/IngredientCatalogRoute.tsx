import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";

/** Platform admins (write later) and household admins (read) may browse the global ingredient catalog. */
export function IngredientCatalogRoute() {
  const { user, loading, isPlatformAdmin, isHouseholdAdmin, hasHousehold } = useAuth();
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

  if (!isPlatformAdmin && !isHouseholdAdmin) {
    return <Navigate to={hasHousehold ? "/today" : "/login"} replace />;
  }

  return <Outlet />;
}
