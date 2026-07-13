export type ButtonVariant = "primary" | "roulette" | "secondary" | "ghost" | "danger";

export type ButtonSize = "sm" | "md" | "lg";

type ButtonClassOptions = {
  loading?: boolean;
};

export function buttonClasses(
  variant: ButtonVariant = "primary",
  size: ButtonSize = "md",
  extra?: string,
  options?: ButtonClassOptions,
): string {
  const classes = ["button"];

  if (variant === "secondary") {
    classes.push("button-secondary");
  } else if (variant === "danger") {
    classes.push("button-danger");
  } else if (variant === "roulette") {
    classes.push("button-roulette");
  } else if (variant === "ghost") {
    classes.push("button-ghost");
  }

  if (size === "sm") {
    classes.push("button-sm");
  } else if (size === "lg") {
    classes.push("button-lg");
  }

  if (options?.loading) {
    classes.push("button-loading");
  }

  if (extra) {
    classes.push(extra);
  }

  return classes.join(" ");
}
