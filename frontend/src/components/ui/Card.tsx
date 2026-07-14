import type { HTMLAttributes, ReactNode } from "react";

export type CardDensity = "default" | "compact" | "comfortable";

export type CardProps = HTMLAttributes<HTMLElement> & {
  as?: "div" | "section" | "article";
  density?: CardDensity;
  children: ReactNode;
};

function densityClass(density: CardDensity): string | undefined {
  if (density === "compact") {
    return "ui-card-compact";
  }
  if (density === "comfortable") {
    return "ui-card-comfortable";
  }
  return undefined;
}

export function Card({ as: Tag = "section", density = "default", className, children, ...props }: CardProps) {
  const classes = ["ui-card", "card", densityClass(density), className].filter(Boolean).join(" ");

  return (
    <Tag className={classes} {...props}>
      {children}
    </Tag>
  );
}
