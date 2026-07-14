import type { NavIconName } from "./navigation";

type NavIconProps = {
  name: NavIconName;
};

const STROKE = 1.75;

export function NavIcon({ name }: NavIconProps) {
  const common = {
    width: 22,
    height: 22,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: STROKE,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  switch (name) {
    case "today":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
          <path d="M12 8v4l2.5 2.5" />
        </svg>
      );
    case "plan":
      return (
        <svg {...common}>
          <rect x="4" y="5" width="16" height="15" rx="2" />
          <path d="M8 3v4M16 3v4M4 10h16" />
        </svg>
      );
    case "review":
      return (
        <svg {...common}>
          <path d="M9 11l2.5 2.5L16 8" />
          <rect x="4" y="4" width="16" height="16" rx="3" />
        </svg>
      );
    case "shopping":
      return (
        <svg {...common}>
          <path d="M7 7h14l-1.2 7H8.2L7 7Z" />
          <path d="M7 7 6 4H3" />
          <circle cx="10" cy="18" r="1.25" fill="currentColor" stroke="none" />
          <circle cx="17" cy="18" r="1.25" fill="currentColor" stroke="none" />
        </svg>
      );
    case "dishes":
      return (
        <svg {...common}>
          <path d="M5 10c0-3 2-5 7-5s7 2 7 5" />
          <path d="M4 10h16v2a6 6 0 0 1-6 6H10a6 6 0 0 1-6-6v-2Z" />
          <path d="M9 6c0-2 1.5-3 3-3s3 1 3 3" />
          <path d="M8 4c.5-1 1.5-1.5 4-1.5s3.5.5 4 1.5" />
        </svg>
      );
    case "settings":
      return (
        <svg {...common}>
          <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z" />
          <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3h.1a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8v.1a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
        </svg>
      );
    default:
      return null;
  }
}
