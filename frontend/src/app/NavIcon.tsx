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
          <path d="M4 17h16" />
          <path d="M6 17a6 6 0 0 1 12 0" />
          <path d="M12 8v-2" />
          <path d="M9.75 6h4.5" />
          <path d="M7.5 20h9" />
        </svg>
      );
    case "catalog":
      return (
        <svg {...common}>
          <path d="M5 4h10a2 2 0 0 1 2 2v14l-4-2-4 2V6a2 2 0 0 0-2-2H5Z" />
          <path d="M9 8h6M9 12h6" />
        </svg>
      );
    case "ingredients":
      return (
        <svg {...common}>
          <path d="M4 11.5C4 7.4 7.4 4 12 4s8 3.4 8 7.5c0 1.1-.9 2-2 2h-3.2l1.2 6.5H8l1.2-6.5H6c-1.1 0-2-.9-2-2Z" />
          <path d="M9.2 13.5h5.6" />
          <path d="M10.2 17h3.6" />
          <path d="M7.5 9.5h.01" />
          <path d="M12 7.8h.01" />
          <path d="M16.5 9.5h.01" />
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
