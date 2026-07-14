import type { ReactNode } from "react";

export type ResponsiveActionGroupProps = {
  children: ReactNode;
  className?: string;
  stackOnMobile?: boolean;
};

export function ResponsiveActionGroup({
  children,
  className,
  stackOnMobile = true,
}: ResponsiveActionGroupProps) {
  return (
    <div
      className={[
        "responsive-action-group",
        stackOnMobile ? "responsive-action-group-stack-sm" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </div>
  );
}
