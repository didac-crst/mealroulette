import type { ReactNode } from "react";

import { PageShell } from "../../components/ui";
import { HouseholdClock } from "./HouseholdClock";

type Props = {
  title: string;
  subtitle?: string;
  loading?: boolean;
  children: ReactNode;
};

export function SettingsPageShell({ title, subtitle, loading = false, children }: Props) {
  return (
    <div className="admin-subpage">
      <PageShell title={title} subtitle={subtitle} loading={loading} loadingMessage="Loading…">
        <HouseholdClock />
        {children}
      </PageShell>
    </div>
  );
}
