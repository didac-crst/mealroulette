import { NavLink } from "react-router-dom";

import { Button } from "../components/ui";
import { BrandLogo } from "../components/BrandLogo";
import { NavIcon } from "./NavIcon";
import { ADMIN_NAV, PRIMARY_NAV } from "./navigation";

type DesktopSidebarProps = {
  username: string;
  isAdmin: boolean;
  onSignOut: () => void;
};

export function DesktopSidebar({ username, isAdmin, onSignOut }: DesktopSidebarProps) {
  return (
    <aside className="desktop-sidebar" aria-label="Application navigation">
      <div className="desktop-sidebar-brand">
        <BrandLogo variant="compact" />
        <div className="desktop-sidebar-brand-text">
          <span className="desktop-sidebar-product">MealRoulette</span>
          <span className="desktop-sidebar-user muted">
            {username}
            {isAdmin ? " · admin" : ""}
          </span>
        </div>
      </div>

      <nav className="desktop-sidebar-nav" aria-label="Primary">
        {PRIMARY_NAV.map(({ to, label, icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `desktop-sidebar-link${isActive ? " desktop-sidebar-link-active" : ""}`
            }
          >
            <NavIcon name={icon} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {isAdmin ? (
        <>
          <div className="desktop-sidebar-separator" role="presentation" />
          <nav className="desktop-sidebar-nav" aria-label="Administration">
            {ADMIN_NAV.map(({ to, label, icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `desktop-sidebar-link${isActive ? " desktop-sidebar-link-active" : ""}`
                }
              >
                <NavIcon name={icon} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
        </>
      ) : null}

      <div className="desktop-sidebar-footer">
        <Button type="button" variant="secondary" size="sm" onClick={onSignOut}>
          Sign out
        </Button>
      </div>
    </aside>
  );
}
