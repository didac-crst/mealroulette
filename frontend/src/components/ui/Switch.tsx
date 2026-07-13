import type { InputHTMLAttributes, ReactNode } from "react";

export type SwitchProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label: ReactNode;
};

export function Switch({ label, className, id, ...props }: SwitchProps) {
  const inputId = id ?? `switch-${typeof label === "string" ? label.replace(/\s+/g, "-").toLowerCase() : "field"}`;

  return (
    <label className={["switch-field", className].filter(Boolean).join(" ")} htmlFor={inputId}>
      <input {...props} id={inputId} type="checkbox" role="switch" className="switch-input" />
      <span className="switch-track" aria-hidden />
      <span className="switch-label">{label}</span>
    </label>
  );
}
