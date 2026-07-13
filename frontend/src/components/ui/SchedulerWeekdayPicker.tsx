import { schedulerWeekdayLabel } from "../../api/scheduler";

export type SchedulerWeekdayPickerProps = {
  value: number;
  onChange: (weekday: number) => void;
  disabled?: boolean;
  ariaLabel: string;
  className?: string;
};

const WEEKDAYS = [0, 1, 2, 3, 4, 5, 6] as const;

function shortWeekdayLabel(weekday: number): string {
  return schedulerWeekdayLabel(weekday).slice(0, 3);
}

export function SchedulerWeekdayPicker({
  value,
  onChange,
  disabled = false,
  ariaLabel,
  className,
}: SchedulerWeekdayPickerProps) {
  return (
    <div
      className={["scheduler-weekday-picker", className].filter(Boolean).join(" ")}
      role="group"
      aria-label={ariaLabel}
    >
      {WEEKDAYS.map((weekday) => {
        const active = value === weekday;
        return (
          <button
            key={weekday}
            type="button"
            className={`scheduler-weekday-option${active ? " scheduler-weekday-option-active" : ""}`}
            disabled={disabled}
            aria-pressed={active}
            title={schedulerWeekdayLabel(weekday)}
            onClick={() => onChange(weekday)}
          >
            {shortWeekdayLabel(weekday)}
          </button>
        );
      })}
    </div>
  );
}
