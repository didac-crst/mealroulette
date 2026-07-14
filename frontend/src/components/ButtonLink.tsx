import { Link, NavLink, type LinkProps, type NavLinkProps } from "react-router-dom";

import { buttonClasses, type ButtonVariant } from "./ui/buttonClasses";

type ButtonLinkProps = LinkProps & {
  variant?: ButtonVariant;
};

export function ButtonLink({ variant = "primary", className, ...props }: ButtonLinkProps) {
  return <Link className={buttonClasses(variant, "md", className)} {...props} />;
}

type NavButtonLinkProps = Omit<NavLinkProps, "className"> & {
  activeVariant?: ButtonVariant;
  inactiveVariant?: ButtonVariant;
  className?: string;
};

export function NavButtonLink({
  activeVariant = "primary",
  inactiveVariant = "secondary",
  className,
  ...props
}: NavButtonLinkProps) {
  return (
    <NavLink
      className={({ isActive }) =>
        buttonClasses(isActive ? activeVariant : inactiveVariant, "md", className)
      }
      {...props}
    />
  );
}

export type { ButtonVariant } from "./ui/buttonClasses";
