import type { ReactNode } from "react";

export type ChoiceCardProps = {
  title: ReactNode;
  description?: ReactNode;
  selected?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
};

export function ChoiceCard({
  title,
  description,
  selected = false,
  disabled = false,
  onClick,
  className,
}: ChoiceCardProps) {
  return (
    <button
      type="button"
      className={[
        "choice-card",
        selected ? "choice-card-selected" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      disabled={disabled}
      aria-pressed={selected}
      aria-label={typeof title === "string" ? title : undefined}
      onClick={onClick}
    >
      <span className="choice-card-title">{title}</span>
      {description ? <span className="choice-card-description muted">{description}</span> : null}
    </button>
  );
}
