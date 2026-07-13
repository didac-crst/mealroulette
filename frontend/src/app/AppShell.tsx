import { Outlet } from "react-router-dom";

import { ButtonLink } from "../components/ButtonLink";
import { useAuth } from "../features/auth/AuthContext";
import { DesktopSidebar } from "./DesktopSidebar";
import { MobileBottomNav } from "./MobileBottomNav";

export function AppShell() {
  const { user, logout, isAdmin } = useAuth();
  const username = user?.username ?? "";

  return (
    <div className="app-shell-layout">
      <DesktopSidebar
        username={username}
        isAdmin={isAdmin}
        onSignOut={() => void logout()}
      />

      <div className="app-shell-main-column">
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
            <button
              type="button"
              className="button button-ghost button-sm mobile-shell-signout"
              onClick={() => void logout()}
            >
              Sign out
            </button>
          </div>
        </header>

        <main className="app-main" id="main-content">
          <Outlet />
        </main>

        <MobileBottomNav />
      </div>
    </div>
  );
}
