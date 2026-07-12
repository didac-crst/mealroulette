import type { ReactNode } from "react";

import { ButtonLink } from "../../components/ButtonLink";

type Props = {
  title: string;
  subtitle?: string;
  children: ReactNode;
};

export function SettingsPageShell({ title, subtitle, children }: Props) {
  return (
    <section className="card stack settings-page">
      <div className="settings-page-header">
        <ButtonLink to="/settings" variant="secondary" className="settings-back-link">
          ← Settings
        </ButtonLink>
        <div>
          <h2>{title}</h2>
          {subtitle ? <p className="muted settings-page-subtitle">{subtitle}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}
