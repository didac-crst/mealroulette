import type { ReactNode } from "react";

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
}: Props) {
  return (
    <div className="stack plan-page">
      <section className="card">
        <div className="week-shell-header">
          <div>
            <h2>{title}</h2>
            {weekStart ? (
              <p className="muted">
                {subtitle}
                <br />
                Week of {formatPlanDate(weekStart)}
              </p>
            ) : null}
          </div>
          <div className="week-nav" role="group" aria-label="Week navigation">
            <button
              type="button"
              className="button button-secondary week-nav-button"
              disabled={!weekStart || loading}
              onClick={onPreviousWeek}
              aria-label="Previous week"
            >
              <span aria-hidden="true">‹</span>
              <span className="week-nav-label-long">Previous</span>
            </button>
            <button
              type="button"
              className="button button-secondary week-nav-button week-nav-today"
              disabled={loading}
              onClick={onThisWeek}
            >
              This week
            </button>
            <button
              type="button"
              className="button button-secondary week-nav-button"
              disabled={!weekStart || loading}
              onClick={onNextWeek}
              aria-label="Next week"
            >
              <span className="week-nav-label-long">Next</span>
              <span aria-hidden="true">›</span>
            </button>
          </div>
        </div>
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : null}
      </section>
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
