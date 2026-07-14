import type { ButtonHTMLAttributes, ReactNode } from "react";

export type NavigationActionProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  icon: ReactNode;
  label: ReactNode;
};

export function NavigationAction({ icon, label, className, ...props }: NavigationActionProps) {
  return (
    <button
      type="button"
      className={["navigation-action", className].filter(Boolean).join(" ")}
      {...props}
    >
      <span className="navigation-action-icon" aria-hidden>
        {icon}
      </span>
      <span className="navigation-action-label">{label}</span>
    </button>
  );
}
