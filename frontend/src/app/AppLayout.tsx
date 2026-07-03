import { NavLink, Outlet } from "react-router-dom";

import { NavButtonLink } from "../components/ButtonLink";
import { useAuth } from "../features/auth/AuthContext";

const TAB_ROUTES = [
  { to: "/plan", label: "Plan" },
  { to: "/review", label: "Review" },
  { to: "/dishes", label: "Dishes" },
] as const;

export function AppLayout() {
  const { user, logout, isAdmin } = useAuth();

  return (
    <div className="app-frame">
      <header className="app-header">
        <div className="app-header-brand">
          <h1>MealRoulette</h1>
          <p className="muted app-header-meta">
            {user?.username}
            {isAdmin ? " · admin" : ""}
          </p>
        </div>
        <nav className="app-header-nav-desktop" aria-label="Main">
          {TAB_ROUTES.map(({ to, label }) => (
            <NavButtonLink key={to} to={to}>
              {label}
            </NavButtonLink>
          ))}
          <button type="button" className="button button-secondary" onClick={() => void logout()}>
            Sign out
          </button>
        </nav>
        <button
          type="button"
          className="button button-secondary app-header-signout-mobile"
          onClick={() => void logout()}
        >
          Sign out
        </button>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <nav className="app-tab-bar" aria-label="Main">
        {TAB_ROUTES.map(({ to, label }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `app-tab${isActive ? " app-tab-active" : ""}`}>
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
