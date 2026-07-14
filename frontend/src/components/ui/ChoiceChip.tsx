import type { ReactNode } from "react";

export type ChoiceChipProps = {
  label: ReactNode;
  selected?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
};

export function ChoiceChip({
  label,
  selected = false,
  disabled = false,
  onClick,
  className,
}: ChoiceChipProps) {
  return (
    <button
      type="button"
      className={[
        "choice-chip",
        selected ? "choice-chip-selected" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      disabled={disabled}
      aria-pressed={selected}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
