import { Outlet, useLocation } from "react-router-dom";

import { ButtonLink } from "../components/ButtonLink";
import { SkipToContent } from "../components/SkipToContent";
import { Button } from "../components/ui";
import { useAuth } from "../features/auth/AuthContext";
import { useReviewAttentionCount } from "../features/planning/useReviewAttentionCount";
import { DesktopSidebar } from "./DesktopSidebar";
import { MobileBottomNav } from "./MobileBottomNav";
import { resolvePrimaryNav } from "./navigation";

function isCookingModePath(pathname: string): boolean {
  return /^\/recipes\/\d+\/cook\/?$/.test(pathname);
}

export function AppShell() {
  const { user, logout, hasHousehold, isHouseholdAdmin, isPlatformAdmin, accessToken } = useAuth();
  const location = useLocation();
  const username = user?.username ?? "";
  const householdName = user?.active_household_name ?? null;
  const reviewAttention = useReviewAttentionCount(hasHousehold ? accessToken : null);
  const cookingMode = isCookingModePath(location.pathname);
  const primaryNav = resolvePrimaryNav({ hasHousehold, isPlatformAdmin, isHouseholdAdmin });

  return (
    <>
      {!cookingMode ? <SkipToContent /> : null}
      <div className={`app-shell-layout${cookingMode ? " app-shell-layout--cooking" : ""}`}>
      {!cookingMode ? (
        <DesktopSidebar
          username={username}
          householdName={householdName}
          showSettings
          primaryNav={primaryNav}
          reviewAttention={reviewAttention}
          onSignOut={() => void logout()}
        />
      ) : null}

      <div className="app-shell-main-column">
        {!cookingMode ? (
          <header className="mobile-shell-bar" aria-label="Account">
            <div className="mobile-shell-identity muted">
              <span className="mobile-shell-product">MealRoulette</span>
              {householdName ? <span className="mobile-shell-household">{householdName}</span> : null}
              <span className="mobile-shell-user">{username}</span>
            </div>
            <div className="mobile-shell-actions">
              <ButtonLink to="/settings" variant="ghost" className="mobile-shell-settings">
                Settings
              </ButtonLink>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="mobile-shell-signout"
                onClick={() => void logout()}
              >
                Sign out
              </Button>
            </div>
          </header>
        ) : null}

        <main className="app-main" id="main-content">
          <Outlet />
        </main>

        {!cookingMode ? <MobileBottomNav navItems={primaryNav} reviewAttention={reviewAttention} /> : null}
      </div>
    </div>
    </>
  );
}
