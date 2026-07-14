import type { ReactNode } from "react";

export type ReviewOutcomeOption = {
  id: string;
  title: ReactNode;
  description?: ReactNode;
  icon: ReactNode;
  disabled?: boolean;
  onSelect: () => void;
};

export type ReviewOutcomeSelectorProps = {
  options: ReviewOutcomeOption[];
  selectedId?: string | null;
  ariaLabel: string;
  className?: string;
};

export function ReviewOutcomeSelector({
  options,
  selectedId,
  ariaLabel,
  className,
}: ReviewOutcomeSelectorProps) {
  return (
    <div
      className={["review-outcome-selector", className].filter(Boolean).join(" ")}
      role="group"
      aria-label={ariaLabel}
    >
      {options.map((option) => {
        const selected = selectedId === option.id;
        return (
          <button
            key={option.id}
            type="button"
            className={`review-outcome-option${selected ? " review-outcome-option-selected" : ""}`}
            disabled={option.disabled}
            aria-pressed={selected}
            onClick={option.onSelect}
          >
            <span className="review-outcome-icon" aria-hidden>
              {option.icon}
            </span>
            <span className="review-outcome-text">
              <span className="review-outcome-title">{option.title}</span>
              {option.description ? (
                <span className="review-outcome-description muted">{option.description}</span>
              ) : null}
            </span>
          </button>
        );
      })}
    </div>
  );
}
