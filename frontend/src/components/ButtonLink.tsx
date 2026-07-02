import { Link, NavLink, type LinkProps, type NavLinkProps } from "react-router-dom";

export type ButtonVariant = "primary" | "secondary" | "danger";

function buttonClasses(variant: ButtonVariant, extra?: string): string {
  const classes = ["button"];
  if (variant === "secondary") {
    classes.push("button-secondary");
  }
  if (variant === "danger") {
    classes.push("button-danger");
  }
  if (extra) {
    classes.push(extra);
  }
  return classes.join(" ");
}

type ButtonLinkProps = LinkProps & {
  variant?: ButtonVariant;
};

export function ButtonLink({ variant = "primary", className, ...props }: ButtonLinkProps) {
  return <Link className={buttonClasses(variant, className)} {...props} />;
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
      className={({ isActive }) => buttonClasses(isActive ? activeVariant : inactiveVariant, className)}
      {...props}
    />
  );
}
