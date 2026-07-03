import { NavLink, Outlet } from "react-router-dom";

import { NavButtonLink } from "../components/ButtonLink";
import { useAuth } from "../features/auth/AuthContext";

const TAB_ROUTES = [
  { to: "/plan", label: "Plan" },
  { to: "/review", label: "Review" },
  { to: "/shopping", label: "List" },
  { to: "/dishes", label: "Dishes" },
] as const;

export function AppLayout() {
  const { user, logout, isAdmin } = useAuth();

  const tabRoutes = isAdmin
    ? [...TAB_ROUTES, { to: "/ingredients", label: "Ingredients" } as const]
    : TAB_ROUTES;

  return (
    <div className="app-frame">
      <header className="app-header">
        <div className="app-header-brand">
          <picture>
            <source srcSet="/logo-header.webp" type="image/webp" />
            <img src="/logo-header.png" alt="" width={40} height={40} className="app-header-logo" />
          </picture>
          <div>
            <h1>MealRoulette</h1>
            <p className="muted app-header-meta">
            {user?.username}
            {isAdmin ? " · admin" : ""}
            </p>
          </div>
        </div>
        <nav className="app-header-nav-desktop" aria-label="Primary navigation">
          {tabRoutes.map(({ to, label }) => (
            <NavButtonLink key={to} to={to}>
              {label}
            </NavButtonLink>
          ))}
          {isAdmin ? (
            <NavButtonLink to="/settings/telegram" inactiveVariant="secondary">
              Telegram
            </NavButtonLink>
          ) : null}
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

      <nav className="app-tab-bar" aria-label="Primary navigation (mobile)">
        {tabRoutes.map(({ to, label }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `app-tab${isActive ? " app-tab-active" : ""}`}>
            {label}
          </NavLink>
        ))}
        {isAdmin ? (
          <NavLink
            to="/settings/telegram"
            className={({ isActive }) => `app-tab${isActive ? " app-tab-active" : ""}`}
          >
            Telegram
          </NavLink>
        ) : null}
      </nav>
    </div>
  );
}
