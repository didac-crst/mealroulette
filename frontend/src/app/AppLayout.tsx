import { NavLink, Outlet } from "react-router-dom";

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
          <NavLink to="/dishes" className={({ isActive }) => (isActive ? "active" : undefined)}>
            Dishes
          </NavLink>
          <button type="button" className="link-button" onClick={() => void logout()}>
            Sign out
          </button>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
