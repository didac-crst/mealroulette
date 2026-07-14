import type { ReactNode } from "react";

import { PageShell } from "../../components/ui";
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
  actions?: ReactNode;
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
  actions,
}: Props) {
  return (
    <div className={["stack", "plan-page", className].filter(Boolean).join(" ")}>
      <PageShell title={title} subtitle={subtitle} actions={actions} />
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
      {children}
    </div>
  );
}

export { weekNavigationHandlers } from "./WeekNavigator";
