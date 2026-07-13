export type NavIconName = "today" | "plan" | "review" | "shopping" | "dishes" | "settings";

export type AppNavItem = {
  to: string;
  label: string;
  icon: NavIconName;
  end?: boolean;
};

/** Primary mobile and desktop navigation — frequency ordered. */
export const PRIMARY_NAV: AppNavItem[] = [
  { to: "/today", label: "Today", icon: "today", end: false },
  { to: "/plan", label: "Plan", icon: "plan", end: false },
  { to: "/review", label: "Review", icon: "review", end: false },
  { to: "/shopping", label: "Shopping", icon: "shopping", end: false },
  { to: "/dishes", label: "Dishes", icon: "dishes", end: false },
];

export const ADMIN_NAV: AppNavItem[] = [
  { to: "/settings", label: "Settings", icon: "settings", end: false },
];

export function isNavActive(pathname: string, to: string, end = false): boolean {
  if (end) {
    return pathname === to;
  }
  return pathname === to || pathname.startsWith(`${to}/`);
}
