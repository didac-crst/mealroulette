import { NavLink } from "react-router-dom";

import { NavIcon } from "./NavIcon";
import { PRIMARY_NAV } from "./navigation";

type MobileBottomNavProps = {
  reviewAttention?: boolean;
};

export function MobileBottomNav({ reviewAttention = false }: MobileBottomNavProps) {
  return (
    <nav className="mobile-bottom-nav" aria-label="Primary navigation">
      {PRIMARY_NAV.map(({ to, label, icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            `mobile-bottom-nav-item${isActive ? " mobile-bottom-nav-item-active" : ""}`
          }
        >
          <span className="mobile-bottom-nav-icon-wrap">
            <NavIcon name={icon} />
            {reviewAttention && to === "/review" ? (
              <span className="mobile-bottom-nav-badge" aria-hidden />
            ) : null}
          </span>
          <span className="mobile-bottom-nav-label">
            {label}
            {reviewAttention && to === "/review" ? (
              <span className="mobile-bottom-nav-attention"> · needs review</span>
            ) : null}
          </span>
        </NavLink>
      ))}
    </nav>
  );
}
