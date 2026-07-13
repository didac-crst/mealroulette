import type { ReactNode } from "react";

import { Button, Card, PageHeader } from "../../components/ui";
import { addWeeks, formatPlanDate } from "./planFormat";

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
  const pageSubtitle = weekStart
    ? `${subtitle} · Week of ${formatPlanDate(weekStart)}`
    : subtitle;

  return (
    <div className={["stack", "plan-page", className].filter(Boolean).join(" ")}>
      <Card density="comfortable">
        <PageHeader
          title={title}
          subtitle={pageSubtitle}
          actions={
            <div className="week-nav" role="group" aria-label="Week navigation">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="week-nav-button"
                disabled={!weekStart || loading}
                onClick={onPreviousWeek}
                aria-label="Previous week"
              >
                <span aria-hidden="true">‹</span>
                <span className="week-nav-label-long">Previous</span>
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="week-nav-button week-nav-today"
                disabled={loading}
                onClick={onThisWeek}
              >
                This week
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="week-nav-button"
                disabled={!weekStart || loading}
                onClick={onNextWeek}
                aria-label="Next week"
              >
                <span className="week-nav-label-long">Next</span>
                <span aria-hidden="true">›</span>
              </Button>
            </div>
          }
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

export function weekNavigationHandlers(
  weekStart: string | null,
  load: (targetWeekStart?: string) => Promise<void>,
) {
  return {
    onPreviousWeek: () => weekStart && void load(addWeeks(weekStart, -1)),
    onThisWeek: () => void load(),
    onNextWeek: () => weekStart && void load(addWeeks(weekStart, 1)),
  };
}
