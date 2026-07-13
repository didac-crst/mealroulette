import type { ReactNode } from "react";

export type DisclosureSectionProps = {
  title: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
};

export function DisclosureSection({
  title,
  children,
  defaultOpen = false,
  className,
}: DisclosureSectionProps) {
  return (
    <details
      className={["disclosure-section", className].filter(Boolean).join(" ")}
      open={defaultOpen || undefined}
    >
      <summary className="disclosure-section-summary">{title}</summary>
      <div className="disclosure-section-body">{children}</div>
    </details>
  );
}
