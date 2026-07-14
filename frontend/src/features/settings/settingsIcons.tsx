const STROKE = 1.75;

const iconProps = {
  width: 22,
  height: 22,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: STROKE,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function SettingsTargetsIcon() {
  return (
    <svg {...iconProps}>
      <path d="M4 19V5" />
      <path d="M4 19h16" />
      <path d="M8 15V11" />
      <path d="M12 15V7" />
      <path d="M16 15v-4" />
    </svg>
  );
}

export function SettingsSchedulerIcon() {
  return (
    <svg {...iconProps}>
      <rect x="4" y="5" width="16" height="15" rx="2" />
      <path d="M8 3v4M16 3v4M4 10h16" />
      <circle cx="12" cy="15" r="2.5" />
    </svg>
  );
}

export function SettingsTelegramIcon() {
  return (
    <svg {...iconProps}>
      <path d="M21 5 4 11l5 2 2 6 3-4 5 4 7-14Z" />
      <path d="m9 13 10-7" />
    </svg>
  );
}

export function SettingsBackupIcon() {
  return (
    <svg {...iconProps}>
      <path d="M12 3v10" />
      <path d="m8 9 4 4 4-4" />
      <path d="M5 15a7 7 0 0 0 14 0" />
    </svg>
  );
}

export function SettingsIngredientsIcon() {
  return (
    <svg {...iconProps}>
      <path d="M8 6h13" />
      <path d="M8 12h13" />
      <path d="M8 18h13" />
      <path d="M3 6h.01" />
      <path d="M3 12h.01" />
      <path d="M3 18h.01" />
    </svg>
  );
}
