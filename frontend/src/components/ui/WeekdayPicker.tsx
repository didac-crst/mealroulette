export type WeekdayPickerProps = {
  dates: string[];
  value: string;
  onChange: (date: string) => void;
  formatLabel: (isoDate: string) => string;
  formatSubLabel?: (isoDate: string) => string;
  disabled?: boolean;
  ariaLabel: string;
  className?: string;
};

export function WeekdayPicker({
  dates,
  value,
  onChange,
  formatLabel,
  formatSubLabel,
  disabled = false,
  ariaLabel,
  className,
}: WeekdayPickerProps) {
  if (dates.length === 0) {
    return <p className="muted">No upcoming days in this week.</p>;
  }

  return (
    <div
      className={["weekday-picker-grid", className].filter(Boolean).join(" ")}
      role="group"
      aria-label={ariaLabel}
    >
      {dates.map((date) => {
        const active = date === value;
        return (
          <button
            key={date}
            type="button"
            className={`weekday-picker-cell${active ? " weekday-picker-cell-active" : ""}`}
            disabled={disabled}
            aria-pressed={active}
            onClick={() => onChange(date)}
          >
            <span className="weekday-picker-weekday">{formatLabel(date)}</span>
            {formatSubLabel ? (
              <span className="weekday-picker-date">{formatSubLabel(date)}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
