import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";

export function HouseholdAdminRoute() {
  const { user, loading, isHouseholdAdmin } = useAuth();
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

  if (!isHouseholdAdmin) {
    return <Navigate to="/today" replace />;
  }

  return <Outlet />;
}
