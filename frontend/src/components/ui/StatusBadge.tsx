import type { ReactNode } from "react";

export type StatusBadgeVariant =
  | "default"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "roulette"
  | "muted";

export type StatusBadgeProps = {
  variant?: StatusBadgeVariant;
  children: ReactNode;
  className?: string;
};

export function StatusBadge({ variant = "default", children, className }: StatusBadgeProps) {
  const classes = ["status-badge", `status-badge-${variant}`, className].filter(Boolean).join(" ");

  return <span className={classes}>{children}</span>;
}
