import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";

/** Routes that require an active household membership (meal planning workflows). */
export function HouseholdMemberRoute() {
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

  if (!hasHousehold) {
    const fallback = isPlatformAdmin ? "/ingredients" : "/login";
    return <Navigate to={fallback} replace />;
  }

  return <Outlet />;
}
