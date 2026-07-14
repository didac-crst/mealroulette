import { COMMON_TIMEZONES } from "../../lib/timezones";

export type TimezoneSelectProps = {
  value: string;
  onChange: (timezone: string) => void;
  id?: string;
  disabled?: boolean;
  ariaLabel?: string;
};

export function TimezoneSelect({ value, onChange, id, disabled, ariaLabel }: TimezoneSelectProps) {
  const knownTimezones = COMMON_TIMEZONES as readonly string[];
  const options = knownTimezones.includes(value) ? knownTimezones : [value, ...knownTimezones];

  return (
    <select
      id={id}
      className="timezone-select"
      value={value}
      disabled={disabled}
      aria-label={ariaLabel ?? "Timezone"}
      onChange={(event) => onChange(event.target.value)}
    >
      {options.map((timezone) => (
        <option key={timezone} value={timezone}>
          {timezone}
        </option>
      ))}
    </select>
  );
}
