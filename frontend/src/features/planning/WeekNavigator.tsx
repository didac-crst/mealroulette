import { Button } from "../../components/ui";
import { addWeeks, formatPlanDate, todayIso, weekDates, weekStartForDate } from "./planFormat";

type Props = {
  weekStart: string | null;
  loading?: boolean;
  onPreviousWeek: () => void;
  onThisWeek: () => void;
  onNextWeek: () => void;
};

function formatWeekRange(weekStart: string): string {
  const dates = weekDates(weekStart);
  if (dates.length === 0) {
    return formatPlanDate(weekStart);
  }
  const start = new Date(`${dates[0]}T12:00:00`);
  const end = new Date(`${dates[dates.length - 1]}T12:00:00`);
  const sameMonth = start.getMonth() === end.getMonth();
  const startLabel = start.toLocaleDateString(undefined, { day: "numeric", month: "short" });
  const endLabel = end.toLocaleDateString(
    undefined,
    sameMonth ? { day: "numeric" } : { day: "numeric", month: "short" },
  );
  return `${startLabel} – ${endLabel}`;
}

export function WeekNavigator({
  weekStart,
  loading = false,
  onPreviousWeek,
  onThisWeek,
  onNextWeek,
}: Props) {
  const currentWeekStart = weekStartForDate(todayIso());
  const isCurrentWeek = weekStart === currentWeekStart;
  const rangeLabel = weekStart ? formatWeekRange(weekStart) : "Select a week";

  return (
    <div className="week-navigator">
      <div className="week-navigator-controls" role="group" aria-label="Week navigation">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="week-nav-chevron"
          disabled={!weekStart || loading}
          onClick={onPreviousWeek}
          aria-label="Previous week"
        >
          ‹
        </Button>
        <p className="week-navigator-range" aria-live="polite">
          {rangeLabel}
        </p>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="week-nav-chevron"
          disabled={!weekStart || loading}
          onClick={onNextWeek}
          aria-label="Next week"
        >
          ›
        </Button>
      </div>
      {!isCurrentWeek ? (
        <button
          type="button"
          className="week-navigator-reset"
          disabled={loading}
          onClick={onThisWeek}
        >
          This week
        </button>
      ) : null}
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
