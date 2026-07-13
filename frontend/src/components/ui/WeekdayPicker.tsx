export type WeekdayPickerProps = {
  dates: string[];
  value: string;
  onChange: (date: string) => void;
  formatLabel: (isoDate: string) => string;
  disabled?: boolean;
  ariaLabel: string;
  className?: string;
};

export function WeekdayPicker({
  dates,
  value,
  onChange,
  formatLabel,
  disabled = false,
  ariaLabel,
  className,
}: WeekdayPickerProps) {
  if (dates.length === 0) {
    return <p className="muted">No upcoming days in this week.</p>;
  }

  return (
    <div
      className={["weekday-picker", className].filter(Boolean).join(" ")}
      role="group"
      aria-label={ariaLabel}
    >
      {dates.map((date) => {
        const active = date === value;
        return (
          <button
            key={date}
            type="button"
            className={`weekday-picker-option${active ? " weekday-picker-option-active" : ""}`}
            disabled={disabled}
            aria-pressed={active}
            onClick={() => onChange(date)}
          >
            {formatLabel(date)}
          </button>
        );
      })}
    </div>
  );
}
