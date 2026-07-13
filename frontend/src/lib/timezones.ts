/** Common household timezones for settings UI (stored value remains IANA id). */
export const COMMON_TIMEZONES = [
  "Europe/Paris",
  "Europe/London",
  "Europe/Berlin",
  "Europe/Madrid",
  "Europe/Rome",
  "Europe/Amsterdam",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "UTC",
] as const;

export const WEEK_OFFSET_OPTIONS = [
  { value: 0, label: "This week" },
  { value: 1, label: "Next week" },
  { value: 2, label: "Two weeks ahead" },
  { value: 3, label: "Three weeks ahead" },
  { value: 4, label: "Four weeks ahead" },
] as const;

export const REMINDER_WINDOW_PRESETS = [
  { value: 1, label: "Today only" },
  { value: 3, label: "Next 3 days" },
  { value: 7, label: "Next 7 days" },
] as const;
