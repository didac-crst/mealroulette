import type { ReactNode } from "react";

import { Button } from "./Button";

export type NumberStepperProps = {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  label?: ReactNode;
  disabled?: boolean;
  ariaLabel: string;
  className?: string;
};

export function NumberStepper({
  value,
  onChange,
  min = 0,
  max = 99,
  step = 1,
  label,
  disabled = false,
  ariaLabel,
  className,
}: NumberStepperProps) {
  const decrease = () => onChange(Math.max(min, value - step));
  const increase = () => onChange(Math.min(max, value + step));

  return (
    <div className={["number-stepper-field", className].filter(Boolean).join(" ")}>
      {label ? <span className="number-stepper-label">{label}</span> : null}
      <div className="number-stepper" role="group" aria-label={ariaLabel}>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="number-stepper-button"
          disabled={disabled || value <= min}
          aria-label={`Decrease ${ariaLabel}`}
          onClick={decrease}
        >
          −
        </Button>
        <output className="number-stepper-value" aria-live="polite">
          {value}
        </output>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="number-stepper-button"
          disabled={disabled || value >= max}
          aria-label={`Increase ${ariaLabel}`}
          onClick={increase}
        >
          +
        </Button>
      </div>
    </div>
  );
}
