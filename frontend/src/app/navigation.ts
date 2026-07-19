export type NavIconName =
  | "today"
  | "plan"
  | "review"
  | "shopping"
  | "dishes"
  | "catalog"
  | "ingredients"
  | "settings";

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
  { to: "/catalog", label: "Catalog", icon: "catalog", end: false },
];

/** Household members and admins may browse the global ingredient catalog (read-only for non-platform). */
export const INGREDIENTS_NAV_ITEM: AppNavItem = {
  to: "/ingredients",
  label: "Ingredients",
  icon: "ingredients",
  end: false,
};

/** Platform moderation queue for public recipe publication requests. */
export const RECIPE_REVIEW_NAV_ITEM: AppNavItem = {
  to: "/catalog/review",
  label: "Recipe review",
  icon: "catalog",
  end: false,
};

/** Platform operator without household membership — global catalog surfaces. */
export const PLATFORM_NAV: AppNavItem[] = [INGREDIENTS_NAV_ITEM, RECIPE_REVIEW_NAV_ITEM];

export function householdPrimaryNav(includeIngredients: boolean): AppNavItem[] {
  if (!includeIngredients) {
    return PRIMARY_NAV;
  }
  return [...PRIMARY_NAV, INGREDIENTS_NAV_ITEM];
}

export function resolvePrimaryNav({
  hasHousehold,
  isPlatformAdmin,
  isHouseholdAdmin: _isHouseholdAdmin,
}: {
  hasHousehold: boolean;
  isPlatformAdmin: boolean;
  isHouseholdAdmin: boolean;
}): AppNavItem[] {
  if (!hasHousehold) {
    return isPlatformAdmin ? PLATFORM_NAV : [];
  }
  const nav = householdPrimaryNav(true);
  if (isPlatformAdmin) {
    return [...nav, RECIPE_REVIEW_NAV_ITEM];
  }
  return nav;
}

export const PLATFORM_ADMIN_NAV: AppNavItem[] = [
  { to: "/settings", label: "Settings", icon: "settings", end: false },
];

export const SETTINGS_NAV: AppNavItem[] = [
  { to: "/settings", label: "Settings", icon: "settings", end: false },
];

/** @deprecated Use SETTINGS_NAV — settings is available to all users. */
export const ADMIN_NAV: AppNavItem[] = SETTINGS_NAV;

export function isNavActive(pathname: string, to: string, end = false): boolean {
  if (end) {
    return pathname === to;
  }
  // Keep Catalog inactive on /catalog/review* so Recipe review can own that surface.
  if (to === "/catalog") {
    return (
      pathname === "/catalog" ||
      pathname.startsWith("/catalog/recipes/") ||
      pathname.startsWith("/catalog/requests")
    );
  }
  return pathname === to || pathname.startsWith(`${to}/`);
}
