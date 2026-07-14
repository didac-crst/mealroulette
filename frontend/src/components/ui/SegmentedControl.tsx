import type { ReactNode } from "react";

export type SegmentedOption<T extends string | number> = {
  value: T;
  label: ReactNode;
};

export type SegmentedControlProps<T extends string | number> = {
  value: T;
  options: SegmentedOption<T>[];
  onChange: (value: T) => void;
  ariaLabel: string;
  className?: string;
  disabled?: boolean;
};

export function SegmentedControl<T extends string | number>({
  value,
  options,
  onChange,
  ariaLabel,
  className,
  disabled = false,
}: SegmentedControlProps<T>) {
  return (
    <div
      className={["segmented-control", className].filter(Boolean).join(" ")}
      role="group"
      aria-label={ariaLabel}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={String(option.value)}
            type="button"
            className={`segmented-control-option${active ? " segmented-control-option-active" : ""}`}
            aria-pressed={active}
            disabled={disabled}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
