import { Outlet, useLocation } from "react-router-dom";

import { ButtonLink } from "../components/ButtonLink";
import { Button } from "../components/ui";
import { useAuth } from "../features/auth/AuthContext";
import { useReviewAttentionCount } from "../features/planning/useReviewAttentionCount";
import { DesktopSidebar } from "./DesktopSidebar";
import { MobileBottomNav } from "./MobileBottomNav";

function isCookingModePath(pathname: string): boolean {
  return /^\/recipes\/\d+\/cook\/?$/.test(pathname);
}

export function AppShell() {
  const { user, logout, isAdmin, accessToken } = useAuth();
  const location = useLocation();
  const username = user?.username ?? "";
  const reviewAttention = useReviewAttentionCount(accessToken);
  const cookingMode = isCookingModePath(location.pathname);

  return (
    <div className={`app-shell-layout${cookingMode ? " app-shell-layout--cooking" : ""}`}>
      {!cookingMode ? (
        <DesktopSidebar
          username={username}
          isAdmin={isAdmin}
          onSignOut={() => void logout()}
        />
      ) : null}

      <div className="app-shell-main-column">
        {!cookingMode ? (
          <header className="mobile-shell-bar" aria-label="Account">
            <p className="mobile-shell-user muted">
              {username}
              {isAdmin ? " · admin" : ""}
            </p>
            <div className="mobile-shell-actions">
              {isAdmin ? (
                <ButtonLink to="/settings" variant="ghost" className="mobile-shell-settings">
                  Settings
                </ButtonLink>
              ) : null}
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

        {!cookingMode ? <MobileBottomNav reviewAttention={reviewAttention} /> : null}
      </div>
    </div>
  );
}
