import { NavLink } from "react-router-dom";

import { NavigationAction } from "../components/ui";
import { BrandLogo } from "../components/BrandLogo";
import { NavIcon } from "./NavIcon";
import { ADMIN_NAV, PRIMARY_NAV } from "./navigation";

type DesktopSidebarProps = {
  username: string;
  isAdmin: boolean;
  reviewAttention?: boolean;
  onSignOut: () => void;
};

function SignOutIcon() {
  return (
    <svg
      width={22}
      height={22}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

export function DesktopSidebar({ username, isAdmin, reviewAttention = false, onSignOut }: DesktopSidebarProps) {
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
            <span className="desktop-sidebar-link-icon-wrap">
              <NavIcon name={icon} />
              {reviewAttention && to === "/review" ? (
                <span className="desktop-sidebar-link-badge" aria-hidden />
              ) : null}
            </span>
            <span>
              {label}
              {reviewAttention && to === "/review" ? (
                <span className="desktop-sidebar-link-attention"> · needs review</span>
              ) : null}
            </span>
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
        <NavigationAction icon={<SignOutIcon />} label="Sign out" onClick={onSignOut} />
      </div>
    </aside>
  );
}
