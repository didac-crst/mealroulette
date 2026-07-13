import { Button } from "../../components/ui";
import { addWeeks, formatPlanDate, weekDates } from "./planFormat";

type Props = {
  weekStart: string | null;
  loading?: boolean;
  onPreviousWeek: () => void;
  onThisWeek: () => void;
  onNextWeek: () => void;
};

export function WeekNavigator({
  weekStart,
  loading = false,
  onPreviousWeek,
  onThisWeek,
  onNextWeek,
}: Props) {
  const dates = weekStart ? weekDates(weekStart) : [];
  const rangeLabel =
    dates.length > 0
      ? `${formatPlanDate(dates[0])} – ${formatPlanDate(dates[dates.length - 1])}`
      : "Select a week";

  return (
    <div className="week-navigator">
      <p className="week-navigator-range" aria-live="polite">
        {rangeLabel}
      </p>
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
