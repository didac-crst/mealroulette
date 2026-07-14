import type { ReactNode } from "react";

export type DisclosureSectionProps = {
  title: ReactNode;
  description?: ReactNode;
  meta?: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
};

export function DisclosureSection({
  title,
  description,
  meta,
  children,
  defaultOpen = false,
  className,
}: DisclosureSectionProps) {
  return (
    <details
      className={["disclosure-section", className].filter(Boolean).join(" ")}
      open={defaultOpen || undefined}
    >
      <summary className="disclosure-section-summary">
        <span className="disclosure-section-heading">
          <span className="disclosure-section-title">{title}</span>
          {description ? (
            <span className="disclosure-section-description muted">{description}</span>
          ) : null}
        </span>
        {meta ? <span className="disclosure-section-meta muted">{meta}</span> : null}
      </summary>
      <div className="disclosure-section-body">{children}</div>
    </details>
  );
}
