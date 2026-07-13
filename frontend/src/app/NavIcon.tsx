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
          <path d="M6 5v14M10 5v14M14 9c2 0 4 1.5 4 4.5V19H10V9h4Z" />
        </svg>
      );
    case "settings":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="3" />
          <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
      );
    default:
      return null;
  }
}
