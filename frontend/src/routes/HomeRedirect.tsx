import { Navigate } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";

export function HomeRedirect() {
  const { loading, hasHousehold, isPlatformAdmin } = useAuth();

  if (loading) {
    return (
      <main className="app-shell">
        <p className="muted">Loading session…</p>
      </main>
    );
  }

  if (hasHousehold) {
    return <Navigate to="/today" replace />;
  }

  if (isPlatformAdmin) {
    return <Navigate to="/ingredients" replace />;
  }

  return <Navigate to="/login" replace />;
}
