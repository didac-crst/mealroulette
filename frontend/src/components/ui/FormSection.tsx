import type { ReactNode } from "react";

import { Card } from "./Card";

export type FormSectionProps = {
  title: string;
  description?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function FormSection({ title, description, children, className }: FormSectionProps) {
  return (
    <Card className={["form-section", className].filter(Boolean).join(" ")}>
      <header className="form-section-header">
        <h2>{title}</h2>
        {description ? <p className="muted">{description}</p> : null}
      </header>
      <div className="form-section-body">{children}</div>
    </Card>
  );
}
