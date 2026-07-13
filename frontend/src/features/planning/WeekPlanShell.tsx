import type { ReactNode } from "react";

import { Card, PageShell } from "../../components/ui";
import { WeekNavigator } from "./WeekNavigator";

type Props = {
  weekStart: string | null;
  loading: boolean;
  title: string;
  subtitle: string;
  onPreviousWeek: () => void;
  onThisWeek: () => void;
  onNextWeek: () => void;
  error: string | null;
  children: ReactNode;
  className?: string;
};

export function WeekPlanShell({
  weekStart,
  loading,
  title,
  subtitle,
  onPreviousWeek,
  onThisWeek,
  onNextWeek,
  error,
  children,
  className,
}: Props) {
  return (
    <div className={["stack", "plan-page", className].filter(Boolean).join(" ")}>
      <Card density="comfortable" className="week-shell-card">
        <PageShell title={title} subtitle={subtitle} />
        <WeekNavigator
          weekStart={weekStart}
          loading={loading}
          onPreviousWeek={onPreviousWeek}
          onThisWeek={onThisWeek}
          onNextWeek={onNextWeek}
        />
        {error ? (
          <p className="error week-shell-error" role="alert">
            {error}
          </p>
        ) : null}
      </Card>
      {children}
    </div>
  );
}

export { weekNavigationHandlers } from "./WeekNavigator";
