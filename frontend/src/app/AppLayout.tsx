import { Outlet } from "react-router-dom";

import { NavButtonLink } from "../components/ButtonLink";
import { useAuth } from "../features/auth/AuthContext";

export function AppLayout() {
  const { user, logout, isAdmin } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>MealRoulette</h1>
          <p className="muted">
            {user?.username} ({user?.role})
            {isAdmin ? " · can edit" : " · read only"}
          </p>
        </div>
        <nav className="app-nav" aria-label="Main">
          <NavButtonLink to="/dishes">Dishes</NavButtonLink>
          <button type="button" className="button button-secondary" onClick={() => void logout()}>
            Sign out
          </button>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
